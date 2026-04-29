FUNCTION_BLOCK FB_AVR_QF_DIAG
VAR_INPUT
    ///<Description>Допконтакт включенного положения</Description>
    xOn : BOOL;

    ///<Description>Допконтакт выключенного положения</Description>
    xOff : BOOL;

    ///<Description>Этому автомату сейчас дана команда включения или выключения</Description>
    xCommanded : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Оба допконтакта одновременно активны</Description>
    xInvalid : BOOL;

    ///<Description>Оба допконтакта одновременно неактивны</Description>
    xNoPosition : BOOL;

    ///<Description>Неопределенное состояние допконтактов</Description>
    xUndefined : BOOL;
END_VAR

xInvalid := xOn AND xOff;
xNoPosition := (NOT xOn) AND (NOT xOff);
xUndefined := xInvalid OR (xNoPosition AND (NOT xCommanded));

END_FUNCTION_BLOCK


FUNCTION_BLOCK FB_AVR_PRIORITY_3
VAR_INPUT
    ///<Description>Разрешить автовозврат на более приоритетный ввод</Description>
    xAutoReturn : BOOL := TRUE;

    ///<Description>Задержка подтверждения смены целевого ввода, секунд. 0 = без задержки</Description>
    udiInputDelaySec : UDINT := 0;

    ///<Description>Ввод 1: напряжение в норме</Description>
    xU1Ok : BOOL;

    ///<Description>Ввод 2: напряжение в норме</Description>
    xU2Ok : BOOL;

    ///<Description>Ввод 3: напряжение в норме</Description>
    xU3Ok : BOOL;

    ///<Description>40F включен</Description>
    xQF1On : BOOL;

    ///<Description>50F включен</Description>
    xQF2On : BOOL;

    ///<Description>60F включен</Description>
    xQF3On : BOOL;

    ///<Description>40F авария</Description>
    xQF1Fault : BOOL;

    ///<Description>50F авария</Description>
    xQF2Fault : BOOL;

    ///<Description>60F авария</Description>
    xQF3Fault : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Ввод 1 готов к работе</Description>
    xS1Ready : BOOL;

    ///<Description>Ввод 2 готов к работе</Description>
    xS2Ready : BOOL;

    ///<Description>Ввод 3 готов к работе</Description>
    xS3Ready : BOOL;

    ///<Description>Количество включенных вводов</Description>
    udiOnCount : UDINT;

    ///<Description>Активный ввод: 0 нет, 1 ввод 1, 2 ввод 2, 3 ввод 3</Description>
    udiActive : UDINT;

    ///<Description>Целевой ввод по мгновенному состоянию напряжений до задержки</Description>
    udiRawTarget : UDINT;

    ///<Description>Выбранный ввод по приоритету</Description>
    udiTarget : UDINT;

    ///<Description>Кандидат целевого ввода, ожидающий окончания задержки</Description>
    udiPendingTarget : UDINT;

    ///<Description>Счетчик задержки подтверждения целевого ввода, секунд</Description>
    udiDelayCounterSec : UDINT;

    ///<Description>Одновременно включено больше одного ввода</Description>
    xAlarmParallel : BOOL;

    ///<Description>TRUE = идет задержка перед принятием нового целевого ввода</Description>
    xTargetDelayActive : BOOL;

    ///<Description>Нет доступного ввода</Description>
    xNoSource : BOOL;
END_VAR

VAR
    xActiveReady : BOOL;
    xTargetInitialized : BOOL;
    udiStableTarget : UDINT;
END_VAR

xS1Ready := xU1Ok AND NOT xQF1Fault;
xS2Ready := xU2Ok AND NOT xQF2Fault;
xS3Ready := xU3Ok AND NOT xQF3Fault;

udiOnCount := 0;
IF xQF1On THEN udiOnCount := udiOnCount + 1; END_IF;
IF xQF2On THEN udiOnCount := udiOnCount + 1; END_IF;
IF xQF3On THEN udiOnCount := udiOnCount + 1; END_IF;

xAlarmParallel := udiOnCount > 1;

udiActive := 0;
IF udiOnCount = 1 THEN
    IF xQF1On THEN udiActive := 1; END_IF;
    IF xQF2On THEN udiActive := 2; END_IF;
    IF xQF3On THEN udiActive := 3; END_IF;
END_IF;

udiRawTarget := 0;
IF xS1Ready THEN
    udiRawTarget := 1;
