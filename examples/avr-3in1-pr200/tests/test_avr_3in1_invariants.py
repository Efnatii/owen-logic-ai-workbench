import itertools
import unittest
from pathlib import Path

from avr_3in1_sim import AVR3In1, AVRInputs


INPUT_FIELDS = (
    "manual_selector",
    "auto_return",
    "u1_ok",
    "u2_ok",
    "u3_ok",
    "qf1_on",
    "qf1_off",
    "qf1_fault",
    "qf2_on",
    "qf2_off",
    "qf2_fault",
    "qf3_on",
    "qf3_off",
    "qf3_fault",
)

STATES = (0, 11, 12, 13, 20, 31, 32, 33, 90, 777)
SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def all_inputs():
    for bits in itertools.product((False, True), repeat=len(INPUT_FIELDS)):
        yield AVRInputs(**dict(zip(INPUT_FIELDS, bits)))


def run_once(inputs, state=0):
    avr = AVR3In1()
    avr.state = state
    return avr.step(inputs)


def active_input(inputs):
    on_count = int(inputs.qf1_on) + int(inputs.qf2_on) + int(inputs.qf3_on)
    if on_count != 1:
        return 0
    if inputs.qf1_on:
        return 1
    if inputs.qf2_on:
        return 2
    return 3


def target_input(inputs):
    target = 0
    if inputs.u1_ok and not inputs.qf1_fault:
        target = 1
    elif inputs.u2_ok and not inputs.qf2_fault:
        target = 2
    elif inputs.u3_ok and not inputs.qf3_fault:
        target = 3

    active = active_input(inputs)
    active_ready = (
        (active == 1 and inputs.u1_ok and not inputs.qf1_fault)
        or (active == 2 and inputs.u2_ok and not inputs.qf2_fault)
        or (active == 3 and inputs.u3_ok and not inputs.qf3_fault)
    )
    if not inputs.auto_return and active_ready:
        target = active
    return target


def undefined_flags(inputs, prior_state):
    qf1_invalid = inputs.qf1_on and inputs.qf1_off
    qf2_invalid = inputs.qf2_on and inputs.qf2_off
    qf3_invalid = inputs.qf3_on and inputs.qf3_off

    qf1_no_pos = not inputs.qf1_on and not inputs.qf1_off
    qf2_no_pos = not inputs.qf2_on and not inputs.qf2_off
    qf3_no_pos = not inputs.qf3_on and not inputs.qf3_off

    qf1_undefined = qf1_invalid or (qf1_no_pos and prior_state not in {11, 31})
    qf2_undefined = qf2_invalid or (qf2_no_pos and prior_state not in {12, 32})
    qf3_undefined = qf3_invalid or (qf3_no_pos and prior_state not in {13, 33})
    return qf1_undefined, qf2_undefined, qf3_undefined


