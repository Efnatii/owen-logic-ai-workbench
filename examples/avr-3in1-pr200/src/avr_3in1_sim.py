from dataclasses import dataclass, fields


@dataclass
class AVRInputs:
    manual_selector: bool = False
    auto_return: bool = True
    input_delay_sec: int = 0

    u1_ok: bool = False
    u2_ok: bool = False
    u3_ok: bool = False

    qf1_on: bool = False
    qf1_off: bool = True
    qf1_fault: bool = False

    qf2_on: bool = False
    qf2_off: bool = True
    qf2_fault: bool = False

    qf3_on: bool = False
    qf3_off: bool = True
    qf3_fault: bool = False


@dataclass
class AVROutputs:
    xQ1: bool = False
    xQ2: bool = False
    xQ3: bool = False
    xQ4: bool = False
    xQ5: bool = False
    xQ6: bool = False

    udiActive: int = 0
    udiRawTarget: int = 0
    udiTarget: int = 0
    udiPendingTarget: int = 0
    udiDelayCounterSec: int = 0
    udiState: int = 0
    xTargetDelayActive: bool = False

    xAutoMode: bool = True
    xManualMode: bool = False

    xAlarm: bool = False
    xAlarmFault: bool = False
    xAlarmParallel: bool = False
    xAlarmUndefined: bool = False
    xQF1Undefined: bool = False
    xQF2Undefined: bool = False
    xQF3Undefined: bool = False
    xNoSource: bool = False


