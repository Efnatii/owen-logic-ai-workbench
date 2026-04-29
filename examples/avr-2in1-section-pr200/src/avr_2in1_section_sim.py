from dataclasses import dataclass, fields


@dataclass
class AVRInputs:
    manual_selector: bool = False
    auto_return: bool = True
    input_delay_sec: int = 0
    section_close_delay_sec: int = 0

    u1_ok: bool = False
    u2_ok: bool = False

    qf1_on: bool = False
    qf1_off: bool = True
    qf1_fault: bool = False

    qf2_on: bool = False
    qf2_off: bool = True
    qf2_fault: bool = False

    qfs_on: bool = False
    qfs_off: bool = True
    qfs_fault: bool = False


@dataclass
class AVROutputs:
    xQ1: bool = False
    xQ2: bool = False
    xQ3: bool = False
    xQ4: bool = False
    xQ5: bool = False
    xQ6: bool = False

    udiCurrentScheme: int = 0
    udiRawTargetScheme: int = 0
    udiTargetScheme: int = 0
    udiPendingTargetScheme: int = 0
    udiDelayCounterSec: int = 0
    udiState: int = 0
    xTargetDelayActive: bool = False
    udiSectionCloseDelayCounterSec: int = 0
    xSectionCloseDelayActive: bool = False

    xAutoMode: bool = True
    xManualMode: bool = False

    xNormalScheme: bool = False
    xFromInput1Scheme: bool = False
    xFromInput2Scheme: bool = False
    xBus1Powered: bool = False
    xBus2Powered: bool = False

    xAlarm: bool = False
    xAlarmFault: bool = False
    xAlarmParallel: bool = False
    xAlarmUndefined: bool = False
    xQF1Undefined: bool = False
    xQF2Undefined: bool = False
    xQFSUndefined: bool = False
    xNoSource: bool = False


