import itertools
import re
import unittest
from pathlib import Path

from avr_2in1_section_sim import AVR2In1Section, AVRInputs


INPUT_FIELDS = (
    "manual_selector",
    "auto_return",
    "u1_ok",
    "u2_ok",
    "qf1_on",
    "qf1_off",
    "qf1_fault",
    "qf2_on",
    "qf2_off",
    "qf2_fault",
    "qfs_on",
    "qfs_off",
    "qfs_fault",
)

STATES = (0, 11, 12, 13, 21, 22, 23, 90, 777)
SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def all_inputs():
    for bits in itertools.product((False, True), repeat=len(INPUT_FIELDS)):
        yield AVRInputs(**dict(zip(INPUT_FIELDS, bits)))


def run_once(inputs, state=0):
    avr = AVR2In1Section()
    avr.state = state
    return avr.step(inputs)


def ready(inputs):
    return (
        inputs.u1_ok and not inputs.qf1_fault,
        inputs.u2_ok and not inputs.qf2_fault,
    )


def current_scheme(inputs):
    if inputs.qf1_on and inputs.qf2_on and inputs.qfs_on:
        return 99
    if inputs.qf1_on and inputs.qf2_on and inputs.qfs_off:
        return 10
    if inputs.qf1_on and inputs.qf2_off and inputs.qfs_on:
        return 11
    if inputs.qf1_off and inputs.qf2_on and inputs.qfs_on:
        return 12
    return 0


def target_scheme(inputs):
    s1_ready, s2_ready = ready(inputs)
    target = 0
    if s1_ready and s2_ready:
        target = 10
        if not inputs.auto_return:
            current = current_scheme(inputs)
            if current == 11:
                target = 11
            elif current == 12:
                target = 12
    elif s1_ready:
        target = 11
    elif s2_ready:
        target = 12
    return target


def undefined_flags(inputs, prior_state):
    qf1_invalid = inputs.qf1_on and inputs.qf1_off
    qf2_invalid = inputs.qf2_on and inputs.qf2_off
    qfs_invalid = inputs.qfs_on and inputs.qfs_off

    qf1_no_pos = not inputs.qf1_on and not inputs.qf1_off
    qf2_no_pos = not inputs.qf2_on and not inputs.qf2_off
    qfs_no_pos = not inputs.qfs_on and not inputs.qfs_off

    qf1_undefined = qf1_invalid or (qf1_no_pos and prior_state not in {11, 21})
    qf2_undefined = qf2_invalid or (qf2_no_pos and prior_state not in {12, 22})
    qfs_undefined = qfs_invalid or (qfs_no_pos and prior_state not in {13, 23})
    return qf1_undefined, qf2_undefined, qfs_undefined


def bus_powered(inputs):
    s1_ready, s2_ready = ready(inputs)
    bus1 = (inputs.qf1_on and s1_ready) or (inputs.qfs_on and inputs.qf2_on and s2_ready)
    bus2 = (inputs.qf2_on and s2_ready) or (inputs.qfs_on and inputs.qf1_on and s1_ready)
    return bus1, bus2


