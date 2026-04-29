FUNCTION_BLOCK FB_AVR_2IN1_SECTION_PR200
VAR_INPUT
    ///<Description>Переключатель авто/ручной. TRUE = ручной режим</Description>
    xManualSelector : BOOL := FALSE; // 1 = ручной, 0 = авто

    ///<Description>Разрешить автовозврат к нормальной схеме 10F + 20F, секционный 30F отключен</Description>
    xAutoReturn : BOOL := TRUE;

    ///<Description>Zaderzhka podtverzhdeniya smeny celevoj shemy po vhodam, sekund/ciklov. 0 = bez zaderzhki</Description>
    udiInputDelaySec : UDINT := 0;

    ///<Description>Zaderzhka vklyucheniya 30F sekcionnogo avtomata, sekund/ciklov. 0 = bez zaderzhki</Description>
    udiSectionCloseDelaySec : UDINT := 0;

    ///<Description>Ввод 1: напряжение в норме</Description>
    xU1Ok : BOOL;

    ///<Description>Ввод 2: напряжение в норме</Description>
    xU2Ok : BOOL;

    ///<Description>10F ввод 1 включен</Description>
    xQF1On : BOOL;

    ///<Description>10F ввод 1 выключен</Description>
    xQF1Off : BOOL;

    ///<Description>10F ввод 1 авария</Description>
    xQF1Fault : BOOL;

    ///<Description>20F ввод 2 включен</Description>
    xQF2On : BOOL;

    ///<Description>20F ввод 2 выключен</Description>
    xQF2Off : BOOL;

    ///<Description>20F ввод 2 авария</Description>
    xQF2Fault : BOOL;

    ///<Description>30F секционный автомат включен</Description>
    xQFSOn : BOOL;

    ///<Description>30F секционный автомат выключен</Description>
    xQFSOff : BOOL;

    ///<Description>30F секционный автомат авария</Description>
    xQFSFault : BOOL;
END_VAR

VAR_OUTPUT
    ///<Description>Q1: включить 10F ввод 1</Description>
    xQ1 : BOOL;

    ///<Description>Q2: выключить 10F ввод 1</Description>
    xQ2 : BOOL;

    ///<Description>Q3: включить 20F ввод 2</Description>
    xQ3 : BOOL;

    ///<Description>Q4: выключить 20F ввод 2</Description>
    xQ4 : BOOL;

    ///<Description>Q5: включить 30F секционный автомат</Description>
    xQ5 : BOOL;

    ///<Description>Q6: выключить 30F секционный автомат</Description>
    xQ6 : BOOL;

    ///<Description>Текущая подтвержденная схема: 0 переход/нет, 10 нормальная, 11 ввод 1 через секцию, 12 ввод 2 через секцию, 99 параллель</Description>
    udiCurrentScheme : UDINT;

    ///<Description>Целевая схема по мгновенному состоянию напряжений до задержки</Description>
    udiRawTargetScheme : UDINT;

    ///<Description>Целевая схема: 0 все отключить, 10 нормальная, 11 ввод 1 через секцию, 12 ввод 2 через секцию</Description>
    udiTargetScheme : UDINT;

    ///<Description>Кандидат целевой схемы, ожидающий окончания задержки</Description>
    udiPendingTargetScheme : UDINT;

    ///<Description>Счетчик задержки подтверждения целевой схемы, секунд</Description>
    udiDelayCounterSec : UDINT;

    ///<Description>Состояние автомата: 0 ожидание, 11/12/13 отключение 10F/20F/30F, 21/22/23 включение 10F/20F/30F, 90 ручной/авария</Description>
    udiState : UDINT;

    ///<Description>TRUE = идет задержка перед принятием новой целевой схемы</Description>
    xTargetDelayActive : BOOL;

    ///<Description>Schotchik zaderzhki pered vklyucheniem 30F, sekund/ciklov vyzova bloka</Description>
    udiSectionCloseDelayCounterSec : UDINT;

    ///<Description>TRUE = idet zaderzhka pered vklyucheniem 30F sekcionnogo avtomata</Description>
    xSectionCloseDelayActive : BOOL;

    ///<Description>АВР находится в автоматическом режиме</Description>
    xAutoMode : BOOL;

    ///<Description>АВР находится в ручном режиме или аварийном режиме</Description>
    xManualMode : BOOL;

    ///<Description>Подтверждена нормальная схема: 10F включен, 20F включен, 30F выключен</Description>
    xNormalScheme : BOOL;

    ///<Description>Подтверждена схема: ввод 1 питает обе секции через 30F</Description>
    xFromInput1Scheme : BOOL;

    ///<Description>Подтверждена схема: ввод 2 питает обе секции через 30F</Description>
    xFromInput2Scheme : BOOL;

    ///<Description>Секция шин 1 имеет питание по подтвержденной схеме</Description>
    xBus1Powered : BOOL;

    ///<Description>Секция шин 2 имеет питание по подтвержденной схеме</Description>
    xBus2Powered : BOOL;

    ///<Description>Общая авария АВР</Description>
    xAlarm : BOOL;

    ///<Description>Авария 10F, 20F или 30F</Description>
    xAlarmFault : BOOL;

    ///<Description>Запрещенная параллель: 10F, 20F и 30F одновременно включены</Description>
    xAlarmParallel : BOOL;

    ///<Description>Неопределенное состояние допконтактов</Description>
    xAlarmUndefined : BOOL;

    ///<Description>Неопределенное состояние допконтактов 10F</Description>
    xQF1Undefined : BOOL;

    ///<Description>Неопределенное состояние допконтактов 20F</Description>
    xQF2Undefined : BOOL;

    ///<Description>Неопределенное состояние допконтактов 30F</Description>
    xQFSUndefined : BOOL;

    ///<Description>Нет доступного ввода</Description>
    xNoSource : BOOL;