ELSIF xS2Ready THEN
    udiRawTarget := 2;
ELSIF xS3Ready THEN
    udiRawTarget := 3;
END_IF;

xActiveReady := FALSE;
IF (udiActive = 1) AND xS1Ready THEN xActiveReady := TRUE; END_IF;
IF (udiActive = 2) AND xS2Ready THEN xActiveReady := TRUE; END_IF;
IF (udiActive = 3) AND xS3Ready THEN xActiveReady := TRUE; END_IF;

IF (NOT xAutoReturn) AND xActiveReady THEN
    udiRawTarget := udiActive;
END_IF;

IF NOT xTargetInitialized THEN
    udiStableTarget := udiRawTarget;
    udiPendingTarget := udiRawTarget;
    udiDelayCounterSec := 0;
    xTargetInitialized := TRUE;
ELSIF udiInputDelaySec = 0 THEN
    udiStableTarget := udiRawTarget;
    udiPendingTarget := udiRawTarget;
    udiDelayCounterSec := 0;
ELSIF udiRawTarget = udiStableTarget THEN
    udiPendingTarget := udiRawTarget;
    udiDelayCounterSec := 0;
ELSE
    IF udiRawTarget <> udiPendingTarget THEN
        udiPendingTarget := udiRawTarget;
        udiDelayCounterSec := 0;
    ELSIF udiDelayCounterSec < udiInputDelaySec THEN
        udiDelayCounterSec := udiDelayCounterSec + 1;
    END_IF;

    IF udiDelayCounterSec >= udiInputDelaySec THEN
        udiStableTarget := udiPendingTarget;
        udiDelayCounterSec := 0;
    END_IF;
END_IF;

udiTarget := udiStableTarget;
xTargetDelayActive := udiRawTarget <> udiTarget;

xNoSource := udiTarget = 0;

END_FUNCTION_BLOCK


FUNCTION_BLOCK FB_AVR_MODE_3
VAR_INPUT
    ///<Description>Переключатель авто/ручной. TRUE = ручной режим</Description>
    xManualSelector : BOOL;

    ///<Description>Есть авария автомата 40F, 50F или 60F</Description>
    xAlarmFault : BOOL;

    ///<Description>Одновременно включено больше одного ввода</Description>
    xAlarmParallel : BOOL;

    ///<Description>Неопределенное состояние допконтактов</Description>
    xAlarmUndefined : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Общая авария АВР</Description>
    xAlarm : BOOL;

    ///<Description>Аварийный режим по текущим входам</Description>
    xEmergencyMode : BOOL;

    ///<Description>АВР находится в автоматическом режиме</Description>
    xAutoMode : BOOL;

    ///<Description>АВР находится в ручном режиме</Description>
    xManualMode : BOOL;
END_VAR

xAlarm := xAlarmFault OR xAlarmParallel OR xAlarmUndefined;
xEmergencyMode := xAlarm;
xManualMode := xManualSelector OR xEmergencyMode;
xAutoMode := (NOT xManualSelector) AND (NOT xEmergencyMode);

END_FUNCTION_BLOCK


FUNCTION_BLOCK FB_AVR_STATE_3
VAR_INPUT
    ///<Description>АВР находится в автоматическом режиме</Description>
    xAutoMode : BOOL;

    ///<Description>Выбранный ввод по приоритету</Description>
    udiTarget : UDINT;

    ///<Description>Активный ввод</Description>
    udiActive : UDINT;

    ///<Description>Все три автомата подтверждены выключенными</Description>
    xAllOffConfirmed : BOOL;

    ///<Description>40F включен</Description>
    xQF1On : BOOL;

    ///<Description>40F выключен</Description>
    xQF1Off : BOOL;

    ///<Description>50F включен</Description>
    xQF2On : BOOL;

    ///<Description>50F выключен</Description>
    xQF2Off : BOOL;

    ///<Description>60F включен</Description>
    xQF3On : BOOL;

    ///<Description>60F выключен</Description>
    xQF3Off : BOOL;

    ///<Description>Ввод 1 готов</Description>
    xS1Ready : BOOL;

    ///<Description>Ввод 2 готов</Description>
    xS2Ready : BOOL;

    ///<Description>Ввод 3 готов</Description>
    xS3Ready : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Состояние автомата АВР</Description>
    udiState : UDINT;
END_VAR

