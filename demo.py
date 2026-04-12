"""
eSim Tool Manager v2.0 – Demo Script
Demonstrates all modules non-interactively on Linux, Windows, and macOS.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dependency_checker import DependencyChecker
from tool_installer import ToolInstaller
from update_manager import UpdateManager
from config_manager import ConfigManager
from logger import Logger
from system_utils import SystemUtils


def load_registry():
    with open(Path(__file__).parent / "tools_registry.json", "r") as f:
        return json.load(f)


def section(title, n):
    print(f"\n{'=' * 60}\n  DEMO {n}: {title}\n{'=' * 60}\n")


def demo_system_info():
    section("System Information", 1)
    su = SystemUtils()
    info = su.get_system_info()
    print(f"  OS              : {info['os']} {info['version']}")
    print(f"  Architecture    : {info['arch']}")
    print(f"  Python          : {info['python_version']}")
    print(f"  Home            : {info['home']}")
    print(f"  Disk Space      : {info['disk_space']}")
    print(f"  Internet        : {'connected' if info['internet'] else 'offline'}")
    print(f"  Package Manager : {info['package_manager']}")
    print("\n  Installed tools:")
    for tool, ver in su.get_installed_tools().items():
        print(f"    ✓ {tool}: {ver}")
    print("\n  ✓ Done")


def demo_dependency_checker():
    section("Dependency Checker", 2)
    dc = DependencyChecker(Logger())
    report = dc.check_all_dependencies(load_registry())
    print(f"\n  Total   : {report['total']}")
    print(f"  Found   : {report['available']}")
    print(f"  Missing : {report['missing']}")
    if report["missing_list"]:
        print("  Missing packages:")
        for p in report["missing_list"][:6]:
            print(f"    ✗ {p}")
    print("\n  ✓ Done")


def demo_tool_registry():
    section("Tool Registry", 3)
    tools = load_registry().get("tools", {})
    print(f"  Tools in registry: {len(tools)}\n")
    for name, info in tools.items():
        versions = ", ".join(info.get("versions", []))
        platforms = []
        if "linux" in info: platforms.append("Linux")
        if "darwin" in info: platforms.append("macOS")
        if "windows" in info: platforms.append("Windows")
        print(f"  • {name} ({versions})  [{', '.join(platforms)}]")
        print(f"    {info.get('description', '')}")
    print("\n  ✓ Done")


def demo_installer_dry_run():
    section("Tool Installer (dry-run)", 4)
    logger = Logger()
    installer = ToolInstaller(logger, dry_run=True)
    registry = load_registry()
    tool_info = registry["tools"]["ngspice"]
    installer.install_tool("ngspice", tool_info, SystemUtils().get_os_type())
    print("\n  ✓ Done (no commands were executed)")


def demo_update_manager():
    section("Update Manager", 5)
    um = UpdateManager(Logger())
    results = um.check_all_updates(load_registry())
    um.display_update_report(results)
    print("\n  Version comparison examples:")
    for a, b in [("40", "41"), ("8.0", "8.0"), ("3.10.2", "3.11.5")]:
        cmp = um.compare_versions(a, b)
        sym = "<" if cmp < 0 else ("=" if cmp == 0 else ">")
        print(f"    {a} {sym} {b}")
    print("\n  ✓ Done")


def demo_config_manager():
    section("Configuration Manager", 6)
    cm = ConfigManager(Logger())
    for name, info in load_registry().get("tools", {}).items():
        cm.configure_tool(name, info)
    cm.display_config()
    env = load_registry().get("environment_variables", {})
    if env:
        print(f"\n  Registry env vars ({len(env)}):")
        for k, v in env.items():
            print(f"    {k}={v}")
    print("\n  ✓ Done")


def demo_logger():
    section("Operation Logging", 7)
    lg = Logger()
    lg.log_action("DEMO_START", "SUCCESS", "Demo started")
    lg.log_action("DEMO_CHECK", "SUCCESS", "Checked deps")
    lg.log_action("DEMO_UPDATE", "SUCCESS", "Checked updates")
    lg.log_action("DEMO_ERROR", "FAILED", "Simulated error")
    s = lg.get_operations_summary()
    print(f"  Total      : {s['total']}")
    print(f"  Successful : {s['successful']}")
    print(f"  Failed     : {s['failed']}")
    print(f"  Warnings   : {s['warnings']}")
    path = lg.export_log_report()
    if path:
        print(f"\n  Report: {path}")
    print("\n  ✓ Done")


def demo_workflow():
    section("End-to-end Workflow", 8)
    lg = Logger()
    steps = [
        ("INIT", "SUCCESS", "Initialised tool manager"),
        ("OS_DETECT", "SUCCESS", "Detected operating system"),
        ("REGISTRY_LOAD", "SUCCESS", "Loaded tool registry (6 tools)"),
        ("DEP_SCAN", "SUCCESS", "Scanned system dependencies"),
        ("UPDATE_CHECK", "SUCCESS", "Checked for tool updates"),
        ("CONFIG_APPLY", "SUCCESS", "Applied tool configurations"),
        ("ENV_VARS", "SUCCESS", "Set environment variables"),
        ("REPORT_GEN", "SUCCESS", "Generated operation report"),
    ]
    for action, status, msg in steps:
        sym = "✓" if status == "SUCCESS" else "⚠" if status == "WARNING" else "✗"
        print(f"  {sym} [{status}] {msg}")
        lg.log_action(action, status, msg)
    print("\n  ✓ Done")


def main():
    print(f"\n{'=' * 60}")
    print("  eSim Automated Tool Manager v2.0 – DEMO")
    print(f"{'=' * 60}")
    print("  Running all demonstrations...\n")

    try:
        demo_system_info()
        demo_dependency_checker()
        demo_tool_registry()
        demo_installer_dry_run()
        demo_update_manager()
        demo_config_manager()
        demo_logger()
        demo_workflow()

        print(f"\n{'=' * 60}")
        print("  ALL DEMOS COMPLETED SUCCESSFULLY")
        print(f"{'=' * 60}")
        print("""
  Capabilities:
    ✓ Automated tool installation (dry-run + execute modes)
    ✓ Update checking and one-command upgrades
    ✓ Automatic configuration and environment setup
    ✓ Comprehensive dependency scanning
    ✓ Cross-platform: Linux · Windows · macOS
    ✓ Package manager integration (apt, brew, choco/winget)
    ✓ Structured logging with JSON + text reports
    ✓ 13-command interactive CLI

  Run interactively:
    python tool_manager.py              (dry-run mode)
    python tool_manager.py --execute    (live installs)

  Config locations:
    Linux  : ~/.esim/
    macOS  : ~/Library/Application Support/eSim/
    Windows: %APPDATA%\\eSim\\
""")
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
