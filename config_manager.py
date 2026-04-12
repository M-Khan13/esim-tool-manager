"""
Configuration Manager Module
Automates tool configuration, path management, and environment variable setup.
Supports Linux, Windows, and macOS (Darwin).
"""

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class ConfigManager:
    """Manages tool configuration, paths, and environment variables"""

    CONFIG_FILENAME = "esim_config.json"

    def __init__(self, logger):
        self.logger = logger
        self.os_type = platform.system()
        self.config_dir = self._resolve_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / self.CONFIG_FILENAME
        self.config = self._load_config()

    def _resolve_config_dir(self) -> Path:
        if self.os_type == "Windows":
            return Path(os.getenv("APPDATA", "")) / "eSim"
        elif self.os_type == "Darwin":
            return Path.home() / "Library" / "Application Support" / "eSim"
        return Path.home() / ".esim"

    def _shell_rc(self) -> Path:
        if self.os_type == "Darwin":
            zshrc = Path.home() / ".zshrc"
            return zshrc if zshrc.exists() else Path.home() / ".bash_profile"
        return Path.home() / ".bashrc"

    def _load_config(self) -> Dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                self.logger.log_action("CONFIG_LOAD", "WARNING", "Corrupt config – reset")
        return self._default_config()

    def _default_config(self) -> Dict:
        return {
            "version": "1.0",
            "tools": {},
            "environment_variables": {},
            "paths": {},
            "user_preferences": {
                "auto_update_check": True,
                "log_level": "INFO",
                "preferred_versions": {},
            },
        }

    def save_config(self) -> bool:
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            self.logger.log_action("CONFIG_SAVE", "SUCCESS", str(self.config_path))
            return True
        except Exception as exc:
            self.logger.log_action("CONFIG_SAVE", "FAILED", str(exc))
            return False

    def configure_tool(self, tool_name: str, tool_info: Dict) -> bool:
        tool_cfg: Dict = {"name": tool_info.get("name", tool_name), "configured": True}

        install_path = self._detect_install_path(tool_name)
        if install_path:
            tool_cfg["install_path"] = install_path

        from update_manager import UpdateManager
        version = UpdateManager(self.logger).get_installed_version(tool_name)
        if version:
            tool_cfg["version"] = version

        self.config.setdefault("tools", {})[tool_name] = tool_cfg
        self.save_config()
        self.logger.log_action(f"CONFIG_{tool_name}", "SUCCESS",
                               f"path={install_path} version={version}")
        return True

    def _detect_install_path(self, tool_name: str) -> Optional[str]:
        cmd = "where" if self.os_type == "Windows" else "which"
        try:
            r = subprocess.run(f"{cmd} {tool_name}", shell=True,
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return r.stdout.strip().splitlines()[0]
        except Exception:
            pass
        return None

    def apply_environment_variables(self, env_vars: Dict[str, str]) -> bool:
        written = 0

        env_file = self.config_dir / "env.sh"
        try:
            lines = [f'export {k}="{os.path.expandvars(v)}"' for k, v in env_vars.items()]
            with open(env_file, "w") as f:
                f.write("# eSim environment variables – source this file\n")
                f.write("\n".join(lines) + "\n")
            written += 1
        except Exception as exc:
            self.logger.log_action("ENV_WRITE", "FAILED", str(exc))

        if self.os_type in ("Linux", "Darwin"):
            written += self._append_to_shell_rc(env_vars)
        elif self.os_type == "Windows":
            written += self._setx_env(env_vars)

        self.config["environment_variables"].update(env_vars)
        self.save_config()
        self.logger.log_action("ENV_APPLY", "SUCCESS" if written else "FAILED",
                               f"Applied {len(env_vars)} variables")
        return written > 0

    def _append_to_shell_rc(self, env_vars: Dict[str, str]) -> int:
        rc = self._shell_rc()
        count = 0
        try:
            existing = rc.read_text() if rc.exists() else ""
            additions = []
            for var, val in env_vars.items():
                marker = f"export {var}="
                if marker not in existing:
                    additions.append(f'export {var}="{os.path.expandvars(val)}"')
                    count += 1
            if additions:
                with open(rc, "a") as f:
                    f.write("\n# eSim Tool Manager\n" + "\n".join(additions) + "\n")
        except Exception as exc:
            self.logger.log_action("SHELL_RC_WRITE", "FAILED", str(exc))
        return count

    def _setx_env(self, env_vars: Dict[str, str]) -> int:
        count = 0
        for var, val in env_vars.items():
            try:
                subprocess.run(f'setx {var} "{val}"', shell=True,
                               capture_output=True, timeout=10)
                count += 1
            except Exception:
                pass
        return count

    def add_to_path(self, directory: str) -> bool:
        current = os.environ.get("PATH", "")
        if directory in current.split(os.pathsep):
            return True

        if self.os_type in ("Linux", "Darwin"):
            rc = self._shell_rc()
            try:
                existing = rc.read_text() if rc.exists() else ""
                line = f'export PATH="$PATH:{directory}"'
                if line not in existing:
                    with open(rc, "a") as f:
                        f.write(f"\n# Added by eSim Tool Manager\n{line}\n")
                self.logger.log_action("PATH_ADD", "SUCCESS", directory)
                return True
            except Exception as exc:
                self.logger.log_action("PATH_ADD", "FAILED", str(exc))
                return False

        elif self.os_type == "Windows":
            try:
                subprocess.run(f'setx PATH "{current};{directory}"', shell=True,
                               capture_output=True, timeout=10)
                self.logger.log_action("PATH_ADD", "SUCCESS", directory)
                return True
            except Exception as exc:
                self.logger.log_action("PATH_ADD", "FAILED", str(exc))
                return False

        return False

    def get_preference(self, key: str, default=None):
        return self.config.get("user_preferences", {}).get(key, default)

    def set_preference(self, key: str, value) -> None:
        self.config.setdefault("user_preferences", {})[key] = value
        self.save_config()

    def display_config(self) -> None:
        print(f"\n  Config file : {self.config_path}")
        print(f"  Config dir  : {self.config_dir}")
        tools = self.config.get("tools", {})
        if tools:
            print("\n  Configured tools:")
            for name, info in tools.items():
                print(f"    {name}: v{info.get('version', '?')} @ {info.get('install_path', '?')}")
        env = self.config.get("environment_variables", {})
        if env:
            print("\n  Environment variables:")
            for var, val in env.items():
                print(f"    {var}={val}")

    def reset_config(self) -> bool:
        self.config = self._default_config()
        return self.save_config()
