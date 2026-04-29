FUNCTION_BLOCK FB_AVR_3IN1_PR200
VAR_INPUT
    ///<Description>Переключатель авто/ручной. TRUE = ручной режим</Description>
    xManualSelector : BOOL := FALSE; // 1 = ручной, 0 = авто

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

    ///<Description>Состояние автомата АВР: 0 ожидание, 11..13 отключение, 20 все отключено, 31..33 включение, 90 ручной/авария</Description>
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
    xS1Ready : BOOL;
    xS2Ready : BOOL;
    xS3Ready : BOOL;

    xAnyFault : BOOL;
    xAnyOn : BOOL;
    xActiveReady : BOOL;
    xEmergencyMode : BOOL;
    xAllOffConfirmed : BOOL;

    xQF1Invalid : BOOL;
    xQF2Invalid : BOOL;
    xQF3Invalid : BOOL;
    xQF1NoPosition : BOOL;
    xQF2NoPosition : BOOL;
    xQF3NoPosition : BOOL;
    xQF1Commanded : BOOL;
    xQF2Commanded : BOOL;
    xQF3Commanded : BOOL;

    xTargetInitialized : BOOL;
    udiStableTarget : UDINT;

    udiOnCount : UDINT;

END_VAR

xAnyFault := xQF1Fault OR xQF2Fault OR xQF3Fault;

xQF1Invalid := xQF1On AND xQF1Off;
xQF2Invalid := xQF2On AND xQF2Off;
xQF3Invalid := xQF3On AND xQF3Off;

xQF1NoPosition := (NOT xQF1On) AND (NOT xQF1Off);
xQF2NoPosition := (NOT xQF2On) AND (NOT xQF2Off);
xQF3NoPosition := (NOT xQF3On) AND (NOT xQF3Off);

xQF1Commanded := (udiState = 11) OR (udiState = 31);
xQF2Commanded := (udiState = 12) OR (udiState = 32);
xQF3Commanded := (udiState = 13) OR (udiState = 33);

// Во время выполнения команды допускается промежуточное положение:
// оба допконтакта могут быть FALSE, пока автомат идет.
// Вне команды такое состояние считается неопределенным.
xQF1Undefined := xQF1Invalid OR (xQF1NoPosition AND NOT xQF1Commanded);
xQF2Undefined := xQF2Invalid OR (xQF2NoPosition AND NOT xQF2Commanded);
xQF3Undefined := xQF3Invalid OR (xQF3NoPosition AND NOT xQF3Commanded);
xAlarmUndefined := xQF1Undefined OR xQF2Undefined OR xQF3Undefined;

xS1Ready := xU1Ok AND NOT xQF1Fault;
xS2Ready := xU2Ok AND NOT xQF2Fault;
xS3Ready := xU3Ok AND NOT xQF3Fault;

udiOnCount := 0;
IF xQF1On THEN udiOnCount := udiOnCount + 1; END_IF;
IF xQF2On THEN udiOnCount := udiOnCount + 1; END_IF;
IF xQF3On THEN udiOnCount := udiOnCount + 1; END_IF;

xAnyOn := udiOnCount > 0;
xAlarmParallel := udiOnCount > 1;
xAllOffConfirmed := xQF1Off AND xQF2Off AND xQF3Off AND NOT xAlarmUndefined;

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

xEmergencyMode := xAnyFault OR xAlarmParallel OR xAlarmUndefined;

xManualMode := xManualSelector OR xEmergencyMode;
xAutoMode := (NOT xManualSelector) AND (NOT xEmergencyMode);

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

xManualMode := xManualSelector OR xEmergencyMode;
xAutoMode := (NOT xManualSelector) AND (NOT xEmergencyMode);

xAlarmFault := xAnyFault;
xAlarm := xAlarmFault OR xAlarmParallel OR xAlarmUndefined;

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

// Для ПЭСПЭЗ пересечение вводов обрабатывается жестко:
// команды включения запрещены, разрешены только команды отключения включенных вводов.
IF xAlarmParallel THEN
    xQ1 := FALSE;
    xQ3 := FALSE;
    xQ5 := FALSE;

    xQ2 := xQF1On;
    xQ4 := xQF2On;
    xQ6 := xQF3On;
END_IF;

END_FUNCTION_BLOCK
