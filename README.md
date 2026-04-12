

<h1 align="center">eSim Automated Tool Manager</h1>

<p align="center">
  <strong>A cross-platform CLI tool that automates installation, configuration, updates, and dependency management for the eSim EDA environment.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-brightgreen" alt="Platform"/>
  <img src="https://img.shields.io/badge/dependencies-zero-success" alt="Zero Dependencies"/>
  <img src="https://img.shields.io/badge/tests-25%20passed-brightgreen?logo=pytest" alt="Tests"/>
</p>

<p align="center">
  <em>Submission for eSim Summer Fellowship 2026 – Screening Task 5 (Tool Manager)</em>
</p>

---

## Table of Contents

- [Highlights](#highlights)
- [Requirements Covered](#requirements-covered)
- [Architecture](#architecture)
- [Module Breakdown](#module-breakdown)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Dry-Run vs Execute Mode](#dry-run-vs-execute-mode)
- [Platform Support](#platform-support)
- [Configuration & Logs](#configuration--logs)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Design Choices](#design-choices)
- [Future Scope](#future-scope)

---

## Highlights

- **Zero external dependencies** — runs on Python's standard library alone
- **True cross-platform** — native integration with `apt` (Linux), `brew` (macOS), `choco`/`winget` (Windows)
- **Safe by default** — dry-run mode shows install commands without executing; `--execute` flag for live installs with user confirmation
- **Registry-driven** — add new tools by editing a JSON file, zero code changes
- **13-command interactive CLI** — install, update, configure, verify, log, and report
- **Dual logging** — human-readable `.log` + structured `operations.json`
- **25 unit tests** — all modules tested with pytest

---

## Requirements Covered

The task requires meeting **any 2** of 6 requirements. This submission covers **all 6**:

| # | Requirement | Module | What It Does |
|:-:|---|---|---|
| 1 | **Tool Installation** | `tool_installer.py` | Installs tools via OS-native package managers with dry-run/execute modes, dependency pre-checks, and post-install verification |
| 2 | **Update & Upgrade** | `update_manager.py` | Detects installed versions via `--version` parsing, compares against registry + apt/brew, provides `upgrade <tool\|all>` |
| 3 | **Configuration** | `config_manager.py` | Auto-detects paths, persists config in JSON, manages env vars across `~/.bashrc`, `~/.zshrc`, and `setx` |
| 4 | **Dependency Checker** | `dependency_checker.py` | Scans all deps via `dpkg`/`brew list`/`where`, reports missing with platform-specific install hints |
| 5 | **User Interface** | `tool_manager.py` | 13-command interactive CLI with banners, menus, version display in verify, log viewer, and report export |
| 6 | **Cross-platform** | All modules | Linux (apt) · macOS (Homebrew) · Windows (choco/winget/silent installers) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User (CLI)                           │
│                                                             │
│   python tool_manager.py              (dry-run mode)        │
│   python tool_manager.py --execute    (live installs)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    tool_manager.py                           │
│              Orchestrator & Command Router                   │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │   install    │ │   upgrade   │ │   configure <tool>   │  │
│  │ check-deps   │ │ check-upd.  │ │   show-config        │  │
│  │ list-*       │ │ upgrade all │ │   system-info        │  │
│  │ verify       │ │             │ │   view-logs          │  │
│  └──────┬──────┘ └──────┬──────┘ └──────────┬───────────┘  │
│         │               │                    │              │
├─────────▼───────────────▼────────────────────▼──────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ tool_        │  │ update_      │  │ config_          │  │
│  │ installer.py │  │ manager.py   │  │ manager.py       │  │
│  │              │  │              │  │                  │  │
│  │ • dry-run /  │  │ • version    │  │ • auto-config    │  │
│  │   execute    │  │   parsing    │  │ • env vars       │  │
│  │ • verify     │  │ • apt/brew   │  │ • path mgmt     │  │
│  │ • confirm    │  │   checking   │  │ • preferences    │  │
│  │              │  │ • upgrade    │  │ • JSON persist   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ dependency_      │  │ system_utils.py                │  │
│  │ checker.py       │  │                                │  │
│  │                  │  │ • OS detection (Linux/Win/Mac) │  │
│  │ • dpkg / brew /  │  │ • which / where abstraction   │  │
│  │   where scanning │  │ • disk, network, arch info    │  │
│  │ • missing report │  │ • package manager detection   │  │
│  │ • install hints  │  │                                │  │
│  └──────────────────┘  └────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    logger.py                          │  │
│  │  • text log: tool_manager.log                        │  │
│  │  • JSON log: operations.json                         │  │
│  │  • summaries, report export, log clearing            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   tools_registry.json                       │
│  6 tools × 3 platforms • versions • deps • install cmds    │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Breakdown

| Module | Role | Key Methods |
|---|---|---|
| `tool_manager.py` | CLI orchestrator, command routing, `--execute` flag handling | `run()`, `install_tool()`, `upgrade_tool()` |
| `tool_installer.py` | Executes or dry-runs installs, verifies post-install, skips already-installed tools | `install_tool()`, `verify_installation()` |
| `update_manager.py` | Parses versions via regex, checks `apt-cache`/`brew outdated`, compares tuples | `check_all_updates()`, `upgrade_tool()` |
| `config_manager.py` | Persists tool paths/versions in JSON, writes env vars to shell configs | `configure_tool()`, `apply_environment_variables()` |
| `dependency_checker.py` | Scans deps via `dpkg`/`brew list`/`where`, reports missing with install hints | `check_all_dependencies()`, `get_missing_dependencies()` |
| `system_utils.py` | Abstracts OS commands, detects package manager, disk/network checks | `get_system_info()`, `get_package_manager()` |
| `logger.py` | Dual text+JSON logging, summaries, report export | `log_action()`, `export_log_report()` |
| `tools_registry.json` | Declarative tool definitions — 6 tools, 3 platforms each | N/A (data file) |

---

## Quick Start

### Prerequisites

- **Python 3.8+** (no external packages required for core functionality)
- Linux (Ubuntu/Debian), macOS, or Windows 10+

### Install & Run

```bash
git clone https://github.com/<your-username>/esim-tool-manager.git
cd esim-tool-manager

# Run interactive CLI (safe dry-run mode)
python tool_manager.py

# Run non-interactive demo
python demo.py

# Run tests
pip install pytest
python -m pytest tests/ -v
```

No `pip install` needed for the core application.

---

## Usage Guide

### Interactive CLI

```
 1. check-dependencies    Scan system for all required packages
 2. install <tool>        Install a specific tool
 3. list-installed        Show tools currently on this system
 4. list-available        Show all tools in the registry with install status
 5. check-updates         Compare installed vs latest versions
 6. upgrade <tool|all>    Upgrade one tool or everything
 7. configure <tool>      Auto-detect paths & set env vars
 8. show-config           Display persisted configuration
 9. verify                Verify which registry tools are installed (with versions)
10. view-logs             Show recent operation log entries
11. export-report         Generate a full text report file
12. system-info           Display OS, arch, Python, disk, network, package manager
13. help                  Show the command menu
 0. exit                  Exit
```

### Example Session

```
$ python tool_manager.py --execute

╔═══════════════════════════════════════════════════╗
║       eSim Automated Tool Manager  v2.0          ║
╚═══════════════════════════════════════════════════╝
  Platform       : Linux 5.15.0 (x86_64)
  Python         : 3.11.5
  Package Manager: apt-get
  Install Mode   : EXECUTE
  Config         : /home/user/.esim

  > check-dependencies

  Checking eSim core tools...
    ✓ python3: Python 3.11.5
    ✗ ngspice: not installed

    Total Checked : 7
    ✓ Available   : 5
    ✗ Missing     : 2

    Install hint:
      sudo apt-get install -y ngspice kicad

  > install ngspice

  ✓ Dependencies satisfied

  Tool    : Ngspice
  Package : ngspice
  Command : sudo apt-get install -y ngspice

  Proceed with installing ngspice? [y/N]: y

  Executing installation...
  ✓ ngspice installed and verified
  ✓ ngspice installed and configured

  > verify

  ✓ ngspice: installed (v42)
  ✗ kicad: not found
  ✓ python3: installed (v3.11.5)
  ✓ git: installed (v2.43.0)
  ✓ gcc: installed (v13.3.0)
  ✓ make: installed (v4.3)

  Total: 5/6 installed
```

---

## Dry-Run vs Execute Mode

| | Dry-Run (default) | Execute (`--execute`) |
|---|---|---|
| **Command** | `python tool_manager.py` | `python tool_manager.py --execute` |
| **Install behavior** | Shows the install command but does NOT run it | Asks for confirmation, then runs the command |
| **Upgrade behavior** | Shows what would be upgraded | Actually runs the upgrade |
| **Safety** | Safe to explore — nothing is modified | Requires sudo/admin for system packages |
| **Use case** | Reviewing what needs to be installed | Actually setting up the environment |

This design ensures nobody accidentally runs `sudo apt-get install` just by exploring the tool. The `--execute` flag is an explicit opt-in.

---

## Platform Support

| Feature | Linux (Ubuntu/Debian) | macOS | Windows |
|---|---|---|---|
| **Tool detection** | `which` | `which` | `where` |
| **Package check** | `dpkg -l` | `brew list` | PATH lookup |
| **Version query** | `apt-cache policy` | `brew outdated --json` | Registry versions |
| **Install** | `apt-get install` | `brew install` | Silent `.exe` installers |
| **Upgrade** | `apt-get --only-upgrade` | `brew upgrade` | Re-run installer |
| **Env vars** | `~/.bashrc` append | `~/.zshrc` append | `setx` (user-level) |
| **Config dir** | `~/.esim/` | `~/Library/Application Support/eSim/` | `%APPDATA%\eSim\` |
| **PM detection** | apt-get, dnf, yum, pacman | brew | choco, winget |

All 6 tools in the registry (Ngspice, KiCad, Python3, Git, GCC, Make) have install commands for all three platforms.

---

## Configuration & Logs

### File Locations

| File | Linux | macOS | Windows |
|---|---|---|---|
| Config | `~/.esim/esim_config.json` | `~/Library/Application Support/eSim/esim_config.json` | `%APPDATA%\eSim\esim_config.json` |
| Text log | `~/.esim/logs/tool_manager.log` | `~/Library/Application Support/eSim/logs/tool_manager.log` | `%APPDATA%\eSim\logs\tool_manager.log` |
| JSON log | `~/.esim/logs/operations.json` | `~/Library/Application Support/eSim/logs/operations.json` | `%APPDATA%\eSim\logs\operations.json` |
| Env file | `~/.esim/env.sh` | `~/Library/Application Support/eSim/env.sh` | Set via `setx` |

### Config File Structure

```json
{
  "version": "1.0",
  "tools": {
    "python3": {
      "name": "Python 3",
      "install_path": "/usr/bin/python3",
      "version": "3.11.5",
      "configured": true
    }
  },
  "environment_variables": {
    "NGSPICE_HOME": "/usr/local/ngspice"
  },
  "user_preferences": {
    "auto_update_check": true,
    "log_level": "INFO"
  }
}
```

---

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

### 25 Tests Across 7 Modules

| Module | Tests | What's Tested |
|---|:-:|---|
| `logger.py` | 6 | File creation, JSON structure, summaries, history limits, export, clearing |
| `system_utils.py` | 6 | OS detection, display name, system info keys, Python existence, command execution, PM detection |
| `dependency_checker.py` | 2 | Report structure, missing dependency detection |
| `update_manager.py` | 4 | Version parsing, comparison logic, update check structure, bulk check count |
| `config_manager.py` | 3 | Save/load cycle, tool configuration, config reset |
| `tool_installer.py` | 4 | Dry-run default, execute mode flag, verify existing tool, already-satisfied skip |

All tests use `pytest` fixtures with `tmp_path` for filesystem isolation and `unittest.mock.patch` to prevent side effects.

---

## Project Structure

```
esim-tool-manager/
├── tool_manager.py            Main CLI (orchestrator, --execute flag)
├── tool_installer.py          Install engine (dry-run / execute modes)
├── update_manager.py          Version checking & upgrades
├── config_manager.py          Configuration & environment management
├── dependency_checker.py      Dependency scanning & validation
├── system_utils.py            Cross-platform OS abstraction
├── logger.py                  Dual text + JSON logging
├── tools_registry.json        Tool definitions (6 tools × 3 platforms)
├── demo.py                    Non-interactive demo (8 demonstrations)
├── requirements.txt           Python dependencies (zero for core)
├── .gitignore
├── README.md                  This file
├── DESIGN_DOCUMENT.md         Detailed architecture document
└── tests/
    ├── __init__.py
    └── test_tool_manager.py   25 unit tests
```

---

## Design Choices

1. **Zero dependencies** — Pure standard library. No `pip install`, no virtualenv, no breakage. Deployable on any machine with Python 3.8+.

2. **Safe-by-default (dry-run)** — The tool never runs install commands unless explicitly launched with `--execute`. In execute mode, it asks for confirmation before each install. This prevents accidental system modifications.

3. **Registry-driven** — `tools_registry.json` is the single source of truth. Adding a new tool (e.g. `verilator`) means adding one JSON block with per-OS commands. No Python changes needed.

4. **Package manager delegation** — Instead of reimplementing package management, the tool delegates to `apt`, `brew`, and `choco`. This ensures proper dependency resolution, security patches, and system integration.

5. **Platform abstraction** — `system_utils.py` handles all OS branching so other modules stay platform-agnostic. Every module that touches the OS uses `platform.system()` to select the right strategy.

6. **Dual logging** — Text logs for humans, JSON logs for scripts. Every action is logged, making the system auditable and debuggable.

7. **Modular architecture** — Each task requirement maps to a dedicated module. Modules communicate via the shared `Logger`. Any module can be replaced or extended independently.

---

## Future Scope

- **GUI frontend** — PyQt5/Tkinter wrapping the existing modules
- **Rollback** — Snapshot versions before upgrade, one-command revert
- **Remote registry** — Fetch `tools_registry.json` from a central URL
- **Plugin system** — Drop-in tool definitions via `plugins/` directory
- **CI/CD** — GitHub Actions matrix testing on Linux, macOS, and Windows
- **Brewfile / packages.config** — Batch installs from manifest files

---