class AVR2In1SectionInvariantTests(unittest.TestCase):
    def test_29_exhaustive_no_breaker_has_open_and_close_commands_together(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertFalse(outputs.xQ1 and outputs.xQ2, (state, inputs, outputs))
                self.assertFalse(outputs.xQ3 and outputs.xQ4, (state, inputs, outputs))
                self.assertFalse(outputs.xQ5 and outputs.xQ6, (state, inputs, outputs))

    def test_30_exhaustive_at_most_one_close_command_exists(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                close_count = int(outputs.xQ1) + int(outputs.xQ3) + int(outputs.xQ5)
                self.assertLessEqual(close_count, 1, (state, inputs, outputs))

    def test_31_exhaustive_close_commands_require_auto_mode_and_no_alarm(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xQ1 or outputs.xQ3 or outputs.xQ5:
                    self.assertTrue(outputs.xAutoMode, (state, inputs, outputs))
                    self.assertFalse(outputs.xManualMode, (state, inputs, outputs))
                    self.assertFalse(outputs.xAlarm, (state, inputs, outputs))

    def test_32_exhaustive_close_10f_requires_ready_input_and_safe_topology(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xQ1:
                    self.assertTrue(inputs.u1_ok and not inputs.qf1_fault, (state, inputs, outputs))
                    self.assertFalse(inputs.qf1_on, (state, inputs, outputs))
                    self.assertEqual(outputs.udiState, 21, (state, inputs, outputs))
                    self.assertIn(outputs.udiTargetScheme, {10, 11}, (state, inputs, outputs))
                    if outputs.udiTargetScheme == 10:
                        self.assertTrue(inputs.qfs_off, (state, inputs, outputs))
                    if outputs.udiTargetScheme == 11:
                        self.assertTrue(inputs.qf2_off, (state, inputs, outputs))
                        self.assertTrue(inputs.qfs_off, (state, inputs, outputs))
                    self.assertFalse(inputs.qfs_on, (state, inputs, outputs))

    def test_33_exhaustive_close_20f_requires_ready_input_and_safe_topology(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xQ3:
                    self.assertTrue(inputs.u2_ok and not inputs.qf2_fault, (state, inputs, outputs))
                    self.assertFalse(inputs.qf2_on, (state, inputs, outputs))
                    self.assertEqual(outputs.udiState, 22, (state, inputs, outputs))
                    self.assertIn(outputs.udiTargetScheme, {10, 12}, (state, inputs, outputs))
                    if outputs.udiTargetScheme == 10:
                        self.assertTrue(inputs.qfs_off, (state, inputs, outputs))
                    if outputs.udiTargetScheme == 12:
                        self.assertTrue(inputs.qf1_off, (state, inputs, outputs))
                        self.assertTrue(inputs.qfs_off, (state, inputs, outputs))
                    self.assertFalse(inputs.qfs_on, (state, inputs, outputs))

    def test_34_exhaustive_close_section_requires_one_confirmed_incomer_and_other_off(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xQ5:
                    self.assertFalse(inputs.qfs_on, (state, inputs, outputs))
                    self.assertEqual(outputs.udiState, 23, (state, inputs, outputs))
                    self.assertIn(outputs.udiTargetScheme, {11, 12}, (state, inputs, outputs))
                    if outputs.udiTargetScheme == 11:
                        self.assertTrue(inputs.u1_ok and not inputs.qf1_fault, (state, inputs, outputs))
                        self.assertTrue(inputs.qf1_on and inputs.qf2_off, (state, inputs, outputs))
                    if outputs.udiTargetScheme == 12:
                        self.assertTrue(inputs.u2_ok and not inputs.qf2_fault, (state, inputs, outputs))
                        self.assertTrue(inputs.qf2_on and inputs.qf1_off, (state, inputs, outputs))
                    self.assertFalse(inputs.qf1_on and inputs.qf2_on, (state, inputs, outputs))

    def test_35_exhaustive_section_never_closes_for_normal_or_no_source_target(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.udiTargetScheme in {0, 10}:
                    self.assertFalse(outputs.xQ5, (state, inputs, outputs))

    def test_36_exhaustive_forbidden_parallel_only_allows_open_commands(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                parallel = inputs.qf1_on and inputs.qf2_on and inputs.qfs_on
                if parallel:
                    self.assertTrue(outputs.xAlarmParallel, (state, inputs, outputs))
                    self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5, (state, inputs, outputs))
                    self.assertEqual(outputs.xQ2, inputs.qf1_on, (state, inputs, outputs))
                    self.assertEqual(outputs.xQ4, inputs.qf2_on, (state, inputs, outputs))
                    self.assertEqual(outputs.xQ6, inputs.qfs_on, (state, inputs, outputs))

    def test_37_exhaustive_alarm_is_exact_or_of_fault_parallel_and_undefined(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                expected = outputs.xAlarmFault or outputs.xAlarmParallel or outputs.xAlarmUndefined
                self.assertEqual(outputs.xAlarm, expected, (state, inputs, outputs))

    def test_38_exhaustive_fault_alarm_is_exact_or_of_breaker_faults(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                expected = inputs.qf1_fault or inputs.qf2_fault or inputs.qfs_fault
                self.assertEqual(outputs.xAlarmFault, expected, (state, inputs, outputs))

    def test_39_exhaustive_current_scheme_matches_confirmed_contacts(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertEqual(outputs.udiCurrentScheme, current_scheme(inputs), (state, inputs, outputs))

    def test_40_exhaustive_target_scheme_matches_priority_and_autoreturn_rule(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertEqual(outputs.udiTargetScheme, target_scheme(inputs), (state, inputs, outputs))

    def test_40b_exhaustive_raw_target_scheme_matches_priority_and_autoreturn_rule(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertEqual(outputs.udiRawTargetScheme, target_scheme(inputs), (state, inputs, outputs))
                self.assertEqual(outputs.udiPendingTargetScheme, outputs.udiTargetScheme, (state, inputs, outputs))
                self.assertEqual(outputs.udiDelayCounterSec, 0, (state, inputs, outputs))

    def test_41_exhaustive_no_source_flag_matches_target_zero(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertEqual(outputs.xNoSource, outputs.udiTargetScheme == 0, (state, inputs, outputs))

    def test_42_exhaustive_manual_and_auto_modes_are_mutually_exclusive(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertNotEqual(outputs.xManualMode, outputs.xAutoMode, (state, inputs, outputs))

    def test_43_exhaustive_manual_selector_blocks_all_commands_without_parallel_alarm(self):
        for state in STATES:
            for inputs in all_inputs():
                if not inputs.manual_selector:
                    continue
                outputs = run_once(inputs, state)
                if not outputs.xAlarmParallel:
                    self.assertFalse(
                        outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6,
                        (state, inputs, outputs),
                    )

    def test_44_exhaustive_any_fault_blocks_all_commands_without_parallel_alarm(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xAlarmFault and not outputs.xAlarmParallel:
                    self.assertFalse(
                        outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6,
                        (state, inputs, outputs),
                    )

    def test_45_exhaustive_undefined_flags_match_contact_rules(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                qf1_undef, qf2_undef, qfs_undef = undefined_flags(inputs, state)
                self.assertEqual(outputs.xQF1Undefined, qf1_undef, (state, inputs, outputs))
                self.assertEqual(outputs.xQF2Undefined, qf2_undef, (state, inputs, outputs))
                self.assertEqual(outputs.xQFSUndefined, qfs_undef, (state, inputs, outputs))
                self.assertEqual(outputs.xAlarmUndefined, qf1_undef or qf2_undef or qfs_undef, (state, inputs, outputs))

    def test_46_exhaustive_undefined_without_parallel_blocks_all_commands(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xAlarmUndefined and not outputs.xAlarmParallel:
                    self.assertFalse(
                        outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6,
                        (state, inputs, outputs),
                    )

    def test_47_exhaustive_non_parallel_open_commands_match_states(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xAlarmParallel:
                    continue
                if outputs.xQ2:
                    self.assertEqual(outputs.udiState, 11, (state, inputs, outputs))
                    self.assertFalse(inputs.qf1_off, (state, inputs, outputs))
                    self.assertTrue(outputs.xAutoMode, (state, inputs, outputs))
                if outputs.xQ4:
                    self.assertEqual(outputs.udiState, 12, (state, inputs, outputs))
                    self.assertFalse(inputs.qf2_off, (state, inputs, outputs))
                    self.assertTrue(outputs.xAutoMode, (state, inputs, outputs))
                if outputs.xQ6:
                    self.assertEqual(outputs.udiState, 13, (state, inputs, outputs))
                    self.assertFalse(inputs.qfs_off, (state, inputs, outputs))
                    self.assertTrue(outputs.xAutoMode, (state, inputs, outputs))

    def test_48_exhaustive_state_output_is_always_known_state(self):
        known_states = {0, 11, 12, 13, 21, 22, 23, 90}
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertIn(outputs.udiState, known_states, (state, inputs, outputs))

    def test_49_exhaustive_confirmed_scheme_flags_are_exact(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertEqual(outputs.xNormalScheme, inputs.qf1_on and inputs.qf2_on and inputs.qfs_off, (state, inputs, outputs))
                self.assertEqual(outputs.xFromInput1Scheme, inputs.qf1_on and inputs.qf2_off and inputs.qfs_on, (state, inputs, outputs))
                self.assertEqual(outputs.xFromInput2Scheme, inputs.qf1_off and inputs.qf2_on and inputs.qfs_on, (state, inputs, outputs))

    def test_50_exhaustive_bus_power_flags_are_exact(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                bus1, bus2 = bus_powered(inputs)
                self.assertEqual(outputs.xBus1Powered, bus1, (state, inputs, outputs))
                self.assertEqual(outputs.xBus2Powered, bus2, (state, inputs, outputs))

    def test_51_exhaustive_target_normal_requires_both_sources_ready(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.udiTargetScheme == 10:
                    s1_ready, s2_ready = ready(inputs)
                    self.assertTrue(s1_ready and s2_ready, (state, inputs, outputs))

    def test_52_exhaustive_target_input1_backup_requires_input1_ready(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.udiTargetScheme == 11:
                    s1_ready, _ = ready(inputs)
                    self.assertTrue(s1_ready, (state, inputs, outputs))

    def test_53_exhaustive_target_input2_backup_requires_input2_ready(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.udiTargetScheme == 12:
                    _, s2_ready = ready(inputs)
                    self.assertTrue(s2_ready, (state, inputs, outputs))

    def test_54_exhaustive_both_ready_with_auto_return_targets_normal(self):
        for state in STATES:
            for inputs in all_inputs():
                if not (inputs.auto_return and inputs.u1_ok and inputs.u2_ok and not inputs.qf1_fault and not inputs.qf2_fault):
                    continue
                outputs = run_once(inputs, state)
                self.assertEqual(outputs.udiTargetScheme, 10, (state, inputs, outputs))

    def test_55_exhaustive_disabled_autoreturn_only_holds_confirmed_backup_schemes(self):
        for state in STATES:
            for inputs in all_inputs():
                if inputs.auto_return:
                    continue
                outputs = run_once(inputs, state)
                s1_ready, s2_ready = ready(inputs)
                if s1_ready and s2_ready and outputs.udiTargetScheme in {11, 12}:
                    self.assertIn(current_scheme(inputs), {11, 12}, (state, inputs, outputs))

    def test_56_exhaustive_close_commands_cannot_create_forbidden_parallel(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                future_qf1 = inputs.qf1_on or outputs.xQ1
                future_qf2 = inputs.qf2_on or outputs.xQ3
                future_qfs = inputs.qfs_on or outputs.xQ5
                if outputs.xQ1 or outputs.xQ3 or outputs.xQ5:
                    self.assertFalse(future_qf1 and future_qf2 and future_qfs, (state, inputs, outputs))

    def test_57_exhaustive_target_values_are_limited_to_defined_schemes(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                self.assertIn(outputs.udiTargetScheme, {0, 10, 11, 12}, (state, inputs, outputs))

    def test_58_static_st_is_one_function_block_with_expected_safe_features(self):
        code = (SRC_DIR / "FB_AVR_2IN1_SECTION_PR200.st").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^FUNCTION_BLOCK\s+", code, flags=re.MULTILINE)), 1)
        self.assertIn("FUNCTION_BLOCK FB_AVR_2IN1_SECTION_PR200", code)
        self.assertIn("xAlarmParallel := xQF1On AND xQF2On AND xQFSOn;", code)
        self.assertIn("xQ5 := (udiState = 23)", code)
        self.assertIn("xQ6 := (udiState = 13)", code)
        self.assertIn("udiInputDelaySec : UDINT", code)
        self.assertIn("udiSectionCloseDelaySec : UDINT", code)
        self.assertNotIn("xSecondPulse", code)
        self.assertIn("udiDelayCounterSec := udiDelayCounterSec + 1", code)
        self.assertIn("udiSectionCloseDelayCounterSec := udiSectionCloseDelayCounterSec + 1", code)
        self.assertIn("udiRawTargetScheme", code)
        self.assertIn("xTargetDelayActive", code)
        self.assertIn("xSectionCloseDelayActive", code)
        for token in ("DelayTimer", "TON", "T#1s", "SYS.TON", "TON(", "UDINT_TO_TIME", "udiDeadMs", "udiTimeoutMs", "xAlarmTimeout"):
            self.assertNotIn(token, code)

    def test_59_exhaustive_delay_memory_states_keep_commands_safe(self):
        for state in STATES:
            for stable_target in (0, 10, 11, 12):
                for inputs in all_inputs():
                    inputs.input_delay_sec = 3
                    avr = AVR2In1Section()
                    avr.state = state
                    avr.target_initialized = True
                    avr.stable_target_scheme = stable_target
                    avr.pending_target_scheme = target_scheme(inputs)
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

    def test_60_exhaustive_section_close_delay_memory_keeps_commands_safe(self):
        for state in STATES:
            for stable_target in (0, 10, 11, 12):
                for section_counter in (0, 1, 2, 3):
                    for inputs in all_inputs():
                        inputs.section_close_delay_sec = 3
                        avr = AVR2In1Section()
                        avr.state = state
                        avr.target_initialized = True
                        avr.stable_target_scheme = stable_target
                        avr.pending_target_scheme = target_scheme(inputs)
                        avr.delay_counter_sec = 0
                        avr.section_close_delay_counter_sec = section_counter

                        outputs = avr.step(inputs)

                        self.assertFalse(outputs.xSectionCloseDelayActive and outputs.xQ5, (state, stable_target, section_counter, inputs, outputs))
                        self.assertFalse(outputs.xQ1 and outputs.xQ2, (state, stable_target, section_counter, inputs, outputs))
                        self.assertFalse(outputs.xQ3 and outputs.xQ4, (state, stable_target, section_counter, inputs, outputs))
                        self.assertFalse(outputs.xQ5 and outputs.xQ6, (state, stable_target, section_counter, inputs, outputs))
                        self.assertLessEqual(
                            int(outputs.xQ1) + int(outputs.xQ3) + int(outputs.xQ5),
                            1,
                            (state, stable_target, section_counter, inputs, outputs),
                        )
                        if outputs.xQ5 and state != 23:
                            self.assertGreaterEqual(
                                outputs.udiSectionCloseDelayCounterSec,
                                inputs.section_close_delay_sec,
                                (state, stable_target, section_counter, inputs, outputs),
                            )

    def test_61_exhaustive_incomer_close_commands_require_section_off(self):
        for state in STATES:
            for inputs in all_inputs():
                outputs = run_once(inputs, state)
                if outputs.xQ1 or outputs.xQ3:
                    self.assertTrue(inputs.qfs_off, (state, inputs, outputs))
                    self.assertFalse(inputs.qfs_on, (state, inputs, outputs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
