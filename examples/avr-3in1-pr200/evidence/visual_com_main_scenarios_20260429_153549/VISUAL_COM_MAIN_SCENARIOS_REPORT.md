# Visual COM Main Scenario Test

Started: 2026-04-29T15:35:49
Input file: `C:\__SELF_PC__\AVR_3IN1_PR200\pr200_reverse\avr3in1_live_inputs.json`
COM log: `C:\__SELF_PC__\AVR_3IN1_PR200\owen_logic_com_emulator_COM22_runtime.stdout.log`

| # | Scenario | Result | Screenshot | Observed |
|---|---|---|---|---|
| 01 | `AUTO_PRIORITY_1_CLOSE_40F_Q1_STATE31` | OK | `01_AUTO_PRIORITY_1_CLOSE_40F_Q1_STATE31.png` | `{"udiInputDelaySec": [3], "xQ1": [1, 1], "xQ2": [0, 0], "xQ3": [0, 0], "xQ5": [0, 0], "udiState": [31], "xAutoMode": [1], "xAlarm": [0]}` |
| 02 | `ACTIVE_40F_HEALTHY_NO_COMMANDS` | OK | `02_ACTIVE_40F_HEALTHY_NO_COMMANDS.png` | `{"udiActive": [1], "xQ1": [0, 0], "xQ2": [0, 0], "xQ3": [0, 0], "xQ4": [0, 0], "xQ5": [0, 0], "xQ6": [0, 0], "udiState": [0], "xAlarm": [0]}` |
| 03 | `U1_LOST_ACTIVE_40F_OPEN_40F_Q2_STATE11` | OK | `03_U1_LOST_ACTIVE_40F_OPEN_40F_Q2_STATE11.png` | `{"udiActive": [1], "udiTarget": [2], "xQ1": [0, 0], "xQ2": [1, 1], "xQ3": [0, 0], "udiState": [11], "xAlarm": [0]}` |
| 04 | `U1_LOST_ALL_OFF_CLOSE_50F_Q3_STATE32` | OK | `04_U1_LOST_ALL_OFF_CLOSE_50F_Q3_STATE32.png` | `{"udiTarget": [2], "xQ1": [0, 0], "xQ2": [0, 0], "xQ3": [1, 1], "xQ4": [0, 0], "xQ5": [0, 0], "udiState": [32], "xAlarm": [0]}` |
| 05 | `U1_U2_LOST_ALL_OFF_CLOSE_60F_Q5_STATE33` | OK | `05_U1_U2_LOST_ALL_OFF_CLOSE_60F_Q5_STATE33.png` | `{"udiTarget": [3], "xQ1": [0, 0], "xQ3": [0, 0], "xQ5": [1, 1], "xQ6": [0, 0], "udiState": [33], "xAlarm": [0]}` |
| 06 | `NO_SOURCES_ALL_OFF_NO_SOURCE` | OK | `06_NO_SOURCES_ALL_OFF_NO_SOURCE.png` | `{"udiTarget": [0], "xQ1": [0, 0], "xQ3": [0, 0], "xQ5": [0, 0], "udiState": [0], "xNoSource": [1], "xAlarm": [0]}` |
| 07 | `UNDEFINED_QF1_ON_AND_OFF_ALARM` | OK | `07_UNDEFINED_QF1_ON_AND_OFF_ALARM.png` | `{"xAlarm": [1], "xAlarmUndefined": [1], "xQF1Undefined": [1], "xManualMode": [1], "xAutoMode": [0], "udiState": [90], "xQ1": [0, 0]}` |
| 08 | `UNDEFINED_QF2_NO_POSITION_ALARM` | OK | `08_UNDEFINED_QF2_NO_POSITION_ALARM.png` | `{"xAlarm": [1], "xAlarmUndefined": [1], "xQF2Undefined": [1], "xManualMode": [1], "xAutoMode": [0], "udiState": [90], "xQ3": [0, 0]}` |
| 09 | `PARALLEL_40F_50F_ONLY_OFF_COMMANDS` | OK | `09_PARALLEL_40F_50F_ONLY_OFF_COMMANDS.png` | `{"xAlarm": [1], "xAlarmParallel": [1], "xQ1": [0, 0], "xQ2": [1, 1], "xQ3": [0, 0], "xQ4": [1, 1], "xQ5": [0, 0], "udiState": [90]}` |
| 10 | `BREAKER_FAULT_QF3_MANUAL_ALARM` | OK | `10_BREAKER_FAULT_QF3_MANUAL_ALARM.png` | `{"xAlarm": [1], "xAlarmFault": [1], "xManualMode": [1], "xAutoMode": [0], "udiState": [90], "xQ5": [0, 0]}` |
| 11 | `MANUAL_SELECTOR_BLOCKS_AUTO` | OK | `11_MANUAL_SELECTOR_BLOCKS_AUTO.png` | `{"xManualMode": [1], "xAutoMode": [0], "xAlarm": [0], "udiState": [90], "xQ1": [0, 0], "xQ3": [0, 0], "xQ5": [0, 0]}` |
