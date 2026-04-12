"""
Logger Module
Dual text + JSON logging with report export.
Supports Linux, Windows, and macOS.
"""

import json
import os
import platform
from datetime import datetime
from pathlib import Path


class Logger:
    """Handles logging and log management"""

    def __init__(self):
        self.setup_log_directory()
        self.log_file = self.log_dir / "tool_manager.log"
        self.json_log_file = self.log_dir / "operations.json"

    def setup_log_directory(self):
        os_type = platform.system()
        if os_type == "Windows":
            self.log_dir = Path(os.getenv("APPDATA", "")) / "eSim" / "logs"
        elif os_type == "Darwin":
            self.log_dir = Path.home() / "Library" / "Application Support" / "eSim" / "logs"
        else:
            self.log_dir = Path.home() / ".esim" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_action(self, action: str, status: str, details: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action:20} | {status:10} | {details}"
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Warning: Could not write log: {e}")
        self._log_json(action, status, details, timestamp)

    def _log_json(self, action: str, status: str, details: str, timestamp: str) -> None:
        try:
            if self.json_log_file.exists():
                with open(self.json_log_file, "r") as f:
                    logs = json.load(f)
            else:
                logs = {"operations": []}
            logs["operations"].append({
                "timestamp": timestamp, "action": action,
                "status": status, "details": details,
            })
            with open(self.json_log_file, "w") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write JSON log: {e}")

    def get_log_history(self, limit: int = 50) -> list:
        try:
            if not self.log_file.exists():
                return []
            with open(self.log_file, "r") as f:
                return f.readlines()[-limit:]
        except Exception:
            return []

    def get_operations_summary(self) -> dict:
        default = {"total": 0, "successful": 0, "failed": 0, "warnings": 0}
        try:
            if not self.json_log_file.exists():
                return default
            with open(self.json_log_file, "r") as f:
                ops = json.load(f).get("operations", [])
            return {
                "total": len(ops),
                "successful": sum(1 for o in ops if o["status"] == "SUCCESS"),
                "failed": sum(1 for o in ops if o["status"] == "FAILED"),
                "warnings": sum(1 for o in ops if o["status"] == "WARNING"),
            }
        except Exception:
            return default

    def export_log_report(self) -> str:
        try:
            report_file = self.log_dir / "report.txt"
            summary = self.get_operations_summary()
            with open(report_file, "w") as f:
                f.write("=" * 60 + "\n")
                f.write("eSim Tool Manager – Operation Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Total Operations : {summary['total']}\n")
                f.write(f"Successful       : {summary['successful']}\n")
                f.write(f"Failed           : {summary['failed']}\n")
                f.write(f"Warnings         : {summary['warnings']}\n\n")
                f.write("Detailed Log:\n" + "-" * 60 + "\n")
                for entry in self.get_log_history(1000):
                    f.write(entry)
            return str(report_file)
        except Exception:
            return ""

    def clear_logs(self) -> bool:
        try:
            if self.log_file.exists():
                self.log_file.unlink()
            if self.json_log_file.exists():
                self.json_log_file.unlink()
            return True
        except Exception:
            return False
