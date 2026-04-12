"""
System Utilities Module
Cross-platform helpers for OS detection, command execution, and system inspection.
Supports Linux, Windows, and macOS (Darwin).
"""

import os
import shutil
import socket
import subprocess
import platform
from typing import Dict, Tuple


class SystemUtils:
    """System utilities for cross-platform compatibility"""

    SUPPORTED_OS = ("Linux", "Windows", "Darwin")

    def __init__(self):
        self.os_type = platform.system()
        self.os_version = platform.release()

    def get_os_type(self) -> str:
        return self.os_type

    def get_os_version(self) -> str:
        return self.os_version

    def get_os_display_name(self) -> str:
        names = {"Linux": "Linux", "Windows": "Windows", "Darwin": "macOS"}
        return names.get(self.os_type, self.os_type)

    def _which_cmd(self) -> str:
        return "where" if self.os_type == "Windows" else "which"

    def check_tool_exists(self, tool_name: str) -> bool:
        try:
            result = subprocess.run(
                f"{self._which_cmd()} {tool_name}",
                shell=True, capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def get_installed_tools(self) -> Dict[str, str]:
        tools = {
            "python3": "Python",
            "ngspice": "Ngspice",
            "kicad-cli": "KiCad",
            "git": "Git",
            "gcc": "GCC",
            "make": "Make",
        }
        installed = {}
        for cmd, label in tools.items():
            if self.check_tool_exists(cmd):
                installed[label] = self.get_tool_version(cmd)
        return installed

    def get_tool_version(self, tool_name: str) -> str:
        for flag in ("--version", "-version", "-v", "version"):
            try:
                success, output = self.execute_command(f"{tool_name} {flag}", timeout=5)
                if success and output:
                    return output.strip().split("\n")[0][:60]
            except Exception:
                continue
        return "installed"

    def create_directory(self, path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False

    def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception:
            return False

    def get_home_directory(self) -> str:
        return os.path.expanduser("~")

    def get_disk_free_space(self) -> str:
        try:
            usage = shutil.disk_usage(self.get_home_directory())
            free_gb = usage.free / (1024 ** 3)
            return f"{free_gb:.1f} GB available"
        except Exception:
            return "Unknown"

    def check_internet_connection(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception:
            return False

    def get_package_manager(self) -> str:
        if self.os_type == "Linux":
            for pm in ("apt-get", "dnf", "yum", "pacman"):
                if self.check_tool_exists(pm):
                    return pm
            return "unknown"
        elif self.os_type == "Darwin":
            return "brew" if self.check_tool_exists("brew") else "none"
        elif self.os_type == "Windows":
            if self.check_tool_exists("choco"):
                return "choco"
            if self.check_tool_exists("winget"):
                return "winget"
            return "none"
        return "unknown"

    def get_system_info(self) -> Dict:
        return {
            "os": self.get_os_display_name(),
            "os_raw": self.os_type,
            "version": self.os_version,
            "arch": platform.machine(),
            "home": self.get_home_directory(),
            "disk_space": self.get_disk_free_space(),
            "internet": self.check_internet_connection(),
            "python_version": platform.python_version(),
            "package_manager": self.get_package_manager(),
        }
