# eSim Automated Tool Manager — Design Document

**Version:** 2.0  
**Date:** April 2026  
**Task:** eSim Summer Fellowship 2026 — Screening Task 5 (Tool Manager)  

---

## 1. Overview

The eSim Automated Tool Manager automates the full lifecycle of external tools required by the eSim EDA environment: **installation, configuration, updates, and dependency management**. It supports Linux, Windows, and macOS with zero external Python dependencies, integrates with native package managers, and provides comprehensive logging.

The system uses a **safe-by-default** design: install commands are shown but not executed unless the user explicitly opts in with `--execute`.

---

## 2. Goals & Constraints

### Goals
- Eliminate manual setup steps for eSim's external dependencies
- Provide a single CLI for the entire tool lifecycle (install → configure → update → verify)
- Work identically on Linux, Windows, and macOS
- Never modify the system without explicit user consent
- Log every operation for auditability

### Constraints
- Python 3.8+ standard library only (zero pip dependencies)
- No root/admin required to run the manager itself
- Graceful degradation when tools are missing

---

## 3. Architecture

### 3.1 System Architecture

```
                    ┌──────────────┐
                    │   User CLI   │
                    │  --execute   │
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │    tool_manager.py      │
              │   (Command Router)      │
              └─┬──────┬──────┬──────┬──┘
                │      │      │      │
    ┌───────────▼┐ ┌───▼────┐ ┌▼─────┐ ┌▼──────────────┐
    │ tool_      │ │update_ │ │config│ │ dependency_   │
    │ installer  │ │manager │ │mgr   │ │ checker       │
    │            │ │        │ │      │ │               │
    │ dry-run /  │ │apt/brew│ │JSON  │ │dpkg/brew/     │
    │ execute    │ │compare │ │env   │ │where          │
    └─────┬──────┘ └───┬────┘ └──┬───┘ └──────┬────────┘
          │            │         │             │
    ┌─────▼────────────▼─────────▼─────────────▼────────┐
    │              system_utils.py                       │
    │         (Platform Abstraction Layer)               │
    └───────────────────────┬───────────────────────────┘
                            │
    ┌───────────────────────▼───────────────────────────┐
    │                  logger.py                         │
    │          (Text + JSON Dual Logging)                │
    └───────────────────────┬───────────────────────────┘
                            │
    ┌───────────────────────▼───────────────────────────┐
    │             tools_registry.json                    │
    │    (6 tools × 3 platforms, declarative)            │
    └───────────────────────────────────────────────────┘
```

### 3.2 Module Dependency Graph

```
tool_manager.py
  ├── tool_installer.py    ──▶ logger.py
  ├── update_manager.py    ──▶ logger.py
  ├── config_manager.py    ──▶ logger.py, update_manager.py
  ├── dependency_checker.py──▶ logger.py
  ├── system_utils.py      (no dependencies)
  └── logger.py            (no dependencies)
```

No circular dependencies. All modules depend on `logger.py` for operation recording.

---

## 4. Module Design

### 4.1 tool_installer.py — Installation Engine

**Two modes controlled by `dry_run` flag:**

| Mode | Behavior |
|---|---|
| `dry_run=True` (default) | Prints install command, does NOT execute. Shows manual instructions. |
| `dry_run=False` (`--execute`) | Asks user confirmation → runs command → verifies binary on PATH |

**Install flow:**
```
install_tool(name)
  ├── Check if already installed → skip if yes
  ├── Look up OS-specific config from registry
  ├── Display install plan (tool, package, command)
  ├── If dry_run → print instructions, return
  ├── If execute → ask user confirmation [y/N]
  ├── Run install command via subprocess
  ├── Verify installation (which/where)
  └── Log result
```

**Post-install:** `tool_manager.py` auto-calls `config_manager.configure_tool()` on success.

### 4.2 update_manager.py — Update & Upgrade

**Version parsing:** `"3.11.5"` → regex `\d+(\.\d+)+` → tuple `(3, 11, 5)` for comparison.

**Update sources by platform:**

| OS | Primary | Fallback |
|---|---|---|
| Linux | `apt-cache policy` (Installed vs Candidate) | Registry `versions[-1]` |
| macOS | `brew outdated --json=v2` | Registry `versions[-1]` |
| Windows | — | Registry `versions[-1]` |

**Upgrade strategy:**

| OS | Primary | Fallback |
|---|---|---|
| Linux | `sudo apt-get install --only-upgrade -y <pkg>` | Full `install_cmd` |
| macOS | `brew upgrade <pkg>` | Full `install_cmd` |
| Windows | Full `install_cmd` | — |