class AVR2In1Section:
    def __init__(self) -> None:
        self.state = 0
        self.target_initialized = False
        self.stable_target_scheme = 0
        self.pending_target_scheme = 0
        self.delay_counter_sec = 0
        self.section_close_delay_counter_sec = 0

    def step(self, i: AVRInputs) -> AVROutputs:
        any_fault = i.qf1_fault or i.qf2_fault or i.qfs_fault

        qf1_invalid = i.qf1_on and i.qf1_off
        qf2_invalid = i.qf2_on and i.qf2_off
        qfs_invalid = i.qfs_on and i.qfs_off

        qf1_no_position = not i.qf1_on and not i.qf1_off
        qf2_no_position = not i.qf2_on and not i.qf2_off
        qfs_no_position = not i.qfs_on and not i.qfs_off

        qf1_commanded = self.state in {11, 21}
        qf2_commanded = self.state in {12, 22}
        qfs_commanded = self.state in {13, 23}

        qf1_undefined = qf1_invalid or (qf1_no_position and not qf1_commanded)
        qf2_undefined = qf2_invalid or (qf2_no_position and not qf2_commanded)
        qfs_undefined = qfs_invalid or (qfs_no_position and not qfs_commanded)
        alarm_undefined = qf1_undefined or qf2_undefined or qfs_undefined

        s1_ready = i.u1_ok and not i.qf1_fault
        s2_ready = i.u2_ok and not i.qf2_fault

        normal_scheme = i.qf1_on and i.qf2_on and i.qfs_off
        from_input1_scheme = i.qf1_on and i.qf2_off and i.qfs_on
        from_input2_scheme = i.qf1_off and i.qf2_on and i.qfs_on
        alarm_parallel = i.qf1_on and i.qf2_on and i.qfs_on

        current_scheme = 0
        if alarm_parallel:
            current_scheme = 99
        elif normal_scheme:
            current_scheme = 10
        elif from_input1_scheme:
            current_scheme = 11
        elif from_input2_scheme:
            current_scheme = 12

        bus1_powered = (i.qf1_on and s1_ready) or (i.qfs_on and i.qf2_on and s2_ready)
        bus2_powered = (i.qf2_on and s2_ready) or (i.qfs_on and i.qf1_on and s1_ready)

        raw_target_scheme = 0
        if s1_ready and s2_ready:
            raw_target_scheme = 10
            if not i.auto_return:
                if current_scheme == 11 and s1_ready:
                    raw_target_scheme = 11
                elif current_scheme == 12 and s2_ready:
                    raw_target_scheme = 12
        elif s1_ready:
            raw_target_scheme = 11
        elif s2_ready:
            raw_target_scheme = 12

        input_delay_sec = max(0, int(i.input_delay_sec))
        section_close_delay_sec = max(0, int(i.section_close_delay_sec))
        if not self.target_initialized:
            self.stable_target_scheme = raw_target_scheme
            self.pending_target_scheme = raw_target_scheme
            self.delay_counter_sec = 0
            self.target_initialized = True
        elif input_delay_sec == 0:
            self.stable_target_scheme = raw_target_scheme
            self.pending_target_scheme = raw_target_scheme
            self.delay_counter_sec = 0
        elif raw_target_scheme == self.stable_target_scheme:
            self.pending_target_scheme = raw_target_scheme
            self.delay_counter_sec = 0
        else:
            if raw_target_scheme != self.pending_target_scheme:
                self.pending_target_scheme = raw_target_scheme
                self.delay_counter_sec = 0
            elif self.delay_counter_sec < input_delay_sec:
                self.delay_counter_sec += 1

            if self.delay_counter_sec >= input_delay_sec:
                self.stable_target_scheme = self.pending_target_scheme
                self.delay_counter_sec = 0

        target_scheme = self.stable_target_scheme
        target_delay_active = raw_target_scheme != target_scheme

        emergency_mode = any_fault or alarm_parallel or alarm_undefined
        auto_mode = not i.manual_selector and not emergency_mode

        section_close_request = (
            auto_mode
            and self.state != 23
            and not i.qfs_on
            and (
                (target_scheme == 11 and s1_ready and i.qf1_on and i.qf2_off)
                or (target_scheme == 12 and s2_ready and i.qf2_on and i.qf1_off)
            )
        )

        if not section_close_request or section_close_delay_sec == 0:
            self.section_close_delay_counter_sec = 0
        elif self.section_close_delay_counter_sec < section_close_delay_sec:
            self.section_close_delay_counter_sec += 1

        section_close_delay_done = (
            section_close_delay_sec == 0
            or self.section_close_delay_counter_sec >= section_close_delay_sec
        )
        section_close_delay_active = section_close_request and not section_close_delay_done

        if auto_mode:
            if self.state in {0, 90}:
                if target_scheme == 0:
                    if i.qfs_on:
                        self.state = 13
                    elif i.qf1_on:
                        self.state = 11
                    elif i.qf2_on:
                        self.state = 12
                    else:
                        self.state = 0
                elif target_scheme == 10:
                    if i.qfs_on:
                        self.state = 13
                    elif not i.qf1_on:
                        self.state = 21
                    elif not i.qf2_on:
                        self.state = 22
                    else:
                        self.state = 0
                elif target_scheme == 11:
                    if i.qf2_on:
                        self.state = 12
                    elif not i.qf1_on and i.qfs_on:
                        self.state = 13
                    elif not i.qf1_on:
                        self.state = 21
                    elif not i.qfs_on:
                        if section_close_delay_done:
                            self.state = 23
                        else:
                            self.state = 0
                    else:
                        self.state = 0
                elif target_scheme == 12:
                    if i.qf1_on:
                        self.state = 11
                    elif not i.qf2_on and i.qfs_on:
                        self.state = 13
                    elif not i.qf2_on:
                        self.state = 22
                    elif not i.qfs_on:
                        if section_close_delay_done:
                            self.state = 23
                        else:
                            self.state = 0
                    else:
                        self.state = 0
            elif self.state == 11:
                if i.qf1_off:
                    self.state = 0
            elif self.state == 12:
                if i.qf2_off:
                    self.state = 0
            elif self.state == 13:
                if i.qfs_off:
                    self.state = 0
            elif self.state == 21:
                if i.qf1_on:
                    self.state = 0
                elif not s1_ready:
                    self.state = 0
            elif self.state == 22:
                if i.qf2_on:
                    self.state = 0
                elif not s2_ready:
                    self.state = 0
            elif self.state == 23:
                if i.qfs_on:
                    self.state = 0
                elif target_scheme in {0, 10}:
                    self.state = 0
            else:
                self.state = 0
        else:
            self.state = 90

        alarm_fault = any_fault
        alarm = alarm_fault or alarm_parallel or alarm_undefined
        auto_mode = not i.manual_selector and not emergency_mode
        manual_mode = i.manual_selector or emergency_mode

        q1 = q2 = q3 = q4 = q5 = q6 = False
        if auto_mode:
            q1 = (
                self.state == 21
                and s1_ready
                and not i.qf1_on
                and not alarm
                and (
                    (target_scheme == 10 and i.qfs_off)
                    or (target_scheme == 11 and i.qf2_off and i.qfs_off)
                )
            )
            q2 = self.state == 11 and not i.qf1_off and not alarm
            q3 = (
                self.state == 22
                and s2_ready
                and not i.qf2_on
                and not alarm
                and (
                    (target_scheme == 10 and i.qfs_off)
                    or (target_scheme == 12 and i.qf1_off and i.qfs_off)
                )
            )
            q4 = self.state == 12 and not i.qf2_off and not alarm
            q5 = (
                self.state == 23
                and not i.qfs_on
                and not alarm
                and (
                    (target_scheme == 11 and s1_ready and i.qf1_on and i.qf2_off)
                    or (target_scheme == 12 and s2_ready and i.qf2_on and i.qf1_off)
                )
            )
            q6 = self.state == 13 and not i.qfs_off and not alarm

        if alarm_parallel:
            q1 = q3 = q5 = False
            q2 = i.qf1_on
            q4 = i.qf2_on
            q6 = i.qfs_on

        return AVROutputs(
            xQ1=q1,
            xQ2=q2,
            xQ3=q3,
            xQ4=q4,
            xQ5=q5,
            xQ6=q6,
            udiCurrentScheme=current_scheme,
            udiRawTargetScheme=raw_target_scheme,
            udiTargetScheme=target_scheme,
            udiPendingTargetScheme=self.pending_target_scheme,
            udiDelayCounterSec=self.delay_counter_sec,
            udiState=self.state,
            xTargetDelayActive=target_delay_active,
            udiSectionCloseDelayCounterSec=self.section_close_delay_counter_sec,
            xSectionCloseDelayActive=section_close_delay_active,
            xAutoMode=auto_mode,
            xManualMode=manual_mode,
            xNormalScheme=normal_scheme,
            xFromInput1Scheme=from_input1_scheme,
            xFromInput2Scheme=from_input2_scheme,
            xBus1Powered=bus1_powered,
            xBus2Powered=bus2_powered,
            xAlarm=alarm,
            xAlarmFault=alarm_fault,
            xAlarmParallel=alarm_parallel,
            xAlarmUndefined=alarm_undefined,
            xQF1Undefined=qf1_undefined,
            xQF2Undefined=qf2_undefined,
            xQFSUndefined=qfs_undefined,
            xNoSource=target_scheme == 0,
        )


