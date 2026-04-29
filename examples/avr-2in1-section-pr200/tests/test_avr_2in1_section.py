import unittest
from pathlib import Path

from avr_2in1_section_sim import AVR2In1Section, AVRInputs, SectionPlant


SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def run_once(inputs, state=0):
    avr = AVR2In1Section()
    avr.state = state
    return avr.step(inputs)


class AVR2In1SectionScenarioTests(unittest.TestCase):
    def test_01_no_source_all_breakers_off_is_idle(self):
        outputs = run_once(AVRInputs())
        self.assertEqual(outputs.udiTargetScheme, 0)
        self.assertTrue(outputs.xNoSource)
        self.assertFalse(outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6)

    def test_02_both_sources_ok_from_all_off_starts_with_10f_close(self):
        outputs = run_once(AVRInputs(u1_ok=True, u2_ok=True))
        self.assertEqual(outputs.udiTargetScheme, 10)
        self.assertEqual(outputs.udiState, 21)
        self.assertTrue(outputs.xQ1)
        self.assertFalse(outputs.xQ3 or outputs.xQ5)

    def test_03_normal_scheme_closes_20f_after_10f_when_section_is_off(self):
        inputs = AVRInputs(u1_ok=True, u2_ok=True, qf1_on=True, qf1_off=False, qfs_off=True)
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 10)
        self.assertEqual(outputs.udiState, 22)
        self.assertTrue(outputs.xQ3)

    def test_04_confirmed_normal_scheme_is_idle(self):
        inputs = AVRInputs(
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiCurrentScheme, 10)
        self.assertTrue(outputs.xNormalScheme)
        self.assertEqual(outputs.udiState, 0)

    def test_05_auto_return_from_input1_backup_opens_section_first(self):
        inputs = AVRInputs(
            auto_return=True,
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiCurrentScheme, 11)
        self.assertEqual(outputs.udiTargetScheme, 10)
        self.assertEqual(outputs.udiState, 13)
        self.assertTrue(outputs.xQ6)

    def test_06_disabled_auto_return_holds_input1_backup(self):
        inputs = AVRInputs(
            auto_return=False,
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 11)
        self.assertEqual(outputs.udiState, 0)
        self.assertFalse(outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6)

    def test_07_disabled_auto_return_holds_input2_backup(self):
        inputs = AVRInputs(
            auto_return=False,
            u1_ok=True,
            u2_ok=True,
            qf1_off=True,
            qf2_on=True,
            qf2_off=False,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 12)
        self.assertEqual(outputs.udiState, 0)

    def test_08_only_input1_ready_from_all_off_closes_10f(self):
        outputs = run_once(AVRInputs(u1_ok=True, u2_ok=False))
        self.assertEqual(outputs.udiTargetScheme, 11)
        self.assertEqual(outputs.udiState, 21)
        self.assertTrue(outputs.xQ1)

    def test_09_only_input1_ready_after_10f_closes_section(self):
        inputs = AVRInputs(u1_ok=True, qf1_on=True, qf1_off=False, qf2_off=True, qfs_off=True)
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 11)
        self.assertEqual(outputs.udiState, 23)
        self.assertTrue(outputs.xQ5)

    def test_10_only_input1_ready_opens_20f_before_section(self):
        inputs = AVRInputs(
            u1_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 11)
        self.assertEqual(outputs.udiState, 12)
        self.assertTrue(outputs.xQ4)

    def test_11_only_input2_ready_opens_10f_before_section(self):
        inputs = AVRInputs(
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 12)
        self.assertEqual(outputs.udiState, 11)
        self.assertTrue(outputs.xQ2)

    def test_12_input1_loss_from_normal_opens_10f(self):
        inputs = AVRInputs(
            u1_ok=False,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 12)
        self.assertEqual(outputs.udiState, 11)
        self.assertTrue(outputs.xQ2)

    def test_13_input2_loss_from_normal_opens_20f(self):
        inputs = AVRInputs(
            u1_ok=True,
            u2_ok=False,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 11)
        self.assertEqual(outputs.udiState, 12)
        self.assertTrue(outputs.xQ4)

    def test_14_both_sources_lost_opens_existing_breakers(self):
        inputs = AVRInputs(
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = run_once(inputs)
        self.assertEqual(outputs.udiTargetScheme, 0)
        self.assertTrue(outputs.xNoSource)
        self.assertEqual(outputs.udiState, 11)
        self.assertTrue(outputs.xQ2)

    def test_15_forbidden_parallel_sends_only_trip_commands(self):
        inputs = AVRInputs(
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = run_once(inputs)
        self.assertTrue(outputs.xAlarmParallel)
        self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5)
        self.assertTrue(outputs.xQ2 and outputs.xQ4 and outputs.xQ6)

    def test_16_manual_selector_blocks_automatic_close(self):
        outputs = run_once(AVRInputs(manual_selector=True, u1_ok=True, u2_ok=True))
        self.assertTrue(outputs.xManualMode)
        self.assertFalse(outputs.xAutoMode)
        self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5)

    def test_17_fault_moves_to_manual_emergency_without_close_command(self):
        outputs = run_once(AVRInputs(u1_ok=True, qf1_fault=True))
        self.assertTrue(outputs.xAlarmFault)
        self.assertTrue(outputs.xManualMode)
        self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5)

    def test_18_invalid_on_and_off_contacts_are_undefined(self):
        outputs = run_once(AVRInputs(u1_ok=True, qf1_on=True, qf1_off=True))
        self.assertTrue(outputs.xQF1Undefined)
        self.assertTrue(outputs.xAlarmUndefined)
        self.assertTrue(outputs.xManualMode)

    def test_19_no_position_outside_command_is_undefined(self):
        outputs = run_once(AVRInputs(u1_ok=True, qf1_on=False, qf1_off=False))
        self.assertTrue(outputs.xQF1Undefined)
        self.assertTrue(outputs.xAlarmUndefined)

    def test_20_no_position_during_10f_close_command_is_allowed(self):
        inputs = AVRInputs(u1_ok=True, u2_ok=True, qf1_on=False, qf1_off=False, qfs_off=True)
        outputs = run_once(inputs, state=21)
        self.assertFalse(outputs.xQF1Undefined)
        self.assertTrue(outputs.xQ1)

    def test_21_no_position_during_section_close_command_is_allowed(self):
        inputs = AVRInputs(u1_ok=True, qf1_on=True, qf1_off=False, qf2_off=True, qfs_on=False, qfs_off=False)
        outputs = run_once(inputs, state=23)
        self.assertFalse(outputs.xQFSUndefined)
        self.assertTrue(outputs.xQ5)

    def test_22_emergency_state_clears_when_contacts_are_clean(self):
        outputs = run_once(AVRInputs(u1_ok=True, u2_ok=True), state=90)
        self.assertFalse(outputs.xManualMode)
        self.assertTrue(outputs.xAutoMode)
        self.assertEqual(outputs.udiState, 21)

    def test_23_section_breaker_output_mapping_and_no_timers_in_st(self):
        code = (SRC_DIR / "FB_AVR_2IN1_SECTION_PR200.st").read_text(encoding="utf-8")
        self.assertIn("Q5: включить 30F секционный автомат", code)
        self.assertIn("Q6: выключить 30F секционный автомат", code)
        self.assertIn("xQ5 := (udiState = 23)", code)
        self.assertIn("xQ6 := (udiState = 13)", code)
        for token in ("SYS.TON", "UDINT_TO_TIME", "udiDeadMs", "udiTimeoutMs", "xAlarmTimeout"):
            self.assertNotIn(token, code)

    def test_24_simulation_converges_from_all_off_to_normal_scheme(self):
        avr = AVR2In1Section()
        plant = SectionPlant()
        base = AVRInputs(u1_ok=True, u2_ok=True)
        last = None
        for _ in range(12):
            last = avr.step(plant.to_inputs(base))
            plant.apply(last)
        self.assertEqual(plant.on, [True, True, False])
        self.assertEqual(last.udiTargetScheme, 10)

    def test_25_simulation_transfers_from_normal_to_input2_backup(self):
        avr = AVR2In1Section()
        plant = SectionPlant()
        plant.set_scheme(10)
        base = AVRInputs(u1_ok=False, u2_ok=True)
        last = None
        for _ in range(12):
            last = avr.step(plant.to_inputs(base))
            plant.apply(last)
        self.assertEqual(plant.on, [False, True, True])
        self.assertEqual(last.udiTargetScheme, 12)

    def test_26_simulation_returns_to_normal_when_auto_return_enabled(self):
        avr = AVR2In1Section()
        plant = SectionPlant()
        plant.set_scheme(12)
        base = AVRInputs(auto_return=True, u1_ok=True, u2_ok=True)
        last = None
        for _ in range(12):
            last = avr.step(plant.to_inputs(base))
            plant.apply(last)
        self.assertEqual(plant.on, [True, True, False])
        self.assertEqual(last.udiTargetScheme, 10)

    def test_27_simulation_holds_backup_when_auto_return_disabled(self):
        avr = AVR2In1Section()
        plant = SectionPlant()
        plant.set_scheme(12)
        base = AVRInputs(auto_return=False, u1_ok=True, u2_ok=True)
        last = None
        for _ in range(8):
            last = avr.step(plant.to_inputs(base))
            plant.apply(last)
        self.assertEqual(plant.on, [False, True, True])
        self.assertEqual(last.udiTargetScheme, 12)

    def test_28_simulation_opens_all_when_sources_are_lost(self):
        avr = AVR2In1Section()
        plant = SectionPlant()
        plant.set_scheme(11)
        base = AVRInputs(u1_ok=False, u2_ok=False)
        for _ in range(12):
            outputs = avr.step(plant.to_inputs(base))
            plant.apply(outputs)
        self.assertEqual(plant.on, [False, False, False])

    def test_29_short_input_1_voltage_dip_does_not_switch_with_delay(self):
        avr = AVR2In1Section()
        normal = AVRInputs(
            input_delay_sec=3,
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = avr.step(normal)
        self.assertEqual(outputs.udiTargetScheme, 10)

        dip = AVRInputs(
            input_delay_sec=3,
            u1_ok=False,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        for _ in range(2):
            outputs = avr.step(dip)
            self.assertTrue(outputs.xTargetDelayActive)
            self.assertEqual(outputs.udiRawTargetScheme, 12)
            self.assertEqual(outputs.udiTargetScheme, 10)
            self.assertFalse(outputs.xQ2 or outputs.xQ6)

        restored = AVRInputs(
            input_delay_sec=3,
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = avr.step(restored)
        self.assertFalse(outputs.xTargetDelayActive)
        self.assertEqual(outputs.udiTargetScheme, 10)
        self.assertFalse(outputs.xQ2 or outputs.xQ6)

    def test_30_sustained_input_1_loss_switches_after_delay(self):
        avr = AVR2In1Section()
        normal = AVRInputs(
            input_delay_sec=3,
            u1_ok=True,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        avr.step(normal)

        lost = AVRInputs(
            input_delay_sec=3,
            u1_ok=False,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = avr.step(lost)
        self.assertTrue(outputs.xTargetDelayActive)
        self.assertFalse(outputs.xQ2)

        outputs = None
        for _ in range(3):
            outputs = avr.step(lost)

        self.assertIsNotNone(outputs)
        self.assertFalse(outputs.xTargetDelayActive)
        self.assertEqual(outputs.udiTargetScheme, 12)
        self.assertTrue(outputs.xQ2)

    def test_31_st_code_exposes_integer_delay_without_library_timer(self):
        code = (SRC_DIR / "FB_AVR_2IN1_SECTION_PR200.st").read_text(encoding="utf-8")
        self.assertIn("udiInputDelaySec : UDINT", code)
        self.assertIn("udiSectionCloseDelaySec : UDINT", code)
        self.assertNotIn("xSecondPulse", code)
        self.assertIn("udiDelayCounterSec := udiDelayCounterSec + 1", code)
        self.assertIn("udiSectionCloseDelayCounterSec := udiSectionCloseDelayCounterSec + 1", code)
        self.assertIn("xSectionCloseDelayActive", code)
        self.assertIn("udiRawTargetScheme", code)
        self.assertIn("xTargetDelayActive", code)
        for token in ("DelayTimer", "TON", "T#1s", "SYS.TON", "TON(", "UDINT_TO_TIME", "TIME_TO"):
            self.assertNotIn(token, code)

    def test_32_section_30f_waits_delay_before_closing_from_input1(self):
        avr = AVR2In1Section()
        inputs = AVRInputs(
            section_close_delay_sec=3,
            u1_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_off=True,
        )

        outputs = avr.step(inputs)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 1)
        self.assertEqual(outputs.udiState, 0)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(inputs)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 2)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(inputs)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 3)
        self.assertEqual(outputs.udiState, 23)
        self.assertTrue(outputs.xQ5)

    def test_33_section_30f_waits_delay_before_closing_from_input2(self):
        avr = AVR2In1Section()
        inputs = AVRInputs(
            section_close_delay_sec=2,
            u2_ok=True,
            qf1_off=True,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )

        outputs = avr.step(inputs)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 1)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(inputs)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertEqual(outputs.udiState, 23)
        self.assertTrue(outputs.xQ5)

    def test_34_section_delay_resets_when_request_disappears(self):
        avr = AVR2In1Section()
        ready_for_section = AVRInputs(
            section_close_delay_sec=3,
            u1_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_off=True,
        )
        outputs = avr.step(ready_for_section)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 1)
        self.assertTrue(outputs.xSectionCloseDelayActive)

        lost_source = AVRInputs(
            section_close_delay_sec=3,
            u1_ok=False,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_off=True,
        )
        outputs = avr.step(lost_source)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 0)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertFalse(outputs.xQ5)

    def test_35_simulation_does_not_close_section_immediately_after_input_trip(self):
        avr = AVR2In1Section()
        plant = SectionPlant(delay_cycles=1)
        plant.set_scheme(10)
        base = AVRInputs(section_close_delay_sec=3, u1_ok=False, u2_ok=True)

        outputs = avr.step(plant.to_inputs(base))
        plant.apply(outputs)
        self.assertTrue(outputs.xQ2)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(plant.to_inputs(base))
        plant.apply(outputs)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(plant.to_inputs(base))
        plant.apply(outputs)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(plant.to_inputs(base))
        plant.apply(outputs)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertTrue(outputs.xQ5)

    def test_36_dark_restart_from_input2_backup_opens_section_before_10f_close(self):
        avr = AVR2In1Section()

        restored_input1 = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=True,
            u2_ok=False,
            qf1_off=True,
            qf2_on=True,
            qf2_off=False,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = avr.step(restored_input1)
        self.assertEqual(outputs.udiTargetScheme, 11)
        self.assertTrue(outputs.xQ4)
        self.assertFalse(outputs.xQ1 or outputs.xQ5)

        qf2_open_section_still_closed = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=True,
            u2_ok=False,
            qf1_off=True,
            qf2_off=True,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = avr.step(qf2_open_section_still_closed)
        self.assertFalse(outputs.xQ1 or outputs.xQ5 or outputs.xQ6)

        outputs = avr.step(qf2_open_section_still_closed)
        self.assertTrue(outputs.xQ6)
        self.assertFalse(outputs.xQ1 or outputs.xQ5)

        section_open = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=True,
            u2_ok=False,
            qf1_off=True,
            qf2_off=True,
            qfs_off=True,
        )
        outputs = avr.step(section_open)
        self.assertFalse(outputs.xQ1 or outputs.xQ5)

        outputs = avr.step(section_open)
        self.assertTrue(outputs.xQ1)
        self.assertFalse(outputs.xQ5)

        input1_closed = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=True,
            u2_ok=False,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_off=True,
        )
        outputs = avr.step(input1_closed)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(input1_closed)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertTrue(outputs.xQ5)

    def test_37_dark_restart_from_input1_backup_opens_section_before_20f_close(self):
        avr = AVR2In1Section()

        restored_input2 = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=False,
            u2_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = avr.step(restored_input2)
        self.assertEqual(outputs.udiTargetScheme, 12)
        self.assertTrue(outputs.xQ2)
        self.assertFalse(outputs.xQ3 or outputs.xQ5)

        qf1_open_section_still_closed = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=False,
            u2_ok=True,
            qf1_off=True,
            qf2_off=True,
            qfs_on=True,
            qfs_off=False,
        )
        outputs = avr.step(qf1_open_section_still_closed)
        self.assertFalse(outputs.xQ3 or outputs.xQ5 or outputs.xQ6)

        outputs = avr.step(qf1_open_section_still_closed)
        self.assertTrue(outputs.xQ6)
        self.assertFalse(outputs.xQ3 or outputs.xQ5)

        section_open = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=False,
            u2_ok=True,
            qf1_off=True,
            qf2_off=True,
            qfs_off=True,
        )
        outputs = avr.step(section_open)
        self.assertFalse(outputs.xQ3 or outputs.xQ5)

        outputs = avr.step(section_open)
        self.assertTrue(outputs.xQ3)
        self.assertFalse(outputs.xQ5)

        input2_closed = AVRInputs(
            section_close_delay_sec=2,
            u1_ok=False,
            u2_ok=True,
            qf1_off=True,
            qf2_on=True,
            qf2_off=False,
            qfs_off=True,
        )
        outputs = avr.step(input2_closed)
        self.assertTrue(outputs.xSectionCloseDelayActive)
        self.assertFalse(outputs.xQ5)

        outputs = avr.step(input2_closed)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertTrue(outputs.xQ5)

    def test_38_input_delay_does_not_delay_section_when_section_delay_is_zero(self):
        avr = AVR2In1Section()
        inputs = AVRInputs(
            input_delay_sec=5,
            section_close_delay_sec=0,
            u1_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_off=True,
            qfs_off=True,
        )

        outputs = avr.step(inputs)
        self.assertFalse(outputs.xSectionCloseDelayActive)
        self.assertEqual(outputs.udiSectionCloseDelayCounterSec, 0)
        self.assertTrue(outputs.xQ5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