END_VAR

VAR
    xS1Ready : BOOL;
    xS2Ready : BOOL;

    xAnyFault : BOOL;
    xEmergencyMode : BOOL;

    xQF1Invalid : BOOL;
    xQF2Invalid : BOOL;
    xQFSInvalid : BOOL;

    xQF1NoPosition : BOOL;
    xQF2NoPosition : BOOL;
    xQFSNoPosition : BOOL;

    xQF1Commanded : BOOL;
    xQF2Commanded : BOOL;
    xQFSCommanded : BOOL;

    xTargetInitialized : BOOL;
    udiStableTargetScheme : UDINT;

    xSectionCloseRequest : BOOL;
    xSectionCloseDelayDone : BOOL;
END_VAR

xAnyFault := xQF1Fault OR xQF2Fault OR xQFSFault;

xQF1Invalid := xQF1On AND xQF1Off;
xQF2Invalid := xQF2On AND xQF2Off;
xQFSInvalid := xQFSOn AND xQFSOff;

xQF1NoPosition := (NOT xQF1On) AND (NOT xQF1Off);
xQF2NoPosition := (NOT xQF2On) AND (NOT xQF2Off);
xQFSNoPosition := (NOT xQFSOn) AND (NOT xQFSOff);

xQF1Commanded := (udiState = 11) OR (udiState = 21);
xQF2Commanded := (udiState = 12) OR (udiState = 22);
xQFSCommanded := (udiState = 13) OR (udiState = 23);

// Во время команды допускается промежуточное положение допконтактов:
// оба контакта FALSE, пока мотор-привод идет. Вне команды это аварийная неопределенность.
xQF1Undefined := xQF1Invalid OR (xQF1NoPosition AND NOT xQF1Commanded);
xQF2Undefined := xQF2Invalid OR (xQF2NoPosition AND NOT xQF2Commanded);
xQFSUndefined := xQFSInvalid OR (xQFSNoPosition AND NOT xQFSCommanded);
xAlarmUndefined := xQF1Undefined OR xQF2Undefined OR xQFSUndefined;

xS1Ready := xU1Ok AND NOT xQF1Fault;
xS2Ready := xU2Ok AND NOT xQF2Fault;

