# OWEN Logic AI Workbench

Repository name: `owen-logic-ai-workbench`

This repository collects the AI-facing pieces for creating, inspecting, testing, and visually validating OWEN Logic / ProgramRelayFBD projects, especially PR100/PR200 Structured Text and FBD workflows.

## What Is Inside

```text
owen-logic-ai-workbench/
  mcp/
    owen_logic_server.py              # Local MCP server for OWEN Logic GUI checks
  skills/
    owen-logic-testing/               # Codex skill for OWEN Logic work
  tools/
    pr200/
      owen_logic_com_emulator.py      # COM/Modbus/OWEN protocol emulator
      pr200_debug_extract.py          # Program/debug-point extractor from COM logs
      pr200_avr_runtime.py            # AVR 3-in-1 runtime adapter
      debug_emulator_audit.py         # Byte-level debug-cell audit
      visual_com_main_scenarios.py    # Visual COM scenario runner
  examples/
    avr-2in1-section-pr200/
      src/                            # ST code and Python model
      tests/                          # Scenario and exhaustive invariant tests
      docs/                           # Test report
    avr-3in1-pr200/
      src/                            # ST code and Python model
      tests/                          # Example invariant and COM tests
      docs/                           # Notes, diagrams, reports
      artifacts/                      # Curated OWEN/PR200 extracted artifacts
      evidence/                       # Visual/debug evidence from test sessions
  config/
    codex-config.example.toml         # Example Codex MCP configuration
```

## Repository Purpose

Use this as a single project folder for AI-assisted OWEN Logic work:

- find and launch OWEN Logic;
- capture OWEN Logic window screenshots;
- smoke-test `.owle` projects;
- review OWEN Structured Text;
- emulate PR200 COM communication;
- reconstruct PR200 upload/debug command blocks from COM logs;
- map OWEN online-debug cells to function-block signals;
- run deterministic tests for AVR logic and debug-point mapping;
- keep АВР 3-в-1 and АВР 2-в-1 с секционированием examples in one repeatable place.

## Suggested Codex Installation

Copy or symlink the skill folder into the Codex skills directory:

```powershell
Copy-Item -Recurse -Force `
  C:\__SELF_PC__\owen-logic-ai-workbench\skills\owen-logic-testing `
  C:\Users\Alexandra\.codex\skills\owen-logic-testing
```

Register the MCP server in `C:\Users\Alexandra\.codex\config.toml`. Use `config/codex-config.example.toml` as the template.

## Python Setup

```powershell
cd C:\__SELF_PC__\owen-logic-ai-workbench
python -m pip install -r requirements.txt
```

The MCP server itself is intentionally lightweight. The PR200 emulator and visual tools use extra packages listed in `requirements.txt`.

## Quick Checks

Compile all Python files:

```powershell
Get-ChildItem -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

Run the OWEN Logic MCP server self-check by listing tools from Codex after registering the MCP server.

Run AVR 3-in-1 example tests by setting `PYTHONPATH` to include both the generic PR200 tools and the example source:

```powershell
$env:PYTHONPATH = "C:\__SELF_PC__\owen-logic-ai-workbench\tools\pr200;C:\__SELF_PC__\owen-logic-ai-workbench\examples\avr-3in1-pr200\src"
python -m unittest `
  C:\__SELF_PC__\owen-logic-ai-workbench\examples\avr-3in1-pr200\tests\test_avr_3in1.py `
  C:\__SELF_PC__\owen-logic-ai-workbench\examples\avr-3in1-pr200\tests\test_avr_3in1_invariants.py `
  -v
```

Full discovery in `examples/avr-3in1-pr200/tests` also includes COM/GUI/artifact tests and is intentionally hardware/workstation dependent.

Run AVR 2-in-1 with sectioning tests:

```powershell
$env:PYTHONPATH = "C:\__SELF_PC__\owen-logic-ai-workbench\examples\avr-2in1-section-pr200\src"
python -m unittest discover C:\__SELF_PC__\owen-logic-ai-workbench\examples\avr-2in1-section-pr200\tests -v
```

## Notes

Generated screenshots, COM logs, live captures, PDFs, and debug audit output are ignored by default. Keep reusable source and documentation in the repository; keep large runtime evidence outside git unless it is intentionally curated.
