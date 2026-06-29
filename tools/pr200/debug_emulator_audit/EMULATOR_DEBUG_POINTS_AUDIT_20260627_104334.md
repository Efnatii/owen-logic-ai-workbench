# Emulator Debug Points Audit

Started: 2026-06-27T10:43:34
Symbol map: `C:\Users\Efnatii\Workspaces\__EGOR_GOROKHOVITSKY_WORKBENCH__\07_TOOLS\r\owen\examples\avr-3in1-pr200\artifacts\pr200_reverse\avr3in1_debug_symbol_map.json`

This audit drives the emulator through real Modbus function `0x41` packets and decodes the returned `ReadData` cells.

| # | Scenario | Result | Cells | Block | CRC | Observed key values |
|---|---|---|---:|---:|---|---|
| 01 | `priority_1_close_40f` | OK | 59 | 1 | OK | `{"udiState": [31], "xAlarm": [0], "xAutoMode": [1], "xManualMode": [0], "xQ1": [1, 1], "xQ2": [0, 0], "xQ3": [0, 0], "xQ5": [0, 0]}` |
| 02 | `active_40f_no_commands` | OK | 59 | 1 | OK | `{"udiActive": [1], "udiState": [0], "xAlarm": [0], "xAutoMode": [1], "xManualMode": [0], "xQ1": [0, 0], "xQ2": [0, 0], "xQ3": [0, 0], "xQ4": [0, 0], "xQ5": [0, 0], "xQ6": [0, 0]}` |
| 03 | `u1_lost_open_40f` | OK | 59 | 1 | OK | `{"udiActive": [1], "udiState": [11], "udiTarget": [2], "xAlarm": [0], "xAutoMode": [1], "xManualMode": [0], "xQ1": [0, 0], "xQ2": [1, 1], "xQ3": [0, 0]}` |
| 04 | `u1_lost_close_50f` | OK | 59 | 1 | OK | `{"udiState": [32], "udiTarget": [2], "xAlarm": [0], "xAutoMode": [1], "xManualMode": [0], "xQ1": [0, 0], "xQ3": [1, 1], "xQ4": [0, 0], "xQ5": [0, 0]}` |
| 05 | `u1_u2_lost_close_60f` | OK | 59 | 1 | OK | `{"udiState": [33], "udiTarget": [3], "xAlarm": [0], "xAutoMode": [1], "xManualMode": [0], "xQ1": [0, 0], "xQ3": [0, 0], "xQ5": [1, 1], "xQ6": [0, 0]}` |
| 06 | `no_sources` | OK | 59 | 1 | OK | `{"udiState": [0], "udiTarget": [0], "xAlarm": [0], "xAutoMode": [1], "xManualMode": [0], "xNoSource": [1], "xQ1": [0, 0], "xQ3": [0, 0], "xQ5": [0, 0]}` |
| 07 | `undefined_qf1_on_and_off` | OK | 59 | 1 | OK | `{"udiState": [90], "xAlarm": [1], "xAlarmUndefined": [1], "xAutoMode": [0], "xManualMode": [1], "xQF1Undefined": [1]}` |
| 08 | `undefined_qf2_no_position` | OK | 59 | 1 | OK | `{"udiState": [90], "xAlarm": [1], "xAlarmUndefined": [1], "xAutoMode": [0], "xManualMode": [1], "xQF2Undefined": [1]}` |
| 09 | `parallel_40f_50f_only_off` | OK | 59 | 1 | OK | `{"udiState": [90], "xAlarm": [1], "xAlarmParallel": [1], "xAutoMode": [0], "xManualMode": [1], "xQ1": [0, 0], "xQ2": [1, 1], "xQ3": [0, 0], "xQ4": [1, 1], "xQ5": [0, 0]}` |
| 10 | `qf3_fault` | OK | 59 | 1 | OK | `{"udiState": [90], "xAlarm": [1], "xAlarmFault": [1], "xAutoMode": [0], "xManualMode": [1], "xQ5": [0, 0]}` |
| 11 | `manual_selector_blocks_auto` | OK | 59 | 1 | OK | `{"udiState": [90], "xAlarm": [0], "xAutoMode": [0], "xManualMode": [1], "xQ1": [0, 0], "xQ3": [0, 0], "xQ5": [0, 0]}` |