xNormalScheme := xQF1On AND xQF2On AND xQFSOff;
xFromInput1Scheme := xQF1On AND xQF2Off AND xQFSOn;
xFromInput2Scheme := xQF1Off AND xQF2On AND xQFSOn;
xAlarmParallel := xQF1On AND xQF2On AND xQFSOn;

udiCurrentScheme := 0;
IF xAlarmParallel THEN
    udiCurrentScheme := 99;
ELSIF xNormalScheme THEN
    udiCurrentScheme := 10;
ELSIF xFromInput1Scheme THEN
    udiCurrentScheme := 11;
ELSIF xFromInput2Scheme THEN
    udiCurrentScheme := 12;
END_IF;

xBus1Powered := (xQF1On AND xS1Ready) OR (xQFSOn AND xQF2On AND xS2Ready);
xBus2Powered := (xQF2On AND xS2Ready) OR (xQFSOn AND xQF1On AND xS1Ready);

udiRawTargetScheme := 0;
IF xS1Ready AND xS2Ready THEN
    udiRawTargetScheme := 10;

    IF NOT xAutoReturn THEN
        IF (udiCurrentScheme = 11) AND xS1Ready THEN
            udiRawTargetScheme := 11;
        ELSIF (udiCurrentScheme = 12) AND xS2Ready THEN
            udiRawTargetScheme := 12;
        END_IF;
    END_IF;
ELSIF xS1Ready THEN
    udiRawTargetScheme := 11;
ELSIF xS2Ready THEN
    udiRawTargetScheme := 12;
END_IF;

IF NOT xTargetInitialized THEN
    udiStableTargetScheme := udiRawTargetScheme;
    udiPendingTargetScheme := udiRawTargetScheme;
    udiDelayCounterSec := 0;
    xTargetInitialized := TRUE;
ELSIF udiInputDelaySec = 0 THEN
    udiStableTargetScheme := udiRawTargetScheme;
    udiPendingTargetScheme := udiRawTargetScheme;
    udiDelayCounterSec := 0;
ELSIF udiRawTargetScheme = udiStableTargetScheme THEN
    udiPendingTargetScheme := udiRawTargetScheme;
    udiDelayCounterSec := 0;
ELSE
    IF udiRawTargetScheme <> udiPendingTargetScheme THEN
        udiPendingTargetScheme := udiRawTargetScheme;
        udiDelayCounterSec := 0;
    ELSIF udiDelayCounterSec < udiInputDelaySec THEN
        udiDelayCounterSec := udiDelayCounterSec + 1;
    END_IF;

    IF udiDelayCounterSec >= udiInputDelaySec THEN
        udiStableTargetScheme := udiPendingTargetScheme;
        udiDelayCounterSec := 0;
    END_IF;
END_IF;

udiTargetScheme := udiStableTargetScheme;
xTargetDelayActive := udiRawTargetScheme <> udiTargetScheme;

xNoSource := udiTargetScheme = 0;

xEmergencyMode := xAnyFault OR xAlarmParallel OR xAlarmUndefined;
xManualMode := xManualSelector OR xEmergencyMode;
xAutoMode := (NOT xManualSelector) AND (NOT xEmergencyMode);

xSectionCloseRequest := xAutoMode AND (udiState <> 23) AND (NOT xQFSOn) AND
    (((udiTargetScheme = 11) AND xS1Ready AND xQF1On AND xQF2Off) OR
     ((udiTargetScheme = 12) AND xS2Ready AND xQF2On AND xQF1Off));

IF (NOT xSectionCloseRequest) OR (udiSectionCloseDelaySec = 0) THEN
    udiSectionCloseDelayCounterSec := 0;
ELSIF udiSectionCloseDelayCounterSec < udiSectionCloseDelaySec THEN
    udiSectionCloseDelayCounterSec := udiSectionCloseDelayCounterSec + 1;
END_IF;

xSectionCloseDelayDone := (udiSectionCloseDelaySec = 0) OR (udiSectionCloseDelayCounterSec >= udiSectionCloseDelaySec);
xSectionCloseDelayActive := xSectionCloseRequest AND (NOT xSectionCloseDelayDone);