IF xAutoMode THEN
    CASE udiState OF
        0:
            IF udiTarget = 0 THEN
                IF udiActive = 1 THEN
                    udiState := 11;
                ELSIF udiActive = 2 THEN
                    udiState := 12;
                ELSIF udiActive = 3 THEN
                    udiState := 13;
                END_IF;
            ELSIF udiActive = udiTarget THEN
                udiState := 0;
            ELSIF udiActive = 1 THEN
                udiState := 11;
            ELSIF udiActive = 2 THEN
                udiState := 12;
            ELSIF udiActive = 3 THEN
                udiState := 13;
            ELSIF xAllOffConfirmed THEN
                udiState := 20;
            END_IF;

        11:
            IF xQF1Off THEN
                udiState := 20;
            END_IF;

        12:
            IF xQF2Off THEN
                udiState := 20;
            END_IF;

        13:
            IF xQF3Off THEN
                udiState := 20;
            END_IF;

        20:
            IF udiTarget = 0 THEN
                udiState := 0;
            ELSIF NOT xAllOffConfirmed THEN
                udiState := 0;
            ELSIF udiTarget = 1 THEN
                udiState := 31;
            ELSIF udiTarget = 2 THEN
                udiState := 32;
            ELSIF udiTarget = 3 THEN
                udiState := 33;
            ELSE
                udiState := 0;
            END_IF;

        31:
            IF xQF1On THEN
                udiState := 0;
            ELSIF NOT xS1Ready THEN
                udiState := 0;
            END_IF;

        32:
            IF xQF2On THEN
                udiState := 0;
            ELSIF NOT xS2Ready THEN
                udiState := 0;
            END_IF;

        33:
            IF xQF3On THEN
                udiState := 0;
            ELSIF NOT xS3Ready THEN
                udiState := 0;
            END_IF;
    ELSE
        udiState := 0;
    END_CASE;
ELSE
    udiState := 90;
END_IF;

END_FUNCTION_BLOCK


FUNCTION_BLOCK FB_AVR_COMMANDS_3
VAR_INPUT
    ///<Description>АВР находится в автоматическом режиме</Description>
    xAutoMode : BOOL;

    ///<Description>Общая авария АВР</Description>
    xAlarm : BOOL;

    ///<Description>Одновременно включено больше одного ввода</Description>
    xAlarmParallel : BOOL;

    ///<Description>Состояние автомата АВР</Description>
    udiState : UDINT;

    ///<Description>Ввод 1 готов</Description>
    xS1Ready : BOOL;

    ///<Description>Ввод 2 готов</Description>
    xS2Ready : BOOL;

    ///<Description>Ввод 3 готов</Description>
    xS3Ready : BOOL;

    ///<Description>40F включен</Description>
    xQF1On : BOOL;

    ///<Description>40F выключен</Description>
    xQF1Off : BOOL;

    ///<Description>50F включен</Description>
    xQF2On : BOOL;

    ///<Description>50F выключен</Description>
    xQF2Off : BOOL;

    ///<Description>60F включен</Description>
    xQF3On : BOOL;

    ///<Description>60F выключен</Description>
    xQF3Off : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Q1: включить 40F</Description>
    xQ1 : BOOL;

    ///<Description>Q2: выключить 40F</Description>
    xQ2 : BOOL;

    ///<Description>Q3: включить 50F</Description>
    xQ3 : BOOL;

    ///<Description>Q4: выключить 50F</Description>
    xQ4 : BOOL;

    ///<Description>Q5: включить 60F</Description>
    xQ5 : BOOL;

    ///<Description>Q6: выключить 60F</Description>
    xQ6 : BOOL;
END_VAR

xQ1 := FALSE;
xQ2 := FALSE;
xQ3 := FALSE;
xQ4 := FALSE;
xQ5 := FALSE;
xQ6 := FALSE;

IF xAutoMode THEN
    xQ1 := (udiState = 31) AND xS1Ready AND
           xQF2Off AND xQF3Off AND (NOT xAlarm);
    xQ2 := (udiState = 11) AND (NOT xQF1Off) AND (NOT xAlarm);

    xQ3 := (udiState = 32) AND xS2Ready AND
           xQF1Off AND xQF3Off AND (NOT xAlarm);
    xQ4 := (udiState = 12) AND (NOT xQF2Off) AND (NOT xAlarm);

    xQ5 := (udiState = 33) AND xS3Ready AND
           xQF1Off AND xQF2Off AND (NOT xAlarm);
    xQ6 := (udiState = 13) AND (NOT xQF3Off) AND (NOT xAlarm);