class AVR3In1:
    def __init__(self) -> None:
        self.state = 0
        self.target_initialized = False
        self.stable_target = 0
        self.pending_target = 0
        self.delay_counter_sec = 0

    def step(self, i: AVRInputs) -> AVROutputs:
        qf1_invalid = i.qf1_on and i.qf1_off
        qf2_invalid = i.qf2_on and i.qf2_off
        qf3_invalid = i.qf3_on and i.qf3_off

        qf1_no_position = not i.qf1_on and not i.qf1_off
        qf2_no_position = not i.qf2_on and not i.qf2_off
        qf3_no_position = not i.qf3_on and not i.qf3_off

        qf1_commanded = self.state in {11, 31}
        qf2_commanded = self.state in {12, 32}
        qf3_commanded = self.state in {13, 33}

        qf1_undefined = qf1_invalid or (qf1_no_position and not qf1_commanded)
        qf2_undefined = qf2_invalid or (qf2_no_position and not qf2_commanded)
        qf3_undefined = qf3_invalid or (qf3_no_position and not qf3_commanded)
        alarm_undefined = qf1_undefined or qf2_undefined or qf3_undefined

        any_fault = i.qf1_fault or i.qf2_fault or i.qf3_fault
        s1_ready = i.u1_ok and not i.qf1_fault
        s2_ready = i.u2_ok and not i.qf2_fault
        s3_ready = i.u3_ok and not i.qf3_fault

        on_count = int(i.qf1_on) + int(i.qf2_on) + int(i.qf3_on)
        alarm_parallel = on_count > 1
        all_off_confirmed = i.qf1_off and i.qf2_off and i.qf3_off and not alarm_undefined

        active = 0
        if on_count == 1:
            if i.qf1_on:
                active = 1
            if i.qf2_on:
                active = 2
            if i.qf3_on:
                active = 3

        raw_target = 0
        if s1_ready:
            raw_target = 1
        elif s2_ready:
            raw_target = 2
        elif s3_ready:
            raw_target = 3

        active_ready = (
            (active == 1 and s1_ready)
            or (active == 2 and s2_ready)
            or (active == 3 and s3_ready)
        )
        if not i.auto_return and active_ready:
            raw_target = active

        delay_sec = max(0, int(i.input_delay_sec))
        if not self.target_initialized:
            self.stable_target = raw_target
            self.pending_target = raw_target
            self.delay_counter_sec = 0
            self.target_initialized = True
        elif delay_sec == 0:
            self.stable_target = raw_target
            self.pending_target = raw_target
            self.delay_counter_sec = 0
        elif raw_target == self.stable_target:
            self.pending_target = raw_target
            self.delay_counter_sec = 0
        else:
            if raw_target != self.pending_target:
                self.pending_target = raw_target
                self.delay_counter_sec = 0
            elif self.delay_counter_sec < delay_sec:
                self.delay_counter_sec += 1

            if self.delay_counter_sec >= delay_sec:
                self.stable_target = self.pending_target
                self.delay_counter_sec = 0

        target = self.stable_target
        target_delay_active = raw_target != target

        emergency_mode = any_fault or alarm_parallel or alarm_undefined
        auto_mode = not i.manual_selector and not emergency_mode

        if auto_mode:
            if self.state == 0:
                if target == 0:
                    if active == 1:
                        self.state = 11
                    elif active == 2:
                        self.state = 12
                    elif active == 3:
                        self.state = 13
                elif active == target:
                    self.state = 0
                elif active == 1:
                    self.state = 11
                elif active == 2:
                    self.state = 12
                elif active == 3:
                    self.state = 13
                elif all_off_confirmed:
                    self.state = 20
            elif self.state == 11:
                if i.qf1_off:
                    self.state = 20
            elif self.state == 12:
                if i.qf2_off:
                    self.state = 20
            elif self.state == 13:
                if i.qf3_off:
                    self.state = 20
            elif self.state == 20:
                if target == 0:
                    self.state = 0
                elif not all_off_confirmed:
                    self.state = 0
                elif target == 1:
                    self.state = 31
                elif target == 2:
                    self.state = 32
                elif target == 3:
                    self.state = 33
                else:
                    self.state = 0
            elif self.state == 31:
                if i.qf1_on:
                    self.state = 0
                elif not s1_ready:
                    self.state = 0
            elif self.state == 32:
                if i.qf2_on:
                    self.state = 0
                elif not s2_ready:
                    self.state = 0
            elif self.state == 33:
                if i.qf3_on:
                    self.state = 0
                elif not s3_ready:
                    self.state = 0
            else:
                self.state = 0
        else:
            self.state = 90

        emergency_mode = any_fault or alarm_parallel or alarm_undefined
        auto_mode = not i.manual_selector and not emergency_mode
        manual_mode = i.manual_selector or emergency_mode

        alarm_fault = any_fault
        alarm = alarm_fault or alarm_parallel or alarm_undefined

        q1 = q2 = q3 = q4 = q5 = q6 = False
        if auto_mode:
            q1 = self.state == 31 and s1_ready and i.qf2_off and i.qf3_off and not alarm
            q2 = self.state == 11 and not i.qf1_off and not alarm
            q3 = self.state == 32 and s2_ready and i.qf1_off and i.qf3_off and not alarm
            q4 = self.state == 12 and not i.qf2_off and not alarm
            q5 = self.state == 33 and s3_ready and i.qf1_off and i.qf2_off and not alarm
            q6 = self.state == 13 and not i.qf3_off and not alarm

        if alarm_parallel:
            q1 = q3 = q5 = False
            q2 = i.qf1_on
            q4 = i.qf2_on
            q6 = i.qf3_on

        return AVROutputs(
            xQ1=q1,
            xQ2=q2,
            xQ3=q3,
            xQ4=q4,
            xQ5=q5,
            xQ6=q6,
            udiActive=active,
            udiRawTarget=raw_target,
            udiTarget=target,
            udiPendingTarget=self.pending_target,
            udiDelayCounterSec=self.delay_counter_sec,
            udiState=self.state,
            xTargetDelayActive=target_delay_active,
            xAutoMode=auto_mode,
            xManualMode=manual_mode,
            xAlarm=alarm,
            xAlarmFault=alarm_fault,
            xAlarmParallel=alarm_parallel,
            xAlarmUndefined=alarm_undefined,
            xQF1Undefined=qf1_undefined,
            xQF2Undefined=qf2_undefined,
            xQF3Undefined=qf3_undefined,
            xNoSource=target == 0,
        )


class MotorPlant:
    def __init__(self, delay_cycles: int = 2) -> None:
        self.on = [False, False, False]
        self.delay_cycles = delay_cycles
        self.pending = [None, None, None]

    def set_on(self, index: int) -> None:
        self.on[index - 1] = True

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
        for n, prefix in enumerate(("qf1", "qf2", "qf3")):
            if self.pending[n] is None:
                data[f"{prefix}_on"] = self.on[n]
                data[f"{prefix}_off"] = not self.on[n]
            else:
                data[f"{prefix}_on"] = False
                data[f"{prefix}_off"] = False
        return AVRInputs(**data)
