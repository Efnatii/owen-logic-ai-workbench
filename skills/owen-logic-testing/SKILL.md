---
name: owen-logic-testing
description: Test and inspect OWEN Logic projects and the local OWEN Logic Windows application from Codex. Use when the user asks to check, launch, smoke-test, screenshot, diagnose, or automate OWEN Logic / ProgramRelayFBD projects, especially PR100/PR200 Structured Text or FBD work intended to be opened in OWEN Logic.
---

# Owen Logic Testing

## Overview

Use the local OWEN Logic MCP tools to perform non-destructive OWEN Logic checks: find the installation, launch the GUI, list windows/processes, capture screenshots, and run a smoke test. In Codex Desktop these tools may be exposed through `mcp__artifact_tools__` as `owen_logic_*` because the desktop session has a practical MCP-server startup limit; the standalone workspace server is available at `07_TOOLS\ai_capabilities\repositories\owen_logic_ai_workbench\mcp\owen_logic_server.py`.

## Workflow

1. Inspect the project folder first. Look for `.st`, `.json`, exported OWEN Logic files, screenshots, Python simulations, and existing test reports.
2. If local simulation tests exist, run them before opening OWEN Logic. Prefer the project's own commands; for this workspace, many PR200 projects use `python -m pytest`.
3. Use the `owen_logic_find_installation` MCP tool to confirm the executable path and version.
4. Use `owen_logic_smoke_test` for a basic GUI check. Pass `project_path` only when the user gives or the workspace clearly contains the intended OWEN Logic project file.
5. When a visual result matters, use `owen_logic_screenshot` and report the absolute PNG path.
6. For focused UI automation, use `owen_logic_focus_window` and `owen_logic_send_hotkey` only for simple, reversible navigation such as opening a file dialog. Avoid device download/upload actions unless the user explicitly asks.
7. Report what was verified, what was not verified, and any remaining manual OWEN Logic steps.

## MCP Tools

The preferred callable tools are `owen_logic_*`. In this workspace they are normally reachable via `mcp__artifact_tools__` to avoid exceeding the Codex Desktop MCP startup set. If neither `mcp__artifact_tools__owen_logic_*` nor a standalone `mcp__owen_logic__` namespace is visible in the current session, tell the user Codex may need to restart or reload MCP servers after editing the active `$CODEX_HOME\config.toml` and refreshing any default user-home compatibility mirror.

- `owen_logic_find_installation`: locate `ProgramRelayFBD.exe`, report version, and locate the ProjectJsonConverter executable.
- `owen_logic_list_processes`: list running `ProgramRelayFBD.exe` processes and matching windows.
- `owen_logic_list_windows`: inspect visible top-level windows.
- `owen_logic_launch`: start OWEN Logic, optionally with a project path.
- `owen_logic_smoke_test`: find or launch OWEN Logic, wait for the main window, and optionally screenshot it.
- `owen_logic_screenshot`: capture the first matching OWEN Logic window as PNG.
- `owen_logic_focus_window`: bring a matching OWEN Logic window forward.
- `owen_logic_send_hotkey`: send simple hotkeys to the OWEN Logic window.

## Local Paths

Default installation paths on this machine:

- `C:\Program Files\Owen\OWEN Logic\ProgramRelayFBD.exe`
- `C:\Program Files\Owen\OWEN Logic\ProjectJsonConverter\ProgramRelayFBD.exe`

In the `owen-logic-ai-workbench` repository the MCP server script lives at `mcp/owen_logic_server.py`. In this workspace it is launched through `07_TOOLS\ai_capabilities\launchers\mcp-runner.cmd owen_logic`.

Reusable PR200/COM helpers live in `tools/pr200/`:

- `owen_logic_com_emulator.py` for PR200 COM/Modbus/OWEN protocol emulation.
- `pr200_debug_extract.py` for reconstructing upload images and online-debug command blocks from COM logs.
- `debug_emulator_audit.py` for byte-level validation of debug-cell values.

## Project Review

For `.st` files, review them as IEC 61131-3 Structured Text intended for OWEN Logic. Check declarations, timers, trigger logic, state retention, edge cases after power-up, manual/auto priority, alarm reset behavior, and whether comments/test cases match the implementation.

For generated Python simulations, verify that they preserve the intended PLC scan semantics: one scan updates inputs, timers, state, outputs, and diagnostics deterministically. Prefer tests that cover startup state, mode switching, command priority, fault paths, and timing boundaries.

For more detailed testing notes, read `references/workflow.md` only when the task needs deeper guidance.

## Guardrails

- Keep GUI automation non-destructive by default.
- Do not download to a real controller, erase device memory, update firmware, or change communication settings unless the user explicitly requests that action.
- If OWEN Logic is already open, avoid closing it. Work with the existing window and report that it was already running.