END_IF;

// При пересечении вводов разрешены только команды отключения.
IF xAlarmParallel THEN
    xQ1 := FALSE;
    xQ3 := FALSE;
    xQ5 := FALSE;

    xQ2 := xQF1On;
    xQ4 := xQF2On;
    xQ6 := xQF3On;
END_IF;

END_FUNCTION_BLOCK


FUNCTION_BLOCK FB_AVR_3IN1_PR200_MODULAR
VAR_INPUT
    ///<Description>Переключатель авто/ручной. TRUE = ручной режим</Description>
    xManualSelector : BOOL := FALSE;

    ///<Description>Разрешить автовозврат на более приоритетный ввод</Description>
    xAutoReturn : BOOL := TRUE;

    ///<Description>Задержка подтверждения смены целевого ввода, секунд. 0 = без задержки</Description>
    udiInputDelaySec : UDINT := 0;

    ///<Description>Ввод 1: напряжение в норме</Description>
    xU1Ok : BOOL;

    ///<Description>Ввод 2: напряжение в норме</Description>
    xU2Ok : BOOL;

    ///<Description>Ввод 3: напряжение в норме</Description>
    xU3Ok : BOOL;

    ///<Description>40F включен</Description>
    xQF1On : BOOL;

    ///<Description>40F выключен</Description>
    xQF1Off : BOOL;

    ///<Description>40F авария</Description>
    xQF1Fault : BOOL;

    ///<Description>50F включен</Description>
    xQF2On : BOOL;

    ///<Description>50F выключен</Description>
    xQF2Off : BOOL;

    ///<Description>50F авария</Description>
    xQF2Fault : BOOL;

    ///<Description>60F включен</Description>
    xQF3On : BOOL;

    ///<Description>60F выключен</Description>
    xQF3Off : BOOL;

    ///<Description>60F авария</Description>
    xQF3Fault : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Q1: включить 40F</Description>
    xQ1 : BOOL;

    ///<Description>Q2: выключить 40F</Description>
    xQ2 : BOOL;

    ///<Description>Q3: включить 50F</Description>
    xQ3 : BOOL;

    ///<Description>Q4: выключить 50F</Description>
    xQ4 : BOOL;

    ///<Description>Q5: включить 60F</Description>
    xQ5 : BOOL;

    ///<Description>Q6: выключить 60F</Description>
    xQ6 : BOOL;

    ///<Description>Активный ввод: 0 нет, 1 ввод 1, 2 ввод 2, 3 ввод 3</Description>
    udiActive : UDINT;

    ///<Description>Целевой ввод по мгновенному состоянию напряжений до задержки</Description>
    udiRawTarget : UDINT;

    ///<Description>Выбранный ввод по приоритету</Description>
    udiTarget : UDINT;

    ///<Description>Кандидат целевого ввода, ожидающий окончания задержки</Description>
    udiPendingTarget : UDINT;

    ///<Description>Счетчик задержки подтверждения целевого ввода, секунд</Description>
    udiDelayCounterSec : UDINT;

    ///<Description>Состояние автомата АВР</Description>
    udiState : UDINT;

    ///<Description>TRUE = идет задержка перед принятием нового целевого ввода</Description>
    xTargetDelayActive : BOOL;

    ///<Description>АВР находится в автоматическом режиме</Description>
    xAutoMode : BOOL;

    ///<Description>АВР находится в ручном режиме</Description>
    xManualMode : BOOL;

    ///<Description>Общая авария АВР</Description>
    xAlarm : BOOL;

    ///<Description>Авария 40F, 50F или 60F</Description>
    xAlarmFault : BOOL;

    ///<Description>Одновременно включено больше одного ввода</Description>
    xAlarmParallel : BOOL;

    ///<Description>Неопределенное состояние допконтактов</Description>
    xAlarmUndefined : BOOL;

    ///<Description>Неопределенное состояние допконтактов 40F</Description>
    xQF1Undefined : BOOL;

    ///<Description>Неопределенное состояние допконтактов 50F</Description>
    xQF2Undefined : BOOL;

    ///<Description>Неопределенное состояние допконтактов 60F</Description>
    xQF3Undefined : BOOL;

    ///<Description>Нет доступного ввода</Description>
    xNoSource : BOOL;
END_VAR

