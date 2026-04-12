"""
Dependency Checker Module
Checks and validates system dependencies across Linux, Windows, and macOS.
"""

import subprocess
import platform
from typing import Dict, List


class DependencyChecker:
    """Handles dependency checking and validation"""

    def __init__(self, logger):
        self.logger = logger
        self.os_type = platform.system()

    def check_all_dependencies(self, tools_registry: Dict) -> Dict:
        report = {
            "total": 0, "available": 0, "missing": 0, "outdated": 0,
            "missing_list": [], "outdated_list": [], "details": [],
        }

        all_deps = set()
        for tool_info in tools_registry.get("tools", {}).values():
            all_deps.update(tool_info.get("dependencies", []))

        report["total"] = len(all_deps)

        for dep in all_deps:
            if self.check_dependency(dep):
                report["available"] += 1
                report["details"].append({
                    "dependency": dep, "status": "available",
                    "version": self.get_dependency_version(dep),
                })
            else:
                report["missing"] += 1
                report["missing_list"].append(dep)
                report["details"].append({"dependency": dep, "status": "missing"})

        print("\nChecking eSim core tools...")
        for tool in ("ngspice", "kicad-cli", "python3"):
            if self._tool_on_path(tool):
                print(f"  ✓ {tool}: {self._quick_version(tool)}")
            else:
                print(f"  ✗ {tool}: not installed")
                if tool not in report["missing_list"]:
                    report["missing_list"].append(tool)

        self.logger.log_action(
            "DEP_CHECK", "SUCCESS",
            f"Checked {report['total']} deps: {report['available']} ok, {report['missing']} missing",
        )
        return report

    def check_dependency(self, dep_name: str) -> bool:
        try:
            if self.os_type == "Linux":
                r = subprocess.run(f"dpkg -l | grep -q {dep_name}", shell=True,
                                   capture_output=True, text=True)
                if r.returncode == 0:
                    return True
                return self._tool_on_path(dep_name)
            elif self.os_type == "Darwin":
                r = subprocess.run(f"brew list {dep_name}", shell=True,
                                   capture_output=True, text=True)
                if r.returncode == 0:
                    return True
                return self._tool_on_path(dep_name)
            elif self.os_type == "Windows":
                return self._tool_on_path(dep_name)
            return False
        except Exception as e:
            self.logger.log_action("CHECK_DEP", "FAILED", str(e))
            return False

    def _tool_on_path(self, name: str) -> bool:
        cmd = "where" if self.os_type == "Windows" else "which"
        try:
            return subprocess.run(f"{cmd} {name}", shell=True,
                                  capture_output=True, text=True).returncode == 0
        except Exception:
            return False

    def get_dependency_version(self, dep_name: str) -> str:
        try:
            if self.os_type == "Linux":
                r = subprocess.run(f"apt-cache show {dep_name} | grep Version",
                                   shell=True, capture_output=True, text=True)
                if r.returncode == 0:
                    return r.stdout.strip().split(":")[-1].strip()
            elif self.os_type == "Darwin":
                r = subprocess.run(f"brew info {dep_name} | head -1",
                                   shell=True, capture_output=True, text=True)
                if r.returncode == 0:
                    return r.stdout.strip()[:60]
        except Exception:
            pass
        return "unknown"

    def _quick_version(self, tool_name: str) -> str:
        for flag in ("--version", "-version", "-v"):
            try:
                r = subprocess.run(f"{tool_name} {flag}", shell=True,
                                   capture_output=True, text=True, timeout=3)
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout.strip().split("\n")[0][:50]
            except Exception:
                continue
        return "installed"

    def get_missing_dependencies(self, dep_list: List[str]) -> List[str]:
        return [d for d in dep_list if not self.check_dependency(d)]

    def validate_dependency_version(self, dep_name: str, required_version: str) -> bool:
        try:
            return self.get_dependency_version(dep_name) >= required_version
        except Exception:
            return False
