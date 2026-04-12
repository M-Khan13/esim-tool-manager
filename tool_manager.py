"""
eSim Automated Tool Manager v2.0
Main CLI application – orchestrates installation, configuration, updates,
and dependency management for eSim's external tools.
Cross-platform: Linux · Windows · macOS

Usage:
  python tool_manager.py              # interactive mode (dry-run installs)
  python tool_manager.py --execute    # interactive mode (live installs)
  python tool_manager.py --help       # show usage
"""

import os
import sys
import json
import platform
from pathlib import Path

from tool_installer import ToolInstaller
from dependency_checker import DependencyChecker
from update_manager import UpdateManager
from config_manager import ConfigManager
from logger import Logger
from system_utils import SystemUtils


class eSIMToolManager:

    VERSION = "2.0"

    def __init__(self, execute_mode: bool = False):
        self.os_type = platform.system()
        self.execute_mode = execute_mode
        self.logger = Logger()
        self.system_utils = SystemUtils()
        self.installer = ToolInstaller(self.logger, dry_run=not execute_mode)
        self.dep_checker = DependencyChecker(self.logger)
        self.update_mgr = UpdateManager(self.logger)
        self.config_mgr = ConfigManager(self.logger)

        self.setup_directories()
        self.load_tools_registry()

    def setup_directories(self):
        if self.os_type == "Windows":
            self.config_dir = Path(os.getenv("APPDATA", "")) / "eSim"
        elif self.os_type == "Darwin":
            self.config_dir = Path.home() / "Library" / "Application Support" / "eSim"
        else:
            self.config_dir = Path.home() / ".esim"
        self.logs_dir = self.config_dir / "logs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.logger.log_action("INIT", "SUCCESS", f"Directories: {self.config_dir}")

    def load_tools_registry(self):
        registry_path = Path(__file__).parent / "tools_registry.json"
        try:
            with open(registry_path, "r") as f:
                self.tools_registry = json.load(f)
            count = len(self.tools_registry.get("tools", {}))
            self.logger.log_action("REGISTRY_LOAD", "SUCCESS", f"Loaded {count} tools")
        except FileNotFoundError:
            print(f"Error: tools_registry.json not found at {registry_path}")
            self.logger.log_action("REGISTRY_LOAD", "FAILED", "File not found")
            sys.exit(1)

    def display_banner(self):
        os_name = self.system_utils.get_os_display_name()
        pm = self.system_utils.get_package_manager()
        mode = "EXECUTE" if self.execute_mode else "DRY-RUN"
        print(f"""
╔═══════════════════════════════════════════════════╗
║       eSim Automated Tool Manager  v{self.VERSION}          ║
║     Manage your eSim dependencies with ease        ║
╚═══════════════════════════════════════════════════╝
  Platform       : {os_name} {platform.release()} ({platform.machine()})
  Python         : {platform.python_version()}
  Package Manager: {pm}
  Install Mode   : {mode}
  Config         : {self.config_dir}
{'─' * 54}""")

    def display_menu(self):
        print("""
┌──────────────────────────────────────────────────┐
│  Commands                                        │
├──────────────────────────────────────────────────┤
│  1. check-dependencies   Check system deps       │
│  2. install <tool>       Install a tool          │
│  3. list-installed       Installed tools          │
│  4. list-available       Available tools          │
│  5. check-updates        Check for updates        │
│  6. upgrade <tool|all>   Upgrade tool(s)          │
│  7. configure <tool>     Configure a tool         │
│  8. show-config          Show configuration       │
│  9. verify               Verify installations     │
│ 10. view-logs            View operation logs       │
│ 11. export-report        Export log report         │
│ 12. system-info          System information        │
│ 13. help                 Show this menu            │
│  0. exit                 Exit                      │
└──────────────────────────────────────────────────┘""")

    def _install_hint(self, packages):
        if self.os_type == "Linux":
            return f"    sudo apt-get install -y {' '.join(packages)}"
        elif self.os_type == "Darwin":
            return f"    brew install {' '.join(packages)}"
        return f"    Install manually: {', '.join(packages)}"

    def check_dependencies(self):
        print(f"\n{'=' * 54}\n  Checking System Dependencies\n{'=' * 54}")
        report = self.dep_checker.check_all_dependencies(self.tools_registry)
        print(f"\n  Total Checked : {report['total']}")
        print(f"  ✓ Available   : {report['available']}")
        print(f"  ✗ Missing     : {report['missing']}")
        print(f"  ⚠ Outdated    : {report['outdated']}\n")
        if report["missing_list"]:
            print("  Missing:")
            for dep in report["missing_list"]:
                print(f"    ✗ {dep}")
            print(f"\n  Install hint:\n{self._install_hint(report['missing_list'])}")
        elif not report["outdated_list"]:
            print("  ✓ All dependencies satisfied!")

    def install_tool(self, tool_name: str):
        print(f"\n{'=' * 54}\n  Installing {tool_name}\n{'=' * 54}")
        tools = self.tools_registry.get("tools", {})
        if tool_name not in tools:
            print(f"  Error: '{tool_name}' not found in registry")
            return False
        tool_info = tools[tool_name]

        deps = tool_info.get("dependencies", [])
        if deps:
            missing = self.dep_checker.get_missing_dependencies(deps)
            if missing:
                print(f"  Missing dependencies: {', '.join(missing)}")
                print(f"  Install them first:\n{self._install_hint(missing)}")
                self.logger.log_action(f"INSTALL_{tool_name}", "FAILED", f"Missing deps: {missing}")
                return False
        print("  ✓ Dependencies satisfied")

        if self.execute_mode:
            try:
                confirm = input(f"\n  Proceed with installing {tool_name}? [y/N]: ").strip().lower()
                if confirm not in ("y", "yes"):
                    print("  Cancelled.")
                    return False
            except EOFError:
                pass

        success = self.installer.install_tool(tool_name, tool_info, self.os_type)
        if success:
            self.config_mgr.configure_tool(tool_name, tool_info)
            print(f"  ✓ {tool_name} installed and configured")
        return success

    def list_installed_tools(self):
        print(f"\n{'=' * 54}\n  Installed Tools\n{'=' * 54}\n")
        installed = self.system_utils.get_installed_tools()
        if installed:
            for tool, ver in installed.items():
                print(f"  ✓ {tool}: {ver}")
        else:
            print("  No tools detected")

    def list_available_tools(self):
        print(f"\n{'=' * 54}\n  Available Tools\n{'=' * 54}\n")
        tools = self.tools_registry.get("tools", {})
        for name, info in tools.items():
            versions = ", ".join(info.get("versions", ["?"]))
            deps = info.get("dependencies", [])
            installed = self.system_utils.check_tool_exists(name)
            status = "✓" if installed else "✗"
            print(f"  {status} {name} ({versions})")
            print(f"    {info.get('description', '')}")
            if deps:
                print(f"    Deps: {', '.join(deps)}")
            print()
        print(f"  Total: {len(tools)} tools")

    def check_updates(self):
        print(f"\n{'=' * 54}\n  Checking for Updates\n{'=' * 54}")
        results = self.update_mgr.check_all_updates(self.tools_registry)
        self.update_mgr.display_update_report(results)

    def upgrade_tool(self, target: str):
        tools = self.tools_registry.get("tools", {})
        if target == "all":
            results = self.update_mgr.check_all_updates(self.tools_registry)
            upgradable = [r for r in results if r["update_available"]]
            if not upgradable:
                print("\n  ✓ Everything is up to date")
                return
            for r in upgradable:
                print(f"\n  Upgrading {r['tool']} ({r['installed_version']} → {r['latest_available']})...")
                self.update_mgr.upgrade_tool(r["tool"], tools[r["tool"]])
        else:
            if target not in tools:
                print(f"  Error: '{target}' not in registry")
                return
            info = self.update_mgr.check_tool_update(target, tools[target])
            if not info["update_available"]:
                print(f"\n  {target} is up to date ({info['installed_version'] or 'not installed'})")
                return
            print(f"\n  Upgrading {target}...")
            self.update_mgr.upgrade_tool(target, tools[target])

    def configure_tool(self, tool_name: str):
        tools = self.tools_registry.get("tools", {})
        if tool_name not in tools:
            print(f"  Error: '{tool_name}' not in registry")
            return
        print(f"\n  Configuring {tool_name}...")
        self.config_mgr.configure_tool(tool_name, tools[tool_name])
        env_vars = self.tools_registry.get("environment_variables", {})
        if env_vars:
            self.config_mgr.apply_environment_variables(env_vars)
        print(f"  ✓ {tool_name} configured")

    def show_config(self):
        print(f"\n{'=' * 54}\n  Current Configuration\n{'=' * 54}")
        self.config_mgr.display_config()

    def view_logs(self):
        print(f"\n{'=' * 54}\n  Operation Logs (last 20)\n{'=' * 54}\n")
        entries = self.logger.get_log_history(20)
        for e in entries:
            print(f"  {e.strip()}")
        if not entries:
            print("  No logs yet")

    def export_report(self):
        path = self.logger.export_log_report()
        print(f"\n  ✓ Report exported to {path}" if path else "  ✗ Failed to export")

    def verify_installations(self):
        print(f"\n{'=' * 54}\n  Verifying Installations\n{'=' * 54}\n")
        tools = self.tools_registry.get("tools", {})
        count = 0
        for name, info in tools.items():
            exists = self.system_utils.check_tool_exists(name)
            ver = ""
            if exists:
                detected = self.update_mgr.get_installed_version(name)
                ver = f" (v{detected})" if detected else ""
            print(f"  {'✓' if exists else '✗'} {name}: {'installed' + ver if exists else 'not found'}")
            count += exists
        print(f"\n  Total: {count}/{len(tools)} installed")

    def show_system_info(self):
        print(f"\n{'=' * 54}\n  System Information\n{'=' * 54}\n")
        info = self.system_utils.get_system_info()
        print(f"  OS              : {info['os']} {info['version']}")
        print(f"  Architecture    : {info['arch']}")
        print(f"  Python          : {info['python_version']}")
        print(f"  Home            : {info['home']}")
        print(f"  Disk Space      : {info['disk_space']}")
        print(f"  Internet        : {'connected' if info['internet'] else 'offline'}")
        print(f"  Package Manager : {info['package_manager']}")

    def run(self):
        self.display_banner()
        while True:
            try:
                self.display_menu()
                raw = input("\n  > ").strip()
                if not raw:
                    continue
                parts = raw.split()
                cmd = parts[0].lower()
                arg = parts[1].lower() if len(parts) > 1 else None

                cmds = {
                    "check-dependencies": self.check_dependencies, "1": self.check_dependencies,
                    "list-installed": self.list_installed_tools, "3": self.list_installed_tools,
                    "list-available": self.list_available_tools, "4": self.list_available_tools,
                    "check-updates": self.check_updates, "5": self.check_updates,
                    "show-config": self.show_config, "8": self.show_config,
                    "verify": self.verify_installations, "9": self.verify_installations,
                    "view-logs": self.view_logs, "10": self.view_logs,
                    "export-report": self.export_report, "11": self.export_report,
                    "system-info": self.show_system_info, "12": self.show_system_info,
                    "help": self.display_menu, "13": self.display_menu,
                }

                if cmd in cmds:
                    cmds[cmd]()
                elif cmd in ("install", "2"):
                    if not arg: print("  Usage: install <tool>"); continue
                    self.install_tool(arg)
                elif cmd in ("upgrade", "6"):
                    if not arg: print("  Usage: upgrade <tool|all>"); continue
                    self.upgrade_tool(arg)
                elif cmd in ("configure", "7"):
                    if not arg: print("  Usage: configure <tool>"); continue
                    self.configure_tool(arg)
                elif cmd in ("exit", "quit", "0"):
                    print("\n  Goodbye!")
                    self.logger.log_action("EXIT", "SUCCESS", "User exited")
                    break
                else:
                    print("  Unknown command. Type 'help'.")
            except KeyboardInterrupt:
                print("\n\n  Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"  Error: {e}")
                self.logger.log_action("ERROR", "FAILED", str(e))


def main():
    execute = "--execute" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
eSim Automated Tool Manager v2.0

Usage:
  python tool_manager.py              Interactive mode (dry-run installs)
  python tool_manager.py --execute    Interactive mode (live installs)
  python tool_manager.py --help       Show this help

In dry-run mode (default), install commands are displayed but not executed.
Use --execute to actually run install commands (may require sudo/admin).
""")
        return

    try:
        eSIMToolManager(execute_mode=execute).run()
    except Exception as e:
        print(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