VAR
    QF40FDiag : FB_AVR_QF_DIAG;
    QF50FDiag : FB_AVR_QF_DIAG;
    QF60FDiag : FB_AVR_QF_DIAG;

    Priority3 : FB_AVR_PRIORITY_3;
    Mode3 : FB_AVR_MODE_3;
    State3 : FB_AVR_STATE_3;
    Commands3 : FB_AVR_COMMANDS_3;

    xQF1Commanded : BOOL;
    xQF2Commanded : BOOL;
    xQF3Commanded : BOOL;
    xAllOffConfirmed : BOOL;
END_VAR

xQF1Commanded := (State3.udiState = 11) OR (State3.udiState = 31);
xQF2Commanded := (State3.udiState = 12) OR (State3.udiState = 32);
xQF3Commanded := (State3.udiState = 13) OR (State3.udiState = 33);

QF40FDiag(
    xOn := xQF1On,
    xOff := xQF1Off,
    xCommanded := xQF1Commanded
);

QF50FDiag(
    xOn := xQF2On,
    xOff := xQF2Off,
    xCommanded := xQF2Commanded
);

QF60FDiag(
    xOn := xQF3On,
    xOff := xQF3Off,
    xCommanded := xQF3Commanded
);

xQF1Undefined := QF40FDiag.xUndefined;
xQF2Undefined := QF50FDiag.xUndefined;
xQF3Undefined := QF60FDiag.xUndefined;
xAlarmUndefined := xQF1Undefined OR xQF2Undefined OR xQF3Undefined;

Priority3(
    xAutoReturn := xAutoReturn,
    udiInputDelaySec := udiInputDelaySec,
    xU1Ok := xU1Ok,
    xU2Ok := xU2Ok,
    xU3Ok := xU3Ok,
    xQF1On := xQF1On,
    xQF2On := xQF2On,
    xQF3On := xQF3On,
    xQF1Fault := xQF1Fault,
    xQF2Fault := xQF2Fault,
    xQF3Fault := xQF3Fault
);

udiActive := Priority3.udiActive;
udiRawTarget := Priority3.udiRawTarget;
udiTarget := Priority3.udiTarget;
udiPendingTarget := Priority3.udiPendingTarget;
udiDelayCounterSec := Priority3.udiDelayCounterSec;
xTargetDelayActive := Priority3.xTargetDelayActive;
xAlarmParallel := Priority3.xAlarmParallel;
xNoSource := Priority3.xNoSource;
xAlarmFault := xQF1Fault OR xQF2Fault OR xQF3Fault;
xAllOffConfirmed := xQF1Off AND xQF2Off AND xQF3Off AND NOT xAlarmUndefined;

Mode3(
    xManualSelector := xManualSelector,
    xAlarmFault := xAlarmFault,
    xAlarmParallel := xAlarmParallel,
    xAlarmUndefined := xAlarmUndefined
);

xAlarm := Mode3.xAlarm;
xManualMode := Mode3.xManualMode;
xAutoMode := Mode3.xAutoMode;

State3(
    xAutoMode := xAutoMode,
    udiTarget := udiTarget,
    udiActive := udiActive,
    xAllOffConfirmed := xAllOffConfirmed,
    xQF1On := xQF1On,
    xQF1Off := xQF1Off,
    xQF2On := xQF2On,
    xQF2Off := xQF2Off,
    xQF3On := xQF3On,
    xQF3Off := xQF3Off,
    xS1Ready := Priority3.xS1Ready,
    xS2Ready := Priority3.xS2Ready,
    xS3Ready := Priority3.xS3Ready
);

udiState := State3.udiState;

Commands3(
    xAutoMode := xAutoMode,
    xAlarm := xAlarm,
    xAlarmParallel := xAlarmParallel,
    udiState := udiState,
    xS1Ready := Priority3.xS1Ready,
    xS2Ready := Priority3.xS2Ready,
    xS3Ready := Priority3.xS3Ready,
    xQF1On := xQF1On,
    xQF1Off := xQF1Off,
    xQF2On := xQF2On,
    xQF2Off := xQF2Off,
    xQF3On := xQF3On,
    xQF3Off := xQF3Off
);

xQ1 := Commands3.xQ1;
xQ2 := Commands3.xQ2;
xQ3 := Commands3.xQ3;
xQ4 := Commands3.xQ4;
xQ5 := Commands3.xQ5;
xQ6 := Commands3.xQ6;

END_FUNCTION_BLOCK