class SectionPlant:
    def __init__(self, delay_cycles: int = 2) -> None:
        self.on = [False, False, False]
        self.delay_cycles = delay_cycles
        self.pending = [None, None, None]

    def set_scheme(self, scheme: int) -> None:
        if scheme == 10:
            self.on = [True, True, False]
        elif scheme == 11:
            self.on = [True, False, True]
        elif scheme == 12:
            self.on = [False, True, True]
        elif scheme == 0:
            self.on = [False, False, False]
        else:
            raise ValueError(f"unknown scheme {scheme}")
        self.pending = [None, None, None]

    def apply(self, o: AVROutputs) -> None:
        commands = [
            (o.xQ1, o.xQ2),
            (o.xQ3, o.xQ4),
            (o.xQ5, o.xQ6),
        ]
        for n, (cmd_on, cmd_off) in enumerate(commands):
            if cmd_on:
                if self.pending[n] is None or self.pending[n][0] != "on":
                    self.pending[n] = ["on", self.delay_cycles]
            elif cmd_off:
                if self.pending[n] is None or self.pending[n][0] != "off":
                    self.pending[n] = ["off", self.delay_cycles]

        for n, command in enumerate(self.pending):
            if command is None:
                continue
            command[1] -= 1
            if command[1] <= 0:
                self.on[n] = command[0] == "on"
                self.pending[n] = None

    def to_inputs(self, base: AVRInputs) -> AVRInputs:
        data = {field.name: getattr(base, field.name) for field in fields(AVRInputs)}
        for n, prefix in enumerate(("qf1", "qf2", "qfs")):
            if self.pending[n] is None:
                data[f"{prefix}_on"] = self.on[n]
                data[f"{prefix}_off"] = not self.on[n]
            else:
                data[f"{prefix}_on"] = False
                data[f"{prefix}_off"] = False
        return AVRInputs(**data)