class AVRInvariantTests(unittest.TestCase):
    def test_33_exhaustive_outputs_never_have_same_breaker_on_and_off_commands(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertFalse(outputs.xQ1 and outputs.xQ2, (state, inputs, outputs))
                self.assertFalse(outputs.xQ3 and outputs.xQ4, (state, inputs, outputs))
                self.assertFalse(outputs.xQ5 and outputs.xQ6, (state, inputs, outputs))

    def test_34_exhaustive_at_most_one_close_command_exists(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                close_count = int(outputs.xQ1) + int(outputs.xQ3) + int(outputs.xQ5)
                self.assertLessEqual(close_count, 1, (state, inputs, outputs))

    def test_35_exhaustive_close_commands_require_auto_mode_and_no_alarm(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                if outputs.xQ1 or outputs.xQ3 or outputs.xQ5:
                    self.assertTrue(outputs.xAutoMode, (state, inputs, outputs))
                    self.assertFalse(outputs.xManualMode, (state, inputs, outputs))
                    self.assertFalse(outputs.xAlarm, (state, inputs, outputs))

    def test_36_exhaustive_close_40f_requires_input_1_ready_and_other_breakers_off(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                if outputs.xQ1:
                    self.assertTrue(inputs.u1_ok and not inputs.qf1_fault, (state, inputs, outputs))
                    self.assertTrue(inputs.qf2_off and inputs.qf3_off, (state, inputs, outputs))
                    self.assertEqual(outputs.udiState, 31, (state, inputs, outputs))

    def test_37_exhaustive_close_50f_requires_input_2_ready_and_other_breakers_off(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                if outputs.xQ3:
                    self.assertTrue(inputs.u2_ok and not inputs.qf2_fault, (state, inputs, outputs))
                    self.assertTrue(inputs.qf1_off and inputs.qf3_off, (state, inputs, outputs))
                    self.assertEqual(outputs.udiState, 32, (state, inputs, outputs))

    def test_38_exhaustive_close_60f_requires_input_3_ready_and_other_breakers_off(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                if outputs.xQ5:
                    self.assertTrue(inputs.u3_ok and not inputs.qf3_fault, (state, inputs, outputs))
                    self.assertTrue(inputs.qf1_off and inputs.qf2_off, (state, inputs, outputs))
                    self.assertEqual(outputs.udiState, 33, (state, inputs, outputs))

    def test_39_exhaustive_parallel_inputs_only_allow_off_commands(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                parallel = int(inputs.qf1_on) + int(inputs.qf2_on) + int(inputs.qf3_on) > 1
                if parallel:
                    self.assertTrue(outputs.xAlarmParallel, (state, inputs, outputs))
                    self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5, (state, inputs, outputs))
                    self.assertEqual(outputs.xQ2, inputs.qf1_on, (state, inputs, outputs))
                    self.assertEqual(outputs.xQ4, inputs.qf2_on, (state, inputs, outputs))
                    self.assertEqual(outputs.xQ6, inputs.qf3_on, (state, inputs, outputs))

    def test_40_exhaustive_alarm_is_exact_or_of_fault_parallel_and_undefined(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                expected = outputs.xAlarmFault or outputs.xAlarmParallel or outputs.xAlarmUndefined
                self.assertEqual(outputs.xAlarm, expected, (state, inputs, outputs))

    def test_41_exhaustive_fault_alarm_is_exact_or_of_breaker_faults(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                expected = inputs.qf1_fault or inputs.qf2_fault or inputs.qf3_fault
                self.assertEqual(outputs.xAlarmFault, expected, (state, inputs, outputs))

    def test_42_exhaustive_active_input_matches_on_contacts(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertEqual(outputs.udiActive, active_input(inputs), (state, inputs, outputs))

    def test_43_exhaustive_target_input_matches_priority_rule(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertEqual(outputs.udiTarget, target_input(inputs), (state, inputs, outputs))

    def test_43b_exhaustive_raw_target_matches_priority_rule(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertEqual(outputs.udiRawTarget, target_input(inputs), (state, inputs, outputs))
                self.assertEqual(outputs.udiPendingTarget, outputs.udiTarget, (state, inputs, outputs))
                self.assertEqual(outputs.udiDelayCounterSec, 0, (state, inputs, outputs))

    def test_44_exhaustive_no_source_flag_matches_target_zero(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertEqual(outputs.xNoSource, outputs.udiTarget == 0, (state, inputs, outputs))

    def test_45_exhaustive_manual_and_auto_modes_are_mutually_exclusive(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertNotEqual(outputs.xManualMode, outputs.xAutoMode, (state, inputs, outputs))

    def test_46_exhaustive_manual_selector_alone_blocks_close_commands(self):
        for state in STATES:
            for inputs in all_inputs():
                if not inputs.manual_selector:
                    continue
                outputs = run_once(inputs, state=state)
                self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5, (state, inputs, outputs))

    def test_47_exhaustive_undefined_flags_match_contact_rules(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                qf1_undef, qf2_undef, qf3_undef = undefined_flags(inputs, state)
                self.assertEqual(outputs.xQF1Undefined, qf1_undef, (state, inputs, outputs))
                self.assertEqual(outputs.xQF2Undefined, qf2_undef, (state, inputs, outputs))
                self.assertEqual(outputs.xQF3Undefined, qf3_undef, (state, inputs, outputs))
                self.assertEqual(outputs.xAlarmUndefined, qf1_undef or qf2_undef or qf3_undef, (state, inputs, outputs))

    def test_48_exhaustive_undefined_without_parallel_blocks_all_commands(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                if outputs.xAlarmUndefined and not outputs.xAlarmParallel:
                    self.assertFalse(
                        outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6,
                        (state, inputs, outputs),
                    )

    def test_49_exhaustive_non_parallel_off_commands_match_states(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                if outputs.xAlarmParallel:
                    continue
                if outputs.xQ2:
                    self.assertEqual(outputs.udiState, 11, (state, inputs, outputs))
                    self.assertFalse(inputs.qf1_off, (state, inputs, outputs))
                if outputs.xQ4:
                    self.assertEqual(outputs.udiState, 12, (state, inputs, outputs))
                    self.assertFalse(inputs.qf2_off, (state, inputs, outputs))
                if outputs.xQ6:
                    self.assertEqual(outputs.udiState, 13, (state, inputs, outputs))
                    self.assertFalse(inputs.qf3_off, (state, inputs, outputs))

    def test_50_exhaustive_state_output_is_always_known_state(self):
        known_states = {0, 11, 12, 13, 20, 31, 32, 33, 90}
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state=state)
                self.assertIn(outputs.udiState, known_states, (state, inputs, outputs))

    def test_51_exhaustive_clean_emergency_mode_clears_without_selector_edge(self):
        clean_inputs = AVRInputs(
            manual_selector=False,
            auto_return=True,
            u1_ok=True,
            u2_ok=True,
            u3_ok=True,
            qf1_off=True,
            qf2_off=True,
            qf3_off=True,
        )
        outputs = run_once(clean_inputs, state=90)
        self.assertFalse(outputs.xManualMode)
        self.assertTrue(outputs.xAutoMode)

        manual_inputs = AVRInputs(
            manual_selector=True,
            auto_return=True,
            u1_ok=True,
            u2_ok=True,
            u3_ok=True,
            qf1_off=True,
            qf2_off=True,
            qf3_off=True,
        )
        outputs = run_once(manual_inputs, state=90)
        self.assertTrue(outputs.xManualMode)
        self.assertFalse(outputs.xAutoMode)

    def test_52_exhaustive_dirty_emergency_mode_stays_until_inputs_are_normal(self):
        dirty_cases = [
            AVRInputs(u1_ok=True, qf1_fault=True),
            AVRInputs(u1_ok=True, qf1_on=True, qf2_on=True, qf1_off=False, qf2_off=False),
            AVRInputs(u1_ok=True, qf1_on=True, qf1_off=True),
        ]
        for inputs in dirty_cases:
            outputs = run_once(inputs, state=90)
            self.assertTrue(outputs.xManualMode, (inputs, outputs))

    def test_53_exhaustive_static_st_has_correct_q5_q6_mapping_and_no_timer_logic(self):
        code = (SRC_DIR / "FB_AVR_3IN1_PR200.st").read_text(encoding="utf-8")
        for token in ("SYS.TON", "UDINT_TO_TIME", "udiDeadMs", "udiTimeoutMs", "xAlarmTimeout"):
            self.assertNotIn(token, code)
        for token in ("xManualLatch", "xWasManualSelector", "xReturnFromManualToAuto"):
            self.assertNotIn(token, code)
        self.assertIn("Q5: включить 60F", code)
        self.assertIn("Q6: выключить 60F", code)
        self.assertIn("udiInputDelaySec : UDINT", code)
        self.assertNotIn("xSecondPulse", code)
        self.assertIn("udiDelayCounterSec := udiDelayCounterSec + 1", code)
        self.assertIn("udiRawTarget", code)
        self.assertIn("xTargetDelayActive", code)
        for token in ("DelayTimer", "TON", "T#1s"):
            self.assertNotIn(token, code)
        self.assertRegex(code, r"xQ5 := \(udiState = 33\)")
        self.assertRegex(code, r"xQ6 := \(udiState = 13\)")

    def test_54_modular_st_has_expected_small_blocks_and_safe_mapping(self):
        code = (SRC_DIR / "FB_AVR_3IN1_PR200_MODULAR.st").read_text(encoding="utf-8")
        for block_name in (
            "FB_AVR_QF_DIAG",
            "FB_AVR_PRIORITY_3",
            "FB_AVR_MODE_3",
            "FB_AVR_STATE_3",
            "FB_AVR_COMMANDS_3",
            "FB_AVR_3IN1_PR200_MODULAR",
        ):
            self.assertIn(block_name, code)
        for token in ("SYS.TON", "UDINT_TO_TIME", "udiDeadMs", "udiTimeoutMs", "xAlarmTimeout"):
            self.assertNotIn(token, code)
        self.assertIn("Q5: включить 60F", code)
        self.assertIn("Q6: выключить 60F", code)
        self.assertIn("udiInputDelaySec : UDINT", code)
        self.assertNotIn("xSecondPulse", code)
        self.assertIn("udiDelayCounterSec := udiDelayCounterSec + 1", code)
        self.assertIn("udiRawTarget", code)
        self.assertIn("xTargetDelayActive", code)
        for token in ("DelayTimer", "TON", "T#1s"):
            self.assertNotIn(token, code)
        self.assertRegex(code, r"xQ5 := \(udiState = 33\)")
        self.assertRegex(code, r"xQ6 := \(udiState = 13\)")

    def test_55_exhaustive_delay_memory_states_keep_commands_safe(self):
        for state in STATES:
            for stable_target in (0, 1, 2, 3):
                for inputs in all_inputs():
                    inputs.input_delay_sec = 3
                    avr = AVR3In1()
                    avr.state = state
                    avr.target_initialized = True
                    avr.stable_target = stable_target
                    avr.pending_target = target_input(inputs)
                    avr.delay_counter_sec = 1

                    outputs = avr.step(inputs)

                    self.assertFalse(outputs.xQ1 and outputs.xQ2, (state, stable_target, inputs, outputs))
                    self.assertFalse(outputs.xQ3 and outputs.xQ4, (state, stable_target, inputs, outputs))
                    self.assertFalse(outputs.xQ5 and outputs.xQ6, (state, stable_target, inputs, outputs))
                    self.assertLessEqual(int(outputs.xQ1) + int(outputs.xQ3) + int(outputs.xQ5), 1, (state, stable_target, inputs, outputs))
                    if outputs.xQ1 or outputs.xQ3 or outputs.xQ5:
                        self.assertTrue(outputs.xAutoMode, (state, stable_target, inputs, outputs))
                        self.assertFalse(outputs.xAlarm, (state, stable_target, inputs, outputs))
                    if outputs.xAlarmParallel:
                        self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5, (state, stable_target, inputs, outputs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
