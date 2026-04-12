"""
Tool Installer Module
Downloads and installs external tools via OS-native package managers.
Supports Linux (apt), Windows (silent installers), and macOS (Homebrew).

Two modes:
  dry_run=True  (default) — prints install plan without executing
  dry_run=False           — actually runs the install command
"""

import subprocess
import platform
from pathlib import Path
from typing import Dict, Tuple


OS_KEY_MAP = {"Linux": "linux", "Windows": "windows", "Darwin": "darwin"}


class ToolInstaller:
    """Handles tool installation operations"""

    def __init__(self, logger, dry_run: bool = True):
        self.logger = logger
        self.os_type = platform.system()
        self.dry_run = dry_run

    def install_tool(self, tool_name: str, tool_info: Dict, os_type: str) -> bool:
        os_key = OS_KEY_MAP.get(os_type, os_type.lower())
        os_config = tool_info.get(os_key, {})

        if not os_config:
            print(f"  Error: No install config for {os_type}")
            self.logger.log_action(f"INSTALL_{tool_name}", "FAILED", f"No config for {os_type}")
            return False

        installer = os_config.get("installer", "unknown")
        install_cmd = os_config.get("install_cmd", "")

        if self.installer_already_satisfied(tool_name):
            print(f"\n  ✓ {tool_name} is already installed")
            self.logger.log_action(f"INSTALL_{tool_name}", "SUCCESS", "Already installed")
            return True

        print(f"\n  Tool    : {tool_info.get('name', tool_name)}")
        print(f"  Package : {installer}")
        print(f"  Command : {install_cmd}")

        if self.dry_run:
            print(f"\n  [DRY RUN] The command above was NOT executed.")
            print(f"  To actually install, run the tool manager with --execute:")
            print(f"    python tool_manager.py --execute")
            print(f"  Or run the command manually:")
            print(f"    {install_cmd}")
            self.logger.log_action(f"INSTALL_{tool_name}", "DRY_RUN", install_cmd)
            return False

        print(f"\n  Executing installation...")
        success, output = self._run_command(install_cmd, timeout=300)

        if success:
            verified = self.verify_installation(tool_name)
            if verified:
                print(f"  ✓ {tool_name} installed and verified")
                self.logger.log_action(f"INSTALL_{tool_name}", "SUCCESS",
                                       f"Installed via {installer}")
                return True
            else:
                print(f"  ⚠ Command succeeded but {tool_name} not found on PATH")
                print(f"  You may need to restart your terminal or add it to PATH")
                self.logger.log_action(f"INSTALL_{tool_name}", "WARNING",
                                       "Installed but not on PATH")
                return True
        else:
            print(f"  ✗ Installation failed")
            if output:
                for line in output.strip().split("\n")[-5:]:
                    print(f"    {line}")
            self.logger.log_action(f"INSTALL_{tool_name}", "FAILED", output[:200])
            return False

    def installer_already_satisfied(self, tool_name: str) -> bool:
        return self.verify_installation(tool_name)

    def verify_installation(self, tool_name: str) -> bool:
        cmd = "where" if self.os_type == "Windows" else "which"
        try:
            return subprocess.run(
                f"{cmd} {tool_name}", shell=True, capture_output=True, text=True
            ).returncode == 0
        except Exception as e:
            self.logger.log_action("VERIFY", "FAILED", str(e))
            return False

    def get_tool_version(self, tool_name: str) -> str:
        for flag in ("--version", "-v", "-version"):
            try:
                r = subprocess.run(f"{tool_name} {flag}", shell=True,
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout.strip().split("\n")[0]
            except Exception:
                continue
        return "unknown"

    def configure_environment(self, tool_name: str, install_path: str) -> bool:
        try:
            if self.os_type in ("Linux", "Darwin"):
                shell_rc = Path.home() / (".zshrc" if self.os_type == "Darwin" else ".bashrc")
                export_line = f"export {tool_name.upper()}_HOME={install_path}"
                if shell_rc.exists():
                    existing = shell_rc.read_text()
                    if export_line not in existing:
                        with open(shell_rc, "a") as f:
                            f.write(f"\n{export_line}\n")
                return True
            elif self.os_type == "Windows":
                return True
            return False
        except Exception as e:
            self.logger.log_action("CONFIG_ENV", "FAILED", str(e))
            return False

    def _run_command(self, cmd: str, timeout: int = 120) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
