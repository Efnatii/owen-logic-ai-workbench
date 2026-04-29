# OWEN Logic Testing Workflow

Use this reference when a task needs more than a quick smoke test.

## Test Levels

1. Static project review: inspect `.st`, exported project files, diagrams, and README/test reports.
2. Simulation tests: run local Python or other deterministic simulations when present.
3. OWEN Logic smoke test: confirm the installed GUI starts and renders the project environment.
4. Visual verification: capture screenshots of the main window or opened project state.
5. Manual device operations: reserve controller communication, upload/download, and firmware actions for explicit user requests.

## Recommended Checks For PR200 Logic

- Startup state is deterministic after the first PLC scan.
- Manual commands have a documented priority over automatic logic, or the opposite is clearly specified.
- Fault and alarm resets are edge-triggered or level-triggered intentionally.
- Interlocks fail safe when inputs are missing or contradictory.
- Timers have tests at below-threshold, threshold, and above-threshold scan counts.
- Output commands cannot briefly energize mutually exclusive outputs in the same scan.
- Diagnostic bits expose enough state to explain why an output is blocked.

## MCP Usage Patterns

Basic app check:

```text
owen_logic_find_installation
owen_logic_smoke_test
```

Check an already-running GUI:

```text
owen_logic_list_processes
owen_logic_list_windows
owen_logic_screenshot
```

Open-file flow:

```text
owen_logic_focus_window
owen_logic_send_hotkey with ["CTRL", "O"]
```

Use hotkeys sparingly. Prefer project-level tests and screenshots over brittle menu automation.

## Reporting

Always separate:

- Verified automatically.
- Verified visually in OWEN Logic.
- Not verified because the project format/tool support was unavailable.
- Suggested next manual check inside OWEN Logic.
