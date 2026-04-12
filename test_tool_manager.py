"""
Unit tests for eSim Tool Manager
Run: python -m pytest tests/ -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logger import Logger
from system_utils import SystemUtils
from dependency_checker import DependencyChecker
from update_manager import UpdateManager
from config_manager import ConfigManager
from tool_installer import ToolInstaller


@pytest.fixture
def logger(tmp_path):
    with patch.object(Logger, "setup_log_directory"):
        lg = Logger.__new__(Logger)
        lg.log_dir = tmp_path
        lg.log_file = tmp_path / "tool_manager.log"
        lg.json_log_file = tmp_path / "operations.json"
        return lg


@pytest.fixture
def sample_registry():
    return {
        "tools": {
            "python3": {
                "name": "Python 3", "description": "Python interpreter",
                "versions": ["3.10", "3.11", "3.12"],
                "linux": {"installer": "python3", "install_cmd": "sudo apt-get install -y python3"},
                "darwin": {"installer": "python@3", "install_cmd": "brew install python@3"},
                "windows": {"installer": "python-3.12.exe", "install_cmd": "python-3.12.exe /quiet"},
                "dependencies": [],
            },
            "ngspice": {
                "name": "Ngspice", "description": "SPICE simulator",
                "versions": ["40", "41"],
                "linux": {"installer": "ngspice", "install_cmd": "sudo apt-get install -y ngspice"},
                "darwin": {"installer": "ngspice", "install_cmd": "brew install ngspice"},
                "dependencies": ["build-essential", "libfftw3-dev"],
            },
        },
        "environment_variables": {"NGSPICE_HOME": "/usr/local/ngspice"},
    }


class TestLogger:
    def test_log_creates_files(self, logger):
        logger.log_action("TEST", "SUCCESS", "hello")
        assert logger.log_file.exists()
        assert logger.json_log_file.exists()

    def test_json_structure(self, logger):
        logger.log_action("A", "SUCCESS", "ok")
        data = json.loads(logger.json_log_file.read_text())
        assert len(data["operations"]) == 1
        assert data["operations"][0]["action"] == "A"

    def test_operations_summary(self, logger):
        logger.log_action("A", "SUCCESS", "ok")
        logger.log_action("B", "FAILED", "bad")
        logger.log_action("C", "WARNING", "warn")
        s = logger.get_operations_summary()
        assert s == {"total": 3, "successful": 1, "failed": 1, "warnings": 1}

    def test_log_history_limit(self, logger):
        for i in range(10):
            logger.log_action(f"S{i}", "SUCCESS", f"step {i}")
        assert len(logger.get_log_history(3)) == 3

    def test_export_report(self, logger):
        logger.log_action("X", "SUCCESS", "x")
        path = logger.export_log_report()
        assert path and Path(path).exists()

    def test_clear_logs(self, logger):
        logger.log_action("X", "SUCCESS", "x")
        assert logger.clear_logs()
        assert not logger.log_file.exists()


class TestSystemUtils:
    def test_os_type(self):
        assert SystemUtils().get_os_type() in ("Linux", "Windows", "Darwin")

    def test_os_display_name(self):
        assert SystemUtils().get_os_display_name() in ("Linux", "Windows", "macOS")

    def test_system_info_keys(self):
        info = SystemUtils().get_system_info()
        for k in ("os", "os_raw", "version", "arch", "home", "disk_space",
                   "internet", "python_version", "package_manager"):
            assert k in info

    def test_python_exists(self):
        su = SystemUtils()
        assert su.check_tool_exists("python3") or su.check_tool_exists("python")

    def test_execute_command(self):
        ok, out = SystemUtils().execute_command("echo hello")
        assert ok and "hello" in out

    def test_package_manager_detected(self):
        pm = SystemUtils().get_package_manager()
        assert isinstance(pm, str) and len(pm) > 0


class TestDependencyChecker:
    def test_report_structure(self, logger, sample_registry):
        report = DependencyChecker(logger).check_all_dependencies(sample_registry)
        for k in ("total", "available", "missing", "missing_list"):
            assert k in report

    def test_missing_detection(self, logger):
        missing = DependencyChecker(logger).get_missing_dependencies(["nonexistent_xyz"])
        assert "nonexistent_xyz" in missing


class TestUpdateManager:
    def test_parse_version(self):
        assert UpdateManager.parse_version("3.11.5") == (3, 11, 5)
        assert UpdateManager.parse_version("41") == (41,)
        assert UpdateManager.parse_version("") == (0,)

    def test_compare(self, logger):
        um = UpdateManager(logger)
        assert um.compare_versions("3.10", "3.11") == -1
        assert um.compare_versions("3.11", "3.11") == 0
        assert um.compare_versions("3.12", "3.11") == 1

    def test_check_tool_update_structure(self, logger, sample_registry):
        r = UpdateManager(logger).check_tool_update("python3", sample_registry["tools"]["python3"])
        for k in ("tool", "installed_version", "latest_available", "update_available"):
            assert k in r

    def test_check_all_updates_count(self, logger, sample_registry):
        assert len(UpdateManager(logger).check_all_updates(sample_registry)) == 2


class TestConfigManager:
    def test_save_load_cycle(self, logger, tmp_path):
        with patch.object(ConfigManager, "_resolve_config_dir", return_value=tmp_path):
            cm = ConfigManager(logger)
            cm.set_preference("log_level", "DEBUG")
            cm.save_config()
            cm2 = ConfigManager(logger)
            assert cm2.get_preference("log_level") == "DEBUG"

    def test_configure_tool(self, logger, tmp_path, sample_registry):
        with patch.object(ConfigManager, "_resolve_config_dir", return_value=tmp_path):
            cm = ConfigManager(logger)
            cm.configure_tool("python3", sample_registry["tools"]["python3"])
            assert "python3" in cm.config["tools"]

    def test_reset_config(self, logger, tmp_path):
        with patch.object(ConfigManager, "_resolve_config_dir", return_value=tmp_path):
            cm = ConfigManager(logger)
            cm.set_preference("foo", "bar")
            cm.reset_config()
            assert cm.get_preference("foo") is None


class TestToolInstaller:
    def test_dry_run_default(self, logger):
        installer = ToolInstaller(logger)
        assert installer.dry_run is True

    def test_execute_mode(self, logger):
        installer = ToolInstaller(logger, dry_run=False)
        assert installer.dry_run is False

    def test_verify_python(self, logger):
        installer = ToolInstaller(logger)
        assert installer.verify_installation("python3") or installer.verify_installation("python")

    def test_already_satisfied_skips(self, logger):
        installer = ToolInstaller(logger)
        assert installer.installer_already_satisfied("python3") or \
               installer.installer_already_satisfied("python")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
