# Полная блок-схема соединений АВР 3-в-1

Файл показывает все соединения между малыми функциональными блоками из
`FB_AVR_3IN1_PR200_MODULAR.st`.

## 1. Полная схема верхнего уровня

```mermaid
flowchart LR
    %% External inputs
    MS["xManualSelector<br/>1 = ручной"]
    AR["xAutoReturn"]
    U1["xU1Ok"]
    U2["xU2Ok"]
    U3["xU3Ok"]
    F1["xQF1Fault<br/>40F авария"]
    F2["xQF2Fault<br/>50F авария"]
    F3["xQF3Fault<br/>60F авария"]

    QF1ON["xQF1On<br/>40F включен"]
    QF1OFF["xQF1Off<br/>40F выключен"]
    QF2ON["xQF2On<br/>50F включен"]
    QF2OFF["xQF2Off<br/>50F выключен"]
    QF3ON["xQF3On<br/>60F включен"]
    QF3OFF["xQF3Off<br/>60F выключен"]

    %% Blocks
    D1["QF40FDiag<br/>FB_AVR_QF_DIAG"]
    D2["QF50FDiag<br/>FB_AVR_QF_DIAG"]
    D3["QF60FDiag<br/>FB_AVR_QF_DIAG"]

    P["Priority3<br/>FB_AVR_PRIORITY_3"]
    M["Mode3<br/>FB_AVR_MODE_3"]
    S["State3<br/>FB_AVR_STATE_3"]
    C["Commands3<br/>FB_AVR_COMMANDS_3"]

    %% Derived signals
    C1["xQF1Commanded<br/>State3.udiState = 11 OR 31"]
    C2["xQF2Commanded<br/>State3.udiState = 12 OR 32"]
    C3["xQF3Commanded<br/>State3.udiState = 13 OR 33"]
    AF["xAlarmFault<br/>F1 OR F2 OR F3"]
    AU["xAlarmUndefined<br/>D1.xUndefined OR D2.xUndefined OR D3.xUndefined"]
    AOFF["xAllOffConfirmed<br/>xQF1Off AND xQF2Off AND xQF3Off<br/>AND NOT xAlarmUndefined"]

    %% External outputs
    Q1["Q1 / xQ1<br/>включить 40F"]
    Q2["Q2 / xQ2<br/>выключить 40F"]
    Q3["Q3 / xQ3<br/>включить 50F"]
    Q4["Q4 / xQ4<br/>выключить 50F"]
    Q5["Q5 / xQ5<br/>включить 60F"]
    Q6["Q6 / xQ6<br/>выключить 60F"]

    Active["udiActive"]
    Target["udiTarget"]
    StateOut["udiState"]
    AutoMode["xAutoMode"]
    ManualMode["xManualMode"]
    Alarm["xAlarm"]
    AlarmParallel["xAlarmParallel"]
    NoSource["xNoSource"]
    Undef1["xQF1Undefined"]
    Undef2["xQF2Undefined"]
    Undef3["xQF3Undefined"]

    %% Diagnostics inputs
    QF1ON -->|"xOn"| D1
    QF1OFF -->|"xOff"| D1
    C1 -->|"xCommanded"| D1

    QF2ON -->|"xOn"| D2
    QF2OFF -->|"xOff"| D2
    C2 -->|"xCommanded"| D2

    QF3ON -->|"xOn"| D3
    QF3OFF -->|"xOff"| D3
    C3 -->|"xCommanded"| D3

    D1 -->|"xUndefined"| Undef1
    D2 -->|"xUndefined"| Undef2
    D3 -->|"xUndefined"| Undef3
    D1 -->|"xUndefined"| AU
    D2 -->|"xUndefined"| AU
    D3 -->|"xUndefined"| AU

    %% Priority inputs
    AR -->|"xAutoReturn"| P
    U1 -->|"xU1Ok"| P
    U2 -->|"xU2Ok"| P
    U3 -->|"xU3Ok"| P
    QF1ON -->|"xQF1On"| P
    QF2ON -->|"xQF2On"| P
    QF3ON -->|"xQF3On"| P
    F1 -->|"xQF1Fault"| P
    F2 -->|"xQF2Fault"| P
    F3 -->|"xQF3Fault"| P

    %% Priority outputs
    P -->|"udiActive"| Active
    P -->|"udiActive"| S
    P -->|"udiTarget"| Target
    P -->|"udiTarget"| S
    P -->|"xAlarmParallel"| AlarmParallel
    P -->|"xAlarmParallel"| M
    P -->|"xAlarmParallel"| C
    P -->|"xNoSource"| NoSource
    P -->|"xS1Ready"| S
    P -->|"xS2Ready"| S
    P -->|"xS3Ready"| S
    P -->|"xS1Ready"| C
    P -->|"xS2Ready"| C
    P -->|"xS3Ready"| C

    %% Mode inputs
    MS -->|"xManualSelector"| M
    F1 --> AF
    F2 --> AF
    F3 --> AF
    AF -->|"xAlarmFault"| M
    AU -->|"xAlarmUndefined"| M

    %% Mode outputs
    M -->|"xAlarm"| Alarm
    M -->|"xAlarm"| C
    M -->|"xAutoMode"| AutoMode
    M -->|"xAutoMode"| S
    M -->|"xAutoMode"| C
    M -->|"xManualMode"| ManualMode

    %% All off confirmed
    QF1OFF --> AOFF
    QF2OFF --> AOFF
    QF3OFF --> AOFF
    AU --> AOFF
    AOFF -->|"xAllOffConfirmed"| S

    %% State inputs from contacts
    QF1ON -->|"xQF1On"| S
    QF1OFF -->|"xQF1Off"| S
    QF2ON -->|"xQF2On"| S
    QF2OFF -->|"xQF2Off"| S
    QF3ON -->|"xQF3On"| S
    QF3OFF -->|"xQF3Off"| S

    %% State output
    S -->|"udiState"| StateOut
    S -->|"udiState"| C
    S --> C1
    S --> C2
    S --> C3

    %% Commands contact inputs
    QF1ON -->|"xQF1On"| C
    QF1OFF -->|"xQF1Off"| C
    QF2ON -->|"xQF2On"| C
    QF2OFF -->|"xQF2Off"| C
    QF3ON -->|"xQF3On"| C
    QF3OFF -->|"xQF3Off"| C

    %% Physical outputs
    C -->|"xQ1"| Q1
    C -->|"xQ2"| Q2
    C -->|"xQ3"| Q3
    C -->|"xQ4"| Q4
    C -->|"xQ5"| Q5
    C -->|"xQ6"| Q6
```