### 4.3 config_manager.py — Configuration

**Persisted config (`esim_config.json`):**
```json
{
  "tools": { "<name>": { "install_path": "...", "version": "...", "configured": true } },
  "environment_variables": { "VAR": "value" },
  "user_preferences": { "auto_update_check": true, "log_level": "INFO" }
}
```

**Environment variable persistence:**

| OS | Method | Idempotency |
|---|---|---|
| Linux | Append to `~/.bashrc` | Skips if `export VAR=` already present |
| macOS | Append to `~/.zshrc` (or `~/.bash_profile`) | Skips if already present |
| Windows | `setx VAR "val"` | Overwrites (Windows behavior) |
| All | Writes `~/.esim/env.sh` | Always regenerated |

### 4.4 dependency_checker.py — Dependency Scanner

| OS | Package Check | Binary Check |
|---|---|---|
| Linux | `dpkg -l \| grep <dep>` | `which <dep>` |
| macOS | `brew list <dep>` | `which <dep>` |
| Windows | — | `where <dep>` |

Available if **either** check succeeds. Missing deps generate platform-specific install hints.

### 4.5 system_utils.py — Platform Abstraction

| Method | Linux | macOS | Windows |
|---|---|---|---|
| `check_tool_exists()` | `which` | `which` | `where` |
| `get_package_manager()` | apt-get/dnf/yum/pacman | brew | choco/winget |
| `get_disk_free_space()` | `shutil.disk_usage` | `shutil.disk_usage` | `shutil.disk_usage` |
| `get_os_display_name()` | "Linux" | "macOS" | "Windows" |

### 4.6 logger.py — Dual Logging

- **Text:** `[2026-04-05 14:30:22] INSTALL_ngspice      | SUCCESS    | Installed via brew`
- **JSON:** `{ "timestamp": "...", "action": "...", "status": "...", "details": "..." }`

Log directories follow OS conventions: `~/.esim/logs/` (Linux), `~/Library/Application Support/eSim/logs/` (macOS), `%APPDATA%\eSim\logs\` (Windows).

### 4.7 tools_registry.json — Tool Definitions

Each tool entry:
```json
{
  "name": "...", "description": "...", "versions": ["..."],
  "linux":   { "installer": "...", "install_cmd": "..." },
  "darwin":  { "installer": "...", "install_cmd": "..." },
  "windows": { "installer": "...", "install_cmd": "..." },
  "dependencies": ["..."]
}
```

6 tools registered: Ngspice, KiCad, Python3, Git, GCC, Make. Adding a new tool = one JSON block, zero code changes.

---

## 5. Safety Design

| Risk | Mitigation |
|---|---|
| Accidental system modification | Dry-run by default; `--execute` is explicit opt-in |
| Running wrong install command | User confirmation prompt before each install |
| Corrupt config file | Auto-replaced with defaults; warning logged |
| Missing registry file | Fatal error with clear message |
| Command hangs | All subprocess calls have timeout (3–300s) |
| Duplicate shell config entries | Idempotent writes (checks before appending) |

---

## 6. Testing

25 unit tests across 7 modules:

| Module | Tests | Focus |
|---|:-:|---|
| Logger | 6 | File I/O, JSON structure, summaries, export, clear |
| SystemUtils | 6 | OS detection, display name, info keys, tool checks, PM detection |
| DependencyChecker | 2 | Report structure, missing detection |
| UpdateManager | 4 | Version parsing/comparison, update structure, bulk check |
| ConfigManager | 3 | Save/load, tool config, reset |
| ToolInstaller | 4 | Dry-run flag, execute flag, verify, already-satisfied skip |

Tests use `pytest` with `tmp_path` fixtures and `unittest.mock.patch` for isolation.

---

## 7. Future Enhancements

- GUI frontend (PyQt5/Tkinter)
- Rollback support (snapshot before upgrade)
- Remote registry (fetch from URL)
- Plugin system (drop-in tool definitions)
- CI/CD (GitHub Actions on Linux/macOS/Windows)
- Brewfile / Chocolatey packages.config batch installs

---

## 8. Conclusion

The tool manager provides a complete, safe, modular, and cross-platform solution for managing eSim's external dependencies. The dry-run-by-default approach prevents accidental modifications, the registry-driven design makes it extensible without code changes, and the 25-test suite ensures reliability. All 6 task requirements are fully implemented.
