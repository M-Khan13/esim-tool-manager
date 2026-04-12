"""
Update Manager Module
Checks for updates, compares versions, and upgrades tools.
Supports Linux (apt), Windows, and macOS (Homebrew).
"""

import subprocess
import platform
import re
from typing import Dict, List, Optional, Tuple


class UpdateManager:
    """Handles update checking and upgrading of tools"""

    def __init__(self, logger):
        self.logger = logger
        self.os_type = platform.system()

    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, ...]:
        nums = re.findall(r"\d+", version_str)
        return tuple(int(n) for n in nums) if nums else (0,)

    def compare_versions(self, installed: str, available: str) -> int:
        v_inst = self.parse_version(installed)
        v_avail = self.parse_version(available)
        if v_inst < v_avail:
            return -1
        elif v_inst == v_avail:
            return 0
        return 1

    def get_installed_version(self, tool_name: str) -> Optional[str]:
        for flag in ("--version", "-version", "-v", "version"):
            try:
                r = subprocess.run(
                    f"{tool_name} {flag}", shell=True,
                    capture_output=True, text=True, timeout=5,
                )
                if r.returncode == 0:
                    output = r.stdout.strip() or r.stderr.strip()
                    m = re.search(r"(\d+(?:\.\d+)+)", output)
                    if m:
                        return m.group(1)
            except Exception:
                continue
        return None

    def _apt_check_update(self, package: str) -> Optional[str]:
        try:
            r = subprocess.run(f"apt-cache policy {package}", shell=True,
                               capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                return None
            installed = candidate = None
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("Installed:"):
                    v = line.split(":", 1)[1].strip()
                    if v != "(none)":
                        installed = v
                elif line.startswith("Candidate:"):
                    v = line.split(":", 1)[1].strip()
                    if v != "(none)":
                        candidate = v
            if installed and candidate and installed != candidate:
                return candidate
        except Exception:
            pass
        return None

    def _brew_check_update(self, package: str) -> Optional[str]:
        try:
            r = subprocess.run("brew outdated --json=v2", shell=True,
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                import json
                data = json.loads(r.stdout)
                for formula in data.get("formulae", []):
                    if formula.get("name") == package:
                        versions = formula.get("current_version")
                        if versions:
                            return versions
        except Exception:
            pass
        return None

    def check_tool_update(self, tool_name: str, tool_info: Dict) -> Dict:
        result = {
            "tool": tool_name, "installed_version": None,
            "latest_available": None, "update_available": False, "method": None,
        }

        result["installed_version"] = self.get_installed_version(tool_name)

        versions = tool_info.get("versions", [])
        if versions:
            result["latest_available"] = versions[-1]

        if self.os_type == "Linux":
            pkg = tool_info.get("linux", {}).get("installer", tool_name)
            apt_candidate = self._apt_check_update(pkg)
            if apt_candidate:
                result["latest_available"] = apt_candidate
                result["method"] = "apt"
        elif self.os_type == "Darwin":
            pkg = tool_info.get("darwin", {}).get("installer", tool_name)
            brew_candidate = self._brew_check_update(pkg)
            if brew_candidate:
                result["latest_available"] = brew_candidate
                result["method"] = "brew"

        if result["installed_version"] and result["latest_available"]:
            if self.compare_versions(result["installed_version"], result["latest_available"]) < 0:
                result["update_available"] = True

        return result

    def check_all_updates(self, tools_registry: Dict) -> List[Dict]:
        results = []
        for tool_name, tool_info in tools_registry.get("tools", {}).items():
            info = self.check_tool_update(tool_name, tool_info)
            results.append(info)
            status = "UPDATE_AVAILABLE" if info["update_available"] else "UP_TO_DATE"
            self.logger.log_action(
                f"UPDATE_CHECK_{tool_name}", "SUCCESS",
                f"{status}: installed={info['installed_version']} latest={info['latest_available']}",
            )
        return results

    def upgrade_tool(self, tool_name: str, tool_info: Dict) -> bool:
        os_key = {"Linux": "linux", "Windows": "windows", "Darwin": "darwin"}.get(
            self.os_type, self.os_type.lower()
        )
        os_cfg = tool_info.get(os_key, {})
        install_cmd = os_cfg.get("install_cmd", "")

        if not install_cmd:
            print(f"  No install command for {tool_name} on {self.os_type}")
            return False

        if self.os_type == "Linux":
            pkg = os_cfg.get("installer", tool_name)
            cmd = f"sudo apt-get install --only-upgrade -y {pkg}"
            print(f"  Running: {cmd}")
            return self._run_upgrade(tool_name, cmd, install_cmd)

        elif self.os_type == "Darwin":
            pkg = os_cfg.get("installer", tool_name)
            cmd = f"brew upgrade {pkg}"
            print(f"  Running: {cmd}")
            return self._run_upgrade(tool_name, cmd, install_cmd)

        else:
            print(f"  Running: {install_cmd}")
            return self._exec(tool_name, install_cmd)

    def _run_upgrade(self, tool_name: str, primary: str, fallback: str) -> bool:
        if self._exec(tool_name, primary):
            return True
        print(f"  Fallback: {fallback}")
        return self._exec(tool_name, fallback)

    def _exec(self, tool_name: str, cmd: str) -> bool:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            success = r.returncode == 0
            self.logger.log_action(
                f"UPGRADE_{tool_name}", "SUCCESS" if success else "FAILED",
                r.stderr.strip()[:200] if not success else "Upgraded",
            )
            return success
        except Exception as e:
            self.logger.log_action(f"UPGRADE_{tool_name}", "FAILED", str(e))
            return False

    def display_update_report(self, results: List[Dict]) -> None:
        updates = [r for r in results if r["update_available"]]
        current = [r for r in results if not r["update_available"] and r["installed_version"]]
        missing = [r for r in results if r["installed_version"] is None]

        print(f"\n  Up to date   : {len(current)}")
        print(f"  Updates ready: {len(updates)}")
        print(f"  Not installed: {len(missing)}\n")

        if updates:
            print("  Tools with updates available:")
            for r in updates:
                print(f"    ⬆ {r['tool']}: {r['installed_version']} → {r['latest_available']}")
        if missing:
            print("\n  Not installed:")
            for r in missing:
                print(f"    ✗ {r['tool']}")
