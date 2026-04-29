# Таблица соединения малых блоков АВР 3-в-1

Файл с блоками: `FB_AVR_3IN1_PR200_MODULAR.st`.

## Вариант 1: самый простой

Использовать готовый сборочный блок `FB_AVR_3IN1_PR200_MODULAR`.

Он имеет те же внешние входы и выходы, что основной большой блок:

- входы: `xManualSelector`, `xAutoReturn`, `xU1Ok`, `xU2Ok`, `xU3Ok`, `xQF1On`, `xQF1Off`, `xQF1Fault`, `xQF2On`, `xQF2Off`, `xQF2Fault`, `xQF3On`, `xQF3Off`, `xQF3Fault`;
- выходы: `xQ1`, `xQ2`, `xQ3`, `xQ4`, `xQ5`, `xQ6`, диагностика и состояния.

## Вариант 2: собрать на блок-схеме вручную

### 1. Диагностика допконтактов

| Экземпляр | Тип блока | Вход блока | Куда подключить | Выход блока | Куда подключить |
|---|---|---|---|---|---|
| `QF40FDiag` | `FB_AVR_QF_DIAG` | `xOn` | `xQF1On` | `xUndefined` | `xQF1Undefined` |
| `QF40FDiag` | `FB_AVR_QF_DIAG` | `xOff` | `xQF1Off` | `xInvalid` | диагностика, опционально |
| `QF40FDiag` | `FB_AVR_QF_DIAG` | `xCommanded` | `xQF1Commanded` | `xNoPosition` | диагностика, опционально |
| `QF50FDiag` | `FB_AVR_QF_DIAG` | `xOn` | `xQF2On` | `xUndefined` | `xQF2Undefined` |
| `QF50FDiag` | `FB_AVR_QF_DIAG` | `xOff` | `xQF2Off` | `xInvalid` | диагностика, опционально |
| `QF50FDiag` | `FB_AVR_QF_DIAG` | `xCommanded` | `xQF2Commanded` | `xNoPosition` | диагностика, опционально |
| `QF60FDiag` | `FB_AVR_QF_DIAG` | `xOn` | `xQF3On` | `xUndefined` | `xQF3Undefined` |
| `QF60FDiag` | `FB_AVR_QF_DIAG` | `xOff` | `xQF3Off` | `xInvalid` | диагностика, опционально |
| `QF60FDiag` | `FB_AVR_QF_DIAG` | `xCommanded` | `xQF3Commanded` | `xNoPosition` | диагностика, опционально |

Командуемые состояния для входа `xCommanded`:

| Сигнал | Как получить |
|---|---|
| `xQF1Commanded` | `(State3.udiState = 11) OR (State3.udiState = 31)` |
| `xQF2Commanded` | `(State3.udiState = 12) OR (State3.udiState = 32)` |
| `xQF3Commanded` | `(State3.udiState = 13) OR (State3.udiState = 33)` |

Общая неопределенность:

| Сигнал | Как получить |
|---|---|
| `xAlarmUndefined` | `QF40FDiag.xUndefined OR QF50FDiag.xUndefined OR QF60FDiag.xUndefined` |

### 2. Выбор приоритета

| Экземпляр | Тип блока | Вход блока | Куда подключить | Выход блока | Куда подключить |
|---|---|---|---|---|---|
| `Priority3` | `FB_AVR_PRIORITY_3` | `xAutoReturn` | `xAutoReturn` | `xS1Ready` | `State3.xS1Ready`, `Commands3.xS1Ready` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xU1Ok` | `xU1Ok` | `xS2Ready` | `State3.xS2Ready`, `Commands3.xS2Ready` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xU2Ok` | `xU2Ok` | `xS3Ready` | `State3.xS3Ready`, `Commands3.xS3Ready` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xU3Ok` | `xU3Ok` | `udiActive` | `State3.udiActive`, внешний `udiActive` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xQF1On` | `xQF1On` | `udiTarget` | `State3.udiTarget`, внешний `udiTarget` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xQF2On` | `xQF2On` | `xAlarmParallel` | `Mode3.xAlarmParallel`, `Commands3.xAlarmParallel`, внешний `xAlarmParallel` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xQF3On` | `xQF3On` | `xNoSource` | внешний `xNoSource` |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xQF1Fault` | `xQF1Fault` |  |  |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xQF2Fault` | `xQF2Fault` |  |  |
| `Priority3` | `FB_AVR_PRIORITY_3` | `xQF3Fault` | `xQF3Fault` |  |  |

### 3. Режимы и общая авария

