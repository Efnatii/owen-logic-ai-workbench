# AVR 3-in-1 PR200 Example

This example contains the AVR 3-in-1 Structured Text, Python scan model, invariant tests, and PR200/COM helper tests that were used while validating the OWEN Logic project.

Useful paths:

- `src/FB_AVR_3IN1_PR200.st` - monolithic ST function block.
- `src/FB_AVR_3IN1_PR200_MODULAR.st` - modular ST variant.
- `src/avr_3in1_sim.py` - Python scan model used for invariant tests.
- `tests/` - unit, invariant, COM, debug-map, and emulator audit tests.
- `docs/` - project-specific notes and wiring documentation.
- `docs/diagrams/` - FBD and mounting diagrams.
- `docs/reports/` - saved test reports from the original validation sessions.
- `artifacts/` - extracted OWEN project data and PR200 debug/reverse artifacts.
- `evidence/` - curated screenshots and visual COM test evidence.

For tests that import shared PR200 tools:

```powershell
$repo = Resolve-Path "C:\path\to\owen-logic-ai-workbench"
$example = Join-Path $repo "examples\avr-3in1-pr200"
$env:PYTHONPATH = "$(Join-Path $repo 'tools\pr200');$(Join-Path $example 'src')"
python -m unittest `
  (Join-Path $example "tests\test_avr_3in1.py") `
  (Join-Path $example "tests\test_avr_3in1_invariants.py") `
  -v
```

The remaining tests depend on real `.owle` files, captured COM logs, screenshots, OWEN Logic GUI state, or COM emulation sessions.
