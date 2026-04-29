# Визуальный тест основных инвариантов AVR 3 в 1 через OWEN Logic debug

Дата: 2026-04-29 14:35:45
COM: COM21 <-> COM22, значения ReadData берутся из C:\__SELF_PC__\AVR_3IN1_PR200\visual_debug_invariant_evidence\live_debug_values.txt

## Актуальная карта ключевых debug-ячеек
| Сигнал | Ячейки |
|---|---|
| xQ1/xQ2/xQ3/xQ4/xQ5/xQ6 | 27/50, 28/51, 29/52, 30/53, 31/54, 32/55 |
| udiActive, udiRawTarget, udiTarget, udiPendingTarget, udiDelayCounterSec, udiState | 33, 34, 35, 36, 37, 38 |
| xTargetDelayActive, xAutoMode, xManualMode, xAlarm | 39, 40, 41, 42 |
| xAlarmFault, xAlarmParallel, xAlarmUndefined | 43, 44, 45 |
| xQF1Undefined/xQF2Undefined/xQF3Undefined/xNoSource | 46, 47, 48, 49 |

## Сценарии

### 01_priority_1: Приоритет: все вводы в норме, все автоматы отключены -> включать 40F

- Инвариант: priority
- Ожидание: Q1=1, Q3=0, Q5=0; target=1; auto=1
- Отображённые команды: Q1=1 Q2=0 Q3=0 Q4=0 Q5=0 Q6=0
- Диагностика: active=0 raw=1 target=1 pending=1 counter=0 state=31 auto=1 manual=0 alarm=0
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:32.992
- Скрин FBD: visual_debug_invariant_evidence\scenario_01_priority_1_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_01_priority_1_full.png

### 02_delay_no_switch: Задержка 3 сек: кратковременная потеря ввода 1 не даёт команду переключения

- Инвариант: delay
- Ожидание: rawTarget=2, target=1, delayActive=1, все Q=0
- Отображённые команды: Q1=0 Q2=0 Q3=0 Q4=0 Q5=0 Q6=0
- Диагностика: active=1 raw=2 target=1 pending=2 counter=2 state=0 auto=1 manual=0 alarm=0
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:34.818
- Скрин FBD: visual_debug_invariant_evidence\scenario_02_delay_no_switch_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_02_delay_no_switch_full.png

### 03_turn_off_before_on: Нет пересечения: при переходе 40F -> 50F сначала только отключить 40F

- Инвариант: non-overlap
- Ожидание: Q2=1, Q3=0; включение другого ввода запрещено пока 40F не выключен
- Отображённые команды: Q1=0 Q2=1 Q3=0 Q4=0 Q5=0 Q6=0
- Диагностика: active=1 raw=2 target=2 pending=2 counter=0 state=11 auto=1 manual=0 alarm=0
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:36.653
- Скрин FBD: visual_debug_invariant_evidence\scenario_03_turn_off_before_on_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_03_turn_off_before_on_full.png

### 04_on_after_all_off: Нет пересечения: после подтверждения 40F выключен разрешено включить 50F

- Инвариант: non-overlap
- Ожидание: Q3=1 только после qf1Off=1 и все остальные off=1
- Отображённые команды: Q1=0 Q2=0 Q3=1 Q4=0 Q5=0 Q6=0
- Диагностика: active=0 raw=2 target=2 pending=2 counter=0 state=32 auto=1 manual=0 alarm=0
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:38.291
- Скрин FBD: visual_debug_invariant_evidence\scenario_04_on_after_all_off_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_04_on_after_all_off_full.png

### 05_fault_manual: Авария допконтакта: переход в ручной/аварийный режим, команды заблокированы

- Инвариант: fault-manual
- Ожидание: xAlarm=1, xAlarmFault=1, xManualMode=1, все Q=0
- Отображённые команды: Q1=0 Q2=0 Q3=0 Q4=0 Q5=0 Q6=0
- Диагностика: active=1 raw=1 target=1 pending=1 counter=0 state=90 auto=0 manual=1 alarm=1
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:40.112
- Скрин FBD: visual_debug_invariant_evidence\scenario_05_fault_manual_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_05_fault_manual_full.png

### 06_parallel_trip: Параллель включения: авария параллели и команды на отключение включённых автоматов

- Инвариант: parallel
- Ожидание: xAlarmParallel=1, Q2=1, Q4=1, команды включения Q1/Q3/Q5=0
- Отображённые команды: Q1=0 Q2=1 Q3=0 Q4=1 Q5=0 Q6=0
- Диагностика: active=0 raw=1 target=1 pending=1 counter=0 state=90 auto=0 manual=1 alarm=1
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:41.934
- Скрин FBD: visual_debug_invariant_evidence\scenario_06_parallel_trip_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_06_parallel_trip_full.png

### 07_undefined_contacts: Неопределённость допконтактов: 40F одновременно включен и выключен -> авария

- Инвариант: undefined
- Ожидание: xAlarmUndefined=1, xQF1Undefined=1, xManualMode=1, все Q=0
- Отображённые команды: Q1=0 Q2=0 Q3=0 Q4=0 Q5=0 Q6=0
- Диагностика: active=1 raw=1 target=1 pending=1 counter=0 state=90 auto=0 manual=1 alarm=1
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:43.758
- Скрин FBD: visual_debug_invariant_evidence\scenario_07_undefined_contacts_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_07_undefined_contacts_full.png

### 08_no_source: Нет доступных вводов: команд нет, xNoSource=1

- Инвариант: no-source
- Ожидание: rawTarget=0, target=0, xNoSource=1, все Q=0
- Отображённые команды: Q1=0 Q2=0 Q3=0 Q4=0 Q5=0 Q6=0
- Диагностика: active=0 raw=0 target=0 pending=0 counter=0 state=0 auto=1 manual=0 alarm=0
- COM ReadData: block=3, cells=59, matchFirst55=True, ts=2026-04-29T14:35:45.377
- Скрин FBD: visual_debug_invariant_evidence\scenario_08_no_source_wide.png
- Скрин всего окна: visual_debug_invariant_evidence\scenario_08_no_source_full.png