| Экземпляр | Тип блока | Вход блока | Куда подключить | Выход блока | Куда подключить |
|---|---|---|---|---|---|
| `Mode3` | `FB_AVR_MODE_3` | `xManualSelector` | `xManualSelector` | `xAlarm` | `Commands3.xAlarm`, внешний `xAlarm` |
| `Mode3` | `FB_AVR_MODE_3` | `xAlarmFault` | `xQF1Fault OR xQF2Fault OR xQF3Fault` | `xEmergencyMode` | диагностика, опционально |
| `Mode3` | `FB_AVR_MODE_3` | `xAlarmParallel` | `Priority3.xAlarmParallel` | `xAutoMode` | `State3.xAutoMode`, `Commands3.xAutoMode`, внешний `xAutoMode` |
| `Mode3` | `FB_AVR_MODE_3` | `xAlarmUndefined` | `xAlarmUndefined` | `xManualMode` | внешний `xManualMode` |

### 4. Автомат состояний

Перед блоком `State3` сформировать:

| Сигнал | Как получить |
|---|---|
| `xAllOffConfirmed` | `xQF1Off AND xQF2Off AND xQF3Off AND NOT xAlarmUndefined` |

| Экземпляр | Тип блока | Вход блока | Куда подключить | Выход блока | Куда подключить |
|---|---|---|---|---|---|
| `State3` | `FB_AVR_STATE_3` | `xAutoMode` | `Mode3.xAutoMode` | `udiState` | `Commands3.udiState`, внешний `udiState`, сигналы `xQF*Commanded` |
| `State3` | `FB_AVR_STATE_3` | `udiTarget` | `Priority3.udiTarget` |  |  |
| `State3` | `FB_AVR_STATE_3` | `udiActive` | `Priority3.udiActive` |  |  |
| `State3` | `FB_AVR_STATE_3` | `xAllOffConfirmed` | `xAllOffConfirmed` |  |  |
| `State3` | `FB_AVR_STATE_3` | `xQF1On`, `xQF1Off` | `xQF1On`, `xQF1Off` |  |  |
| `State3` | `FB_AVR_STATE_3` | `xQF2On`, `xQF2Off` | `xQF2On`, `xQF2Off` |  |  |
| `State3` | `FB_AVR_STATE_3` | `xQF3On`, `xQF3Off` | `xQF3On`, `xQF3Off` |  |  |
| `State3` | `FB_AVR_STATE_3` | `xS1Ready`, `xS2Ready`, `xS3Ready` | `Priority3.xS1Ready`, `Priority3.xS2Ready`, `Priority3.xS3Ready` |  |  |

### 5. Команды на выходы

| Экземпляр | Тип блока | Вход блока | Куда подключить | Выход блока | Куда подключить |
|---|---|---|---|---|---|
| `Commands3` | `FB_AVR_COMMANDS_3` | `xAutoMode` | `Mode3.xAutoMode` | `xQ1` | `Q1`: включить `40F` |
| `Commands3` | `FB_AVR_COMMANDS_3` | `xAlarm` | `Mode3.xAlarm` | `xQ2` | `Q2`: выключить `40F` |
| `Commands3` | `FB_AVR_COMMANDS_3` | `xAlarmParallel` | `Priority3.xAlarmParallel` | `xQ3` | `Q3`: включить `50F` |
| `Commands3` | `FB_AVR_COMMANDS_3` | `udiState` | `State3.udiState` | `xQ4` | `Q4`: выключить `50F` |
| `Commands3` | `FB_AVR_COMMANDS_3` | `xS1Ready`, `xS2Ready`, `xS3Ready` | `Priority3.xS1Ready`, `Priority3.xS2Ready`, `Priority3.xS3Ready` | `xQ5` | `Q5`: включить `60F` |
| `Commands3` | `FB_AVR_COMMANDS_3` | `xQF1On`, `xQF1Off` | `xQF1On`, `xQF1Off` | `xQ6` | `Q6`: выключить `60F` |
| `Commands3` | `FB_AVR_COMMANDS_3` | `xQF2On`, `xQF2Off` | `xQF2On`, `xQF2Off` |  |  |
| `Commands3` | `FB_AVR_COMMANDS_3` | `xQF3On`, `xQF3Off` | `xQF3On`, `xQF3Off` |  |  |

## Смысл состояний `udiState`

| Значение | Смысл |
|---:|---|
| `0` | ожидание / нормальная работа |
| `11` | выключаем `40F` |
| `12` | выключаем `50F` |
| `13` | выключаем `60F` |
| `20` | все автоматы подтверждены выключенными, можно выбирать включение |
| `31` | включаем `40F` |
| `32` | включаем `50F` |
| `33` | включаем `60F` |
| `90` | ручной режим или аварийный режим |