## 2. Диагностика допконтактов

```mermaid
flowchart LR
    S["State3.udiState"]

    S --> C1["xQF1Commanded<br/>11 OR 31"]
    S --> C2["xQF2Commanded<br/>12 OR 32"]
    S --> C3["xQF3Commanded<br/>13 OR 33"]

    QF1ON["xQF1On"] --> D1["QF40FDiag"]
    QF1OFF["xQF1Off"] --> D1
    C1 --> D1

    QF2ON["xQF2On"] --> D2["QF50FDiag"]
    QF2OFF["xQF2Off"] --> D2
    C2 --> D2

    QF3ON["xQF3On"] --> D3["QF60FDiag"]
    QF3OFF["xQF3Off"] --> D3
    C3 --> D3

    D1 --> U1["xQF1Undefined"]
    D2 --> U2["xQF2Undefined"]
    D3 --> U3["xQF3Undefined"]

    U1 --> AU["xAlarmUndefined"]
    U2 --> AU
    U3 --> AU
```

## 3. Приоритет и режим

```mermaid
flowchart LR
    U1["xU1Ok"] --> P["Priority3"]
    U2["xU2Ok"] --> P
    U3["xU3Ok"] --> P
    AR["xAutoReturn"] --> P
    QF1ON["xQF1On"] --> P
    QF2ON["xQF2On"] --> P
    QF3ON["xQF3On"] --> P
    F1["xQF1Fault"] --> P
    F2["xQF2Fault"] --> P
    F3["xQF3Fault"] --> P

    P -->|"udiActive"| S["State3"]
    P -->|"udiTarget"| S
    P -->|"xS1Ready/xS2Ready/xS3Ready"| S
    P -->|"xS1Ready/xS2Ready/xS3Ready"| C["Commands3"]
    P -->|"xAlarmParallel"| M["Mode3"]
    P -->|"xAlarmParallel"| C

    MS["xManualSelector"] --> M
    AF["xAlarmFault<br/>F1 OR F2 OR F3"] --> M
    AU["xAlarmUndefined"] --> M

    M -->|"xAutoMode"| S
    M -->|"xAutoMode"| C
    M -->|"xAlarm"| C
```

## 4. Автомат состояний и команды

```mermaid
flowchart LR
    P["Priority3<br/>udiActive, udiTarget,<br/>xS1Ready, xS2Ready, xS3Ready"] --> S["State3"]
    M["Mode3<br/>xAutoMode"] --> S
    AOFF["xAllOffConfirmed"] --> S

    QF1["xQF1On / xQF1Off"] --> S
    QF2["xQF2On / xQF2Off"] --> S
    QF3["xQF3On / xQF3Off"] --> S

    S -->|"udiState"| C["Commands3"]
    M -->|"xAutoMode, xAlarm"| C
    P -->|"xAlarmParallel"| C
    P -->|"xS1Ready, xS2Ready, xS3Ready"| C
    QF1 --> C
    QF2 --> C
    QF3 --> C

    C -->|"xQ1"| Q1["Q1 включить 40F"]
    C -->|"xQ2"| Q2["Q2 выключить 40F"]
    C -->|"xQ3"| Q3["Q3 включить 50F"]
    C -->|"xQ4"| Q4["Q4 выключить 50F"]
    C -->|"xQ5"| Q5["Q5 включить 60F"]
    C -->|"xQ6"| Q6["Q6 выключить 60F"]
```

