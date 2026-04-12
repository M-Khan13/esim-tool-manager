<p align="center">
  <img src="https://esim.fossee.in/sites/default/esim_logo.png" alt="eSim Logo" width="110"/>
</p>

<h1 align="center">eSim Automated Tool Manager</h1>

<p align="center">
  <strong>A cross-platform, zero-dependency CLI that automates installation, configuration, updates, and dependency management for the eSim EDA environment — with a safe dry-run mode so nothing ever runs without your consent.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-brightgreen" alt="Platform"/>
  <img src="https://img.shields.io/badge/dependencies-zero-success" alt="Zero Dependencies"/>
  <img src="https://img.shields.io/badge/tests-25%20passed-brightgreen?logo=pytest" alt="25 Tests"/>
  <img src="https://img.shields.io/badge/task-Screening%20Task%205-orange" alt="Screening Task 5"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="MIT"/>
</p>

<p align="center">
  <em>Submission for the eSim Summer Fellowship 2026 – Screening Task 5 (Tool Manager) · IIT Bombay / FOSSEE</em>
</p>

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements Coverage](#requirements-coverage)
4. [Architecture](#architecture)
5. [Module Breakdown](#module-breakdown)
6. [File Structure](#file-structure)
7. [Installation](#installation)
8. [Usage Guide](#usage-guide)
9. [CLI Command Reference](#cli-command-reference)
10. [Dry-Run vs Execute Mode](#dry-run-vs-execute-mode)
11. [Platform Support](#platform-support)
12. [Tool Registry](#tool-registry)
13. [Configuration & Logs](#configuration--logs)
14. [Testing](#testing)
15. [Design Choices](#design-choices)
16. [Safety Model](#safety-model)
17. [Known Limitations](#known-limitations)
18. [Future Scope](#future-scope)
19. [Dependencies](#dependencies)

---

## Overview

The eSim Automated Tool Manager is a standalone Python CLI application that handles the complete lifecycle of all external tools required by the eSim EDA environment. Instead of asking users to manually install ngspice, KiCad, GCC, and their dependencies — and figure out the right commands for their OS — this tool does it all through a single, consistent interface.

It is **safe by default**: the first time you run it, it only *shows* you what it would do. No install command is ever executed until you explicitly launch with `--execute` and confirm the action at the prompt. This design makes it suitable for exploration, auditing, and CI environments where you want to verify intent before touching the system.

The tool integrates natively with the OS package manager (`apt` on Ubuntu/Debian, `brew` on macOS, `choco`/`winget` on Windows) rather than reimplementing package management from scratch. All tool definitions live in a declarative JSON registry — adding a new tool requires editing one JSON block and zero Python code.

---

## Features

- **Zero external dependencies** — built entirely on Python's standard library (`os`, `sys`, `json`, `subprocess`, `platform`, `pathlib`, `re`, `shutil`, `socket`, `datetime`). No `pip install` needed to run the core application.
- **True cross-platform** — native integration with `apt-get` (Linux), `brew` (macOS), and `choco`/`winget` / silent `.exe` installers (Windows). Every feature works identically on all three platforms.
- **Safe-by-default dry-run mode** — installs are displayed but never executed unless you pass `--execute`. In execute mode, you still get a per-install confirmation prompt `[y/N]`.
- **Registry-driven** — `tools_registry.json` is the single source of truth. Add a new tool by adding one JSON block. No code changes required.
- **13-command interactive CLI** — a full-screen menu covering install, update, configure, verify, log viewing, and system reporting.
- **Automatic dependency pre-check** — before any install, missing tool dependencies are detected and printed with platform-specific install hints.
- **Version-aware update checking** — parses installed versions via `--version` output (regex-based), compares against `apt-cache policy` / `brew outdated --json`, and reports what needs upgrading.
- **Auto-configuration** — after install, `config_manager` auto-detects the binary path, records the version, and writes the tool's environment variables to `~/.bashrc`, `~/.zshrc`, or Windows `setx` — idempotently.
- **Dual logging** — every operation is written to both a human-readable `.log` file and a structured `operations.json` for scripting and auditing.
- **Exportable report** — `export-report` generates a timestamped full text report of all operations.
- **25 unit tests** — all seven modules tested with `pytest` using `tmp_path` filesystem isolation and `unittest.mock.patch` for subprocess side effects.

---

## Requirements Coverage

The screening task requires meeting **any 2 of 6** requirements. This submission covers **all 6**:

| # | Requirement | Module | Implementation |
|:-:|---|---|---|
| 1 | **Tool Installation** | `tool_installer.py` | Dry-run and execute modes; dependency pre-check; per-install user confirmation; post-install binary verification via `which`/`where`; skip-if-already-installed logic |
| 2 | **Update & Upgrade** | `update_manager.py` | Version parsing via regex → tuple comparison; `apt-cache policy` / `brew outdated --json` integration; `upgrade <tool\|all>` command |
| 3 | **Configuration Management** | `config_manager.py` | Auto-detects install paths; persists config in `esim_config.json`; writes env vars to `~/.bashrc`, `~/.zshrc`, or `setx`; idempotent (never duplicates shell entries) |
| 4 | **Dependency Checker** | `dependency_checker.py` | Scans via `dpkg -l`, `brew list`, or `where`; reports missing packages with platform-specific install hints; integrated as a pre-flight check before every install |
| 5 | **User Interface** | `tool_manager.py` | 13-command interactive CLI with banner, menu, version display, real-time feedback, structured output |
| 6 | **Cross-platform Support** | All modules | Linux (apt) · macOS (Homebrew) · Windows (choco/winget/silent `.exe`); `system_utils.py` abstracts all OS branching |

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
│           Orchestrator · Command Router · Banner             │
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
│  │ • dry-run /  │  │ • --version  │  │ • path detection │  │
│  │   execute    │  │   regex      │  │ • env var write  │  │
│  │ • verify     │  │ • apt-cache  │  │ • JSON persist   │  │
│  │ • skip-exist │  │   brew JSON  │  │ • idempotent     │  │
│  │ • confirm    │  │ • tuple cmp  │  │   shell writes   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ dependency_      │  │ system_utils.py                │  │
│  │ checker.py       │  │                                │  │
│  │                  │  │ • OS detection                 │  │
│  │ • dpkg / brew /  │  │ • which / where abstraction    │  │
│  │   where scanning │  │ • disk, network, arch info     │  │
│  │ • missing report │  │ • package manager detection    │  │
│  │ • install hints  │  │ • installed tool scanning      │  │
│  └──────────────────┘  └────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    logger.py                          │  │
│  │   text log: tool_manager.log  (human readable)       │  │
│  │   JSON log: operations.json   (structured/scriptable)│  │
│  │   summaries · report export · log clearing           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   tools_registry.json                       │
│     6 tools × 3 platforms · versions · deps · env vars     │
└─────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
tool_manager.py
  ├── tool_installer.py     ──▶ logger.py
  ├── update_manager.py     ──▶ logger.py
  ├── config_manager.py     ──▶ logger.py
  ├── dependency_checker.py ──▶ logger.py
  ├── system_utils.py       (no internal dependencies)
  └── logger.py             (no internal dependencies)
```

There are no circular dependencies. All modules depend on `logger.py` for operation recording, and all OS branching is isolated in `system_utils.py`.

---

## Module Breakdown

### `tool_manager.py` — CLI Orchestrator (14.6 KB)

The top-level entry point. Reads `--execute` / `--help` from `sys.argv`, instantiates all modules, displays the banner (OS, Python version, package manager, install mode, config path), and runs the 13-command interactive loop. All commands are dispatched here; business logic lives in the sub-modules.

Key methods: `run()`, `install_tool()`, `upgrade_tool()`, `configure_tool()`, `check_dependencies()`, `verify_installations()`, `show_system_info()`.

### `tool_installer.py` — Installation Engine (5.3 KB)

Handles the full install flow with two modes controlled by the `dry_run` flag (default `True`):

- **Dry-run**: prints the OS-specific install command with a clear "NOT EXECUTING" label, then returns. No subprocess is spawned.
- **Execute**: asks `[y/N]` per tool, runs the install command via `subprocess.run()`, then verifies the binary appears on `PATH` using `which`/`where`. Already-installed tools are detected and skipped automatically.

Post-install, `tool_manager.py` calls `config_manager.configure_tool()` to persist paths and set environment variables.

Key methods: `install_tool()`, `verify_installation()`, `installer_already_satisfied()`.

### `update_manager.py` — Version Checking & Upgrades (7.4 KB)

Parses installed versions from `--version` output using a regex `\d+(\.\d+)+` and converts them to comparable tuples (e.g. `"3.11.5"` → `(3, 11, 5)`). Compares against the latest available version from:

| OS | Source | Fallback |
|---|---|---|
| Linux | `apt-cache policy <pkg>` (Installed vs Candidate) | Registry `versions[-1]` |
| macOS | `brew outdated --json=v2` | Registry `versions[-1]` |
| Windows | — | Registry `versions[-1]` |

Upgrade strategy delegates to the native package manager (`apt-get install --only-upgrade`, `brew upgrade`) with a fallback to re-running the full install command.

Key methods: `check_all_updates()`, `check_tool_update()`, `upgrade_tool()`, `parse_version()`, `compare_versions()`, `display_update_report()`.

### `config_manager.py` — Configuration & Environment (7.7 KB)

Persists tool configuration in `esim_config.json` under the OS-appropriate directory. Auto-detects binary paths using `which`/`where` after install. Writes environment variables to the user's shell profile (`~/.bashrc` on Linux, `~/.zshrc` / `~/.bash_profile` on macOS, `setx` on Windows) — but only after checking that the entry doesn't already exist, making all writes idempotent. Also generates a shell-sourceable `env.sh` file in the config directory.

Key methods: `configure_tool()`, `apply_environment_variables()`, `save_config()`, `display_config()`, `reset_config()`, `set_preference()`, `get_preference()`.

### `dependency_checker.py` — Dependency Scanner (4.5 KB)

Scans each tool's declared `dependencies` list against the system. A dependency is considered satisfied if *either* the package manager check (`dpkg -l | grep <dep>` on Linux, `brew list <dep>` on macOS) or a direct binary check (`which`/`where`) succeeds. Missing packages are reported with ready-to-paste platform-specific install commands.

Key methods: `check_all_dependencies()`, `get_missing_dependencies()`, `is_dependency_available()`.

### `system_utils.py` — Platform Abstraction Layer (4.5 KB)

Centralises all OS-specific branching so every other module stays platform-agnostic. Detects the OS type via `platform.system()`, resolves the appropriate `which` vs `where` command, identifies the active package manager (checking for `apt-get`, `dnf`, `yum`, `pacman` on Linux; `brew` on macOS; `choco` / `winget` on Windows), and exposes disk space, internet connectivity, and Python version.

Key methods: `get_os_type()`, `get_os_display_name()`, `check_tool_exists()`, `get_package_manager()`, `get_system_info()`, `get_installed_tools()`, `execute_command()`.

### `logger.py` — Dual Logging (4.0 KB)

Every operation in the system is recorded in two formats simultaneously:

- **Text log** (`tool_manager.log`): `[2026-04-05 14:30:22] INSTALL_ngspice | SUCCESS | Installed via apt-get`
- **JSON log** (`operations.json`): structured records with `timestamp`, `action`, `status`, and `details` fields — suitable for parsing by scripts or CI systems.

Also provides `get_operations_summary()` (totals by status), `get_log_history(n)` (last n entries), `export_log_report()` (timestamped full report file), and `clear_logs()`.

Key methods: `log_action()`, `get_operations_summary()`, `get_log_history()`, `export_log_report()`, `clear_logs()`.

### `tools_registry.json` — Declarative Tool Registry (5.9 KB)

The single source of truth for all tool definitions. Contains 6 tools (Ngspice, KiCad, Python3, Git, GCC, Make), each with entries for Linux, macOS, and Windows (installer name, install command, download URL), a list of `dependencies`, and supported `versions`. Also contains a global `environment_variables` block applied during configuration, and a `dependencies` section with cross-platform descriptions of each dependency.

To add a new tool, add one JSON block. No Python changes are needed.

### `demo.py` — Non-Interactive Demo (6.4 KB)

Runs all 8 capabilities (system info, dependency check, registry listing, dry-run install, update check, config, logging, and end-to-end workflow) without any user input. Safe to run on any system — no packages are installed. Useful for CI or reviewing the tool's output before interactive use.

---

## File Structure

```
esim-tool-manager/
├── tool_manager.py            Main CLI (orchestrator, --execute flag, banner, command loop)
├── tool_installer.py          Install engine (dry-run / execute, verification, skip logic)
├── update_manager.py          Version checking & upgrades (regex parsing, tuple comparison)
├── config_manager.py          Configuration & environment management (JSON persist, shell writes)
├── dependency_checker.py      Dependency scanning & validation (dpkg, brew, where)
├── system_utils.py            Cross-platform OS abstraction (which, PM detection, disk/net)
├── logger.py                  Dual text + JSON logging (summary, export, clear)
├── tools_registry.json        Tool definitions (6 tools × 3 platforms, env vars, deps)
├── demo.py                    Non-interactive demo (8 demonstrations, no installs)
├── requirements.txt           Core: zero deps · Testing: pytest>=7.0
├── .gitignore
├── README.md                  This file
├── DESIGN_DOCUMENT.md         Detailed architecture document
└── tests/
    ├── __init__.py
    └── test_tool_manager.py   25 unit tests across 6 modules
```

---

## Installation

### Prerequisites

- **Python 3.8 or later** (standard library only — no `pip install` needed for the core application)
- Linux (Ubuntu/Debian recommended), macOS, or Windows 10+
- `pytest >= 7.0` only if you intend to run the unit test suite

### Clone and Run

```bash
git clone https://github.com/<your-username>/esim-tool-manager.git
cd esim-tool-manager

# Launch interactive CLI in safe dry-run mode (no installs executed)
python tool_manager.py

# Launch interactive CLI in execute mode (live installs, requires sudo/admin for system packages)
python tool_manager.py --execute

# Run the non-interactive demo (safe, no installs)
python demo.py

# Show CLI help
python tool_manager.py --help
```

No virtual environment is needed. No `pip install` is needed for the core application.

### Running the Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

All 25 tests should pass on Linux, macOS, and Windows.

---

## Usage Guide

### Step 1: Explore the System (Dry-Run)

Launch without `--execute` to enter safe exploration mode:

```
$ python tool_manager.py

╔═══════════════════════════════════════════════════╗
║       eSim Automated Tool Manager  v2.0          ║
║     Manage your eSim dependencies with ease       ║
╚═══════════════════════════════════════════════════╝
  Platform       : Linux 5.15.0 (x86_64)
  Python         : 3.11.5
  Package Manager: apt-get
  Install Mode   : DRY-RUN
  Config         : /home/user/.esim
──────────────────────────────────────────────────────

┌──────────────────────────────────────────────────┐
│  Commands                                        │
├──────────────────────────────────────────────────┤
│  1. check-dependencies   Check system deps       │
│  2. install <tool>       Install a tool          │
│  3. list-installed       Installed tools         │
│  4. list-available       Available tools         │
│  5. check-updates        Check for updates       │
│  6. upgrade <tool|all>   Upgrade tool(s)         │
│  7. configure <tool>     Configure a tool        │
│  8. show-config          Show configuration      │
│  9. verify               Verify installations    │
│ 10. view-logs            View operation logs     │
│ 11. export-report        Export log report       │
│ 12. system-info          System information      │
│ 13. help                 Show this menu          │
│  0. exit                 Exit                    │
└──────────────────────────────────────────────────┘
```

### Step 2: Check What's Missing

```
  > check-dependencies

  ============================================================
    Checking System Dependencies
  ============================================================

    Total Checked : 7
    ✓ Available   : 5
    ✗ Missing     : 2

    Missing:
      ✗ ngspice
      ✗ kicad

    Install hint:
      sudo apt-get install -y ngspice kicad
```

### Step 3: See Available Tools

```
  > list-available

  ✗ ngspice (40, 41, 42)
    Open-source SPICE simulator for circuit simulation
    Deps: build-essential, libgomp1, libfftw3-dev

  ✓ python3 (3.9, 3.10, 3.11, 3.12)
    Python programming language and runtime

  ✓ git (2.42, 2.43, 2.44)
    Distributed version control system
  ...
  Total: 6 tools
```

### Step 4: Install a Tool (Dry-Run First)

```
  > install ngspice

  ============================================================
    Installing ngspice
  ============================================================
  ✓ Dependencies satisfied

  Tool    : Ngspice
  Package : ngspice
  Command : sudo apt-get install -y ngspice

  [DRY-RUN] Command shown above — use --execute to run it
```

### Step 5: Actually Install (Execute Mode)

```
$ python tool_manager.py --execute

  > install ngspice

  ✓ Dependencies satisfied

  Tool    : Ngspice
  Package : ngspice
  Command : sudo apt-get install -y ngspice

  Proceed with installing ngspice? [y/N]: y

  Executing installation...
  ✓ ngspice installed and verified
  ✓ ngspice installed and configured
```

### Step 6: Verify All Installations

```
  > verify

  ✓ ngspice: installed (v42)
  ✗ kicad: not found
  ✓ python3: installed (v3.11.5)
  ✓ git: installed (v2.43.0)
  ✓ gcc: installed (v13.3.0)
  ✓ make: installed (v4.3)

  Total: 5/6 installed
```

### Step 7: Check for Updates

```
  > check-updates

  ✓ python3: up to date (v3.11.5)
  ↑ ngspice: v40 → v42 available
  ✓ git: up to date (v2.43.0)

  1 tool(s) can be upgraded. Run: upgrade ngspice
```

### Step 8: Upgrade

```
  > upgrade all

  Upgrading ngspice (v40 → v42)...
  ✓ ngspice upgraded

  ✓ Everything else is up to date
```

---

## CLI Command Reference

Commands can be entered by name or number:

| # | Command | Argument | Description |
|:-:|---|---|---|
| 1 | `check-dependencies` | — | Scans system for all required packages; reports missing with install hints |
| 2 | `install` | `<tool>` | Installs the named tool; checks dependencies first; dry-run or execute based on launch flag |
| 3 | `list-installed` | — | Shows all tools currently detected on the system with their versions |
| 4 | `list-available` | — | Lists all tools in the registry with install status, versions, and deps |
| 5 | `check-updates` | — | Compares installed vs latest versions; shows what can be upgraded |
| 6 | `upgrade` | `<tool\|all>` | Upgrades a single tool or everything that has an update available |
| 7 | `configure` | `<tool>` | Auto-detects install path, records version, writes env vars to shell profile |
| 8 | `show-config` | — | Displays the current persisted configuration (paths, versions, preferences) |
| 9 | `verify` | — | Checks whether each registry tool is installed; shows version if found |
| 10 | `view-logs` | — | Shows the last 20 operation log entries from the text log |
| 11 | `export-report` | — | Generates a timestamped full operation report file and prints its path |
| 12 | `system-info` | — | Displays OS, architecture, Python version, disk space, internet status, package manager |
| 13 | `help` | — | Prints the command menu |
| 0 | `exit` | — | Exits the CLI and logs the session end |

Tool names for `install`, `upgrade`, and `configure` must match a key in `tools_registry.json` (e.g. `ngspice`, `kicad`, `python3`, `git`, `gcc`, `make`).

---

## Dry-Run vs Execute Mode

| | Dry-Run (default) | Execute (`--execute`) |
|---|---|---|
| **Launch command** | `python tool_manager.py` | `python tool_manager.py --execute` |
| **Install behavior** | Prints the install command; does **not** run it | Asks `[y/N]` confirmation, then runs the command |
| **Upgrade behavior** | Shows what would be upgraded | Runs the upgrade command |
| **Config writes** | Shell profile and JSON updates are applied (read-only config, no package manager calls) | Same, plus actual installs |
| **Safety** | Safe to run anywhere — nothing is modified by the package manager | Requires `sudo` / admin for system packages |
| **Use case** | Auditing what's needed; CI output verification | Actually setting up an environment |

The `--execute` flag is an explicit opt-in. Even in execute mode, every install triggers a `[y/N]` confirmation prompt so there are no accidental bulk installs.

---

## Platform Support

| Feature | Linux (Ubuntu/Debian) | macOS | Windows |
|---|---|---|---|
| **Tool detection** | `which` | `which` | `where` |
| **Package scan** | `dpkg -l \| grep <dep>` | `brew list <dep>` | PATH lookup via `where` |
| **Version check** | `apt-cache policy <pkg>` | `brew outdated --json=v2` | Registry `versions[-1]` |
| **Install** | `sudo apt-get install -y <pkg>` | `brew install <pkg>` | Silent `.exe` with `/S` or `/quiet` |
| **Upgrade** | `apt-get install --only-upgrade -y` | `brew upgrade <pkg>` | Re-run silent installer |
| **Env vars** | Append to `~/.bashrc` | Append to `~/.zshrc` | `setx VAR "value"` |
| **Config dir** | `~/.esim/` | `~/Library/Application Support/eSim/` | `%APPDATA%\eSim\` |
| **PM detection** | apt-get, dnf, yum, pacman | brew | choco, winget |

All six tools in the registry have complete install commands for all three platforms.

---

## Tool Registry

`tools_registry.json` contains every tool definition in a declarative format. The top-level structure:

```json
{
  "tools": { ... },
  "dependencies": { ... },
  "environment_variables": { ... },
  "metadata": { ... }
}
```

### Registered Tools (6)

| Tool | Versions | Description |
|---|---|---|
| `ngspice` | 40, 41, 42 | Open-source SPICE circuit simulator |
| `kicad` | 8.0, 9.0 | Open-source EDA for circuit design and PCB layout |
| `python3` | 3.9, 3.10, 3.11, 3.12 | Python programming language and runtime |
| `git` | 2.42, 2.43, 2.44 | Distributed version control system |
| `gcc` | 12, 13, 14 | GNU Compiler Collection |
| `make` | 4.3, 4.4 | Build automation tool |

### Per-Tool Entry Format

```json
{
  "name": "Ngspice",
  "description": "Open-source SPICE simulator for circuit simulation",
  "versions": ["40", "41", "42"],
  "linux":   { "url": "...", "installer": "ngspice",              "install_cmd": "sudo apt-get install -y ngspice" },
  "darwin":  { "url": "...", "installer": "ngspice",              "install_cmd": "brew install ngspice" },
  "windows": { "url": "...", "installer": "ngspice-42-64bit.exe", "install_cmd": "ngspice-42-64bit.exe /S /D=C:\\Program Files\\ngspice" },
  "dependencies": ["build-essential", "libgomp1", "libfftw3-dev"]
}
```

### Adding a New Tool

Add one JSON block to the `"tools"` object. No Python changes are required. For example, to add `verilator`:

```json
"verilator": {
  "name": "Verilator",
  "description": "Fast open-source Verilog/SystemVerilog simulator",
  "versions": ["5.014", "5.020"],
  "linux":  { "installer": "verilator", "install_cmd": "sudo apt-get install -y verilator" },
  "darwin": { "installer": "verilator", "install_cmd": "brew install verilator" },
  "windows": { "installer": "verilator-windows.exe", "install_cmd": "verilator-windows.exe /S" },
  "dependencies": ["make", "gcc"]
}
```

---

## Configuration & Logs

### File Locations

| File | Linux | macOS | Windows |
|---|---|---|---|
| Config | `~/.esim/esim_config.json` | `~/Library/Application Support/eSim/esim_config.json` | `%APPDATA%\eSim\esim_config.json` |
| Text log | `~/.esim/logs/tool_manager.log` | `~/Library/Application Support/eSim/logs/tool_manager.log` | `%APPDATA%\eSim\logs\tool_manager.log` |
| JSON log | `~/.esim/logs/operations.json` | `~/Library/Application Support/eSim/logs/operations.json` | `%APPDATA%\eSim\logs\operations.json` |
| Env file | `~/.esim/env.sh` | `~/Library/Application Support/eSim/env.sh` | Set via `setx` |

### Config File Structure (`esim_config.json`)

```json
{
  "version": "1.0",
  "tools": {
    "python3": {
      "name": "Python 3",
      "install_path": "/usr/bin/python3",
      "version": "3.11.5",
      "configured": true
    },
    "ngspice": {
      "name": "Ngspice",
      "install_path": "/usr/bin/ngspice",
      "version": "42",
      "configured": true
    }
  },
  "environment_variables": {
    "NGSPICE_HOME": "/usr/local/ngspice",
    "KICAD_HOME": "/usr/share/kicad"
  },
  "user_preferences": {
    "auto_update_check": true,
    "log_level": "INFO"
  }
}
```

### Text Log Format

```
[2026-04-05 14:30:22] INSTALL_ngspice      | SUCCESS    | Installed via apt-get
[2026-04-05 14:30:25] CONFIG_ngspice       | SUCCESS    | Path: /usr/bin/ngspice v42
[2026-04-05 14:31:00] UPDATE_CHECK         | SUCCESS    | 1 update available
```

### JSON Log Format (`operations.json`)

```json
{
  "operations": [
    {
      "timestamp": "2026-04-05T14:30:22",
      "action": "INSTALL_ngspice",
      "status": "SUCCESS",
      "details": "Installed via apt-get"
    }
  ]
}
```

---

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

### 25 Tests Across 6 Modules

| Module | Tests | What's Tested |
|---|:-:|---|
| `logger.py` | 6 | File creation on first log, JSON structure and key presence, operations summary (total/successful/failed/warnings), history limit slicing, report file generation, log clearing |
| `system_utils.py` | 6 | OS type string (Linux/Windows/Darwin), display name (macOS vs Darwin), system info dict key completeness, Python binary detection, `execute_command()` output, package manager string presence |
| `dependency_checker.py` | 2 | Report dict structure (total/available/missing/missing_list), nonexistent package detection |
| `update_manager.py` | 4 | `parse_version()` for multi-part and single-part strings and empty string, `compare_versions()` for less/equal/greater, `check_tool_update()` return dict structure, `check_all_updates()` count matches registry |
| `config_manager.py` | 3 | Save/load round-trip preserves preferences, `configure_tool()` adds tool to config dict, `reset_config()` wipes preferences |
| `tool_installer.py` | 4 | `dry_run=True` default, `dry_run=False` via constructor, Python binary verification, already-installed skip logic |

All tests use `pytest` fixtures with `tmp_path` for filesystem isolation and `unittest.mock.patch` to prevent subprocess side effects. Tests are safe to run on any machine without modifying the system.

---

## Design Choices

**Zero dependencies.** Using only the Python standard library means the tool works on any machine with Python 3.8+ — no internet connection needed to set it up, no virtualenv to manage, no version conflicts. The only optional dependency is `pytest` for the test suite.

**Safe-by-default (dry-run).** The tool never runs install commands unless explicitly launched with `--execute`. In execute mode, it asks for confirmation before each install. This prevents any accidental system modification from simply exploring the tool's menus.

**Registry-driven.** `tools_registry.json` is the single source of truth. All install commands, versions, dependencies, and environment variables are declared there. Any module that needs tool data reads from the registry — there are no hard-coded tool names in the Python code. Adding a new tool is a one-line JSON change.

**Package manager delegation.** Rather than reimplementing download-and-install logic, the tool delegates to `apt`, `brew`, and `choco`. This gives correct dependency resolution, security patches, and system integration for free. Silent `.exe` installers are used for Windows tools not available via a package manager.

**Platform abstraction in one place.** All `if platform == "Linux"` / `elif platform == "Darwin"` branching lives in `system_utils.py`. Every other module calls `system_utils` methods and stays platform-agnostic. This makes it straightforward to extend platform support without touching business logic.

**Idempotent shell config writes.** Before appending a `export VAR=...` line to `~/.bashrc` or `~/.zshrc`, the config manager checks whether the export is already present. This means running `configure ngspice` twice doesn't produce duplicate shell entries.

**Dual logging.** Text logs are for humans reading in a terminal; JSON logs are for scripts, CI pipelines, and automated auditing. Every call to `log_action()` writes both simultaneously. This gives a complete, machine-readable audit trail of every operation without requiring a database.

**Modular architecture.** Each task requirement (install, update, config, deps, UI, cross-platform) maps to a dedicated module. Modules communicate only through `logger.py` and through the registry data passed in by `tool_manager.py`. Any module can be replaced, extended, or tested independently.

---

## Safety Model

| Risk | Mitigation |
|---|---|
| Accidental system modification | Dry-run by default; `--execute` is an explicit opt-in flag |
| Bulk installs without review | Per-install `[y/N]` confirmation even in execute mode |
| Command timeout / hang | All `subprocess.run()` calls have explicit timeout (3–300 s depending on operation) |
| Corrupt config file | Auto-replaced with defaults on `json.JSONDecodeError`; warning logged |
| Missing registry file | Fatal error with clear message and non-zero exit code |
| Duplicate shell config entries | Idempotent writes — checks for existing `export VAR=` before appending |
| Dependency failures mid-install | Dependency pre-check runs before any install command; install is aborted with hints if deps are missing |

---

## Known Limitations

- The tool only manages tools defined in `tools_registry.json`. Tools not in the registry cannot be installed or updated through this CLI.
- On Windows, version detection relies on `--version` output parsing. Tools that don't support `--version` (or use a non-standard format) will show `unknown` as the installed version.
- `apt-cache policy` and `brew outdated` are used for update checking. On systems where these commands are unavailable (e.g. non-Debian Linux distros, or macOS without Homebrew), the tool falls back to the registry's declared latest version, which may not reflect the actual latest release.
- Environment variable writes via `setx` on Windows take effect in new shells only. The current terminal session must be restarted to pick up new variables.
- The tool does not handle rollback. If an upgrade breaks something, the previous version must be reinstalled manually.
- All subprocess calls target the system Python's `subprocess` module. Running inside a virtualenv may affect PATH resolution for tools like `which`.

---

## Future Scope

- **GUI frontend** — PyQt5 or Tkinter wrapping the existing module API, displaying install progress in a real-time log window
- **Rollback support** — snapshot installed version before upgrade, one-command revert to previous state
- **Remote registry** — fetch `tools_registry.json` from a central URL so tool definitions stay up-to-date without pulling the repo
- **Plugin system** — drop-in tool definitions via a `plugins/` directory scanned at startup
- **CI/CD integration** — GitHub Actions matrix testing on Ubuntu, macOS, and Windows with automated badge generation
- **Batch manifests** — install everything in a `Brewfile`, `Chocolatey packages.config`, or custom `esim-manifest.json` with one command
- **Progress bars** — real-time download/install progress for large packages via subprocess stdout streaming

---

## Dependencies

| Component | Version | Purpose |
|---|---|---|
| Python | 3.8+ | Runtime (standard library only for core) |
| pytest | 7.0+ | Unit test runner (optional, test suite only) |

All system-level dependencies (ngspice, KiCad, GCC, etc.) are managed by the tool itself — that is the point of this project.

---

<p align="center">
  Built for the <a href="https://esim.fossee.in/">eSim</a> Summer Fellowship 2026 – Screening Task 5 · <a href="https://fossee.in/">FOSSEE</a>, IIT Bombay
</p>