IF xAutoMode THEN
    CASE udiState OF
        0, 90:
            IF udiTargetScheme = 0 THEN
                IF xQFSOn THEN
                    udiState := 13;
                ELSIF xQF1On THEN
                    udiState := 11;
                ELSIF xQF2On THEN
                    udiState := 12;
                ELSE
                    udiState := 0;
                END_IF;

            ELSIF udiTargetScheme = 10 THEN
                IF xQFSOn THEN
                    udiState := 13;
                ELSIF NOT xQF1On THEN
                    udiState := 21;
                ELSIF NOT xQF2On THEN
                    udiState := 22;
                ELSE
                    udiState := 0;
                END_IF;

            ELSIF udiTargetScheme = 11 THEN
                IF xQF2On THEN
                    udiState := 12;
                ELSIF (NOT xQF1On) AND xQFSOn THEN
                    udiState := 13;
                ELSIF NOT xQF1On THEN
                    udiState := 21;
                ELSIF NOT xQFSOn THEN
                    IF xSectionCloseDelayDone THEN
                        udiState := 23;
                    ELSE
                        udiState := 0;
                    END_IF;
                ELSE
                    udiState := 0;
                END_IF;

            ELSIF udiTargetScheme = 12 THEN
                IF xQF1On THEN
                    udiState := 11;
                ELSIF (NOT xQF2On) AND xQFSOn THEN
                    udiState := 13;
                ELSIF NOT xQF2On THEN
                    udiState := 22;
                ELSIF NOT xQFSOn THEN
                    IF xSectionCloseDelayDone THEN
                        udiState := 23;
                    ELSE
                        udiState := 0;
                    END_IF;
                ELSE
                    udiState := 0;
                END_IF;
            END_IF;

        11:
            IF xQF1Off THEN
                udiState := 0;
            END_IF;

        12:
            IF xQF2Off THEN
                udiState := 0;
            END_IF;

        13:
            IF xQFSOff THEN
                udiState := 0;
            END_IF;

        21:
            IF xQF1On THEN
                udiState := 0;
            ELSIF NOT xS1Ready THEN
                udiState := 0;
            END_IF;

        22:
            IF xQF2On THEN
                udiState := 0;
            ELSIF NOT xS2Ready THEN
                udiState := 0;
            END_IF;

        23:
            IF xQFSOn THEN
                udiState := 0;
            ELSIF (udiTargetScheme = 0) OR (udiTargetScheme = 10) THEN
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
    xQ1 := (udiState = 21) AND xS1Ready AND (NOT xQF1On) AND (NOT xAlarm) AND
           (((udiTargetScheme = 10) AND xQFSOff) OR
            ((udiTargetScheme = 11) AND xQF2Off AND xQFSOff));

    xQ2 := (udiState = 11) AND (NOT xQF1Off) AND (NOT xAlarm);

    xQ3 := (udiState = 22) AND xS2Ready AND (NOT xQF2On) AND (NOT xAlarm) AND
           (((udiTargetScheme = 10) AND xQFSOff) OR
            ((udiTargetScheme = 12) AND xQF1Off AND xQFSOff));

    xQ4 := (udiState = 12) AND (NOT xQF2Off) AND (NOT xAlarm);

    xQ5 := (udiState = 23) AND (NOT xQFSOn) AND (NOT xAlarm) AND
           (((udiTargetScheme = 11) AND xS1Ready AND xQF1On AND xQF2Off) OR
            ((udiTargetScheme = 12) AND xS2Ready AND xQF2On AND xQF1Off));

    xQ6 := (udiState = 13) AND (NOT xQFSOff) AND (NOT xAlarm);
END_IF;

// Запрещенная параллель для схемы с секционником:
// 10F, 20F и 30F включены одновременно. В этом случае включение запрещено,
// разрешены только команды отключения уже включенных аппаратов.
IF xAlarmParallel THEN
    xQ1 := FALSE;
    xQ3 := FALSE;
    xQ5 := FALSE;

    xQ2 := xQF1On;
    xQ4 := xQF2On;
    xQ6 := xQFSOn;
END_IF;

END_FUNCTION_BLOCK
