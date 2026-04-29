import unittest
from dataclasses import fields
from pathlib import Path

from avr_3in1_sim import AVR3In1, AVRInputs, MotorPlant


SRC_DIR = Path(__file__).resolve().parents[1] / "src"


class AVR3In1Tests(unittest.TestCase):
    def run_closed_loop(self, avr, plant, base, cycles=40):
        trace = []
        for _ in range(cycles):
            inputs = plant.to_inputs(base)
            outputs = avr.step(inputs)
            trace.append((inputs, outputs, tuple(plant.on), tuple(plant.pending)))
            plant.apply(outputs)
        return trace

    def assert_no_crossing(self, trace):
        for step, (inputs, outputs, plant_on, pending) in enumerate(trace):
            other_is_on_for_q1 = outputs.xQ1 and (inputs.qf2_on or inputs.qf3_on)
            other_is_on_for_q3 = outputs.xQ3 and (inputs.qf1_on or inputs.qf3_on)
            other_is_on_for_q5 = outputs.xQ5 and (inputs.qf1_on or inputs.qf2_on)
            self.assertFalse(
                other_is_on_for_q1 or other_is_on_for_q3 or other_is_on_for_q5,
                f"crossing command at step {step}: outputs={outputs}, plant_on={plant_on}, pending={pending}",
            )
            self.assertLessEqual(sum(plant_on), 1, f"physical crossing at step {step}: {plant_on}")

    def assert_no_command_conflict(self, trace):
        for step, (_, outputs, _, _) in enumerate(trace):
            self.assertFalse(outputs.xQ1 and outputs.xQ2, f"40F command conflict at step {step}")
            self.assertFalse(outputs.xQ3 and outputs.xQ4, f"50F command conflict at step {step}")
            self.assertFalse(outputs.xQ5 and outputs.xQ6, f"60F command conflict at step {step}")

    def test_01_all_sources_ok_selects_input_1(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=10)
        self.assertTrue(plant.on[0])
        self.assert_no_crossing(trace)

    def test_02_input_1_lost_selects_input_2(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(1)
        base = AVRInputs(u1_ok=False, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=16)
        self.assertTrue(plant.on[1])
        self.assert_no_crossing(trace)

    def test_03_inputs_1_and_2_lost_selects_input_3(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(2)
        base = AVRInputs(u1_ok=False, u2_ok=False, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=16)
        self.assertTrue(plant.on[2])
        self.assert_no_crossing(trace)

    def test_04_no_sources_turns_active_input_off(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(3)
        base = AVRInputs(u1_ok=False, u2_ok=False, u3_ok=False)
        trace = self.run_closed_loop(avr, plant, base, cycles=12)
        self.assertEqual(plant.on, [False, False, False])
        self.assertTrue(any(o.xQ6 for _, o, _, _ in trace))
        self.assertTrue(trace[-1][1].xNoSource)

    def test_05_active_good_input_stays_connected(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(1)
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=8)
        self.assertEqual(plant.on, [True, False, False])
        self.assertFalse(any(o.xQ1 or o.xQ2 or o.xQ3 or o.xQ4 or o.xQ5 or o.xQ6 for _, o, _, _ in trace))

    def test_06_auto_return_moves_from_input_2_to_input_1(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(2)
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=18)
        self.assertEqual(plant.on, [True, False, False])
        self.assertTrue(any(o.xQ4 for _, o, _, _ in trace))
        self.assertTrue(any(o.xQ1 for _, o, _, _ in trace))
        self.assert_no_crossing(trace)

    def test_07_auto_return_disabled_keeps_good_active_input_2(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(2)
        base = AVRInputs(auto_return=False, u1_ok=True, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=10)
        self.assertEqual(plant.on, [False, True, False])
        self.assertFalse(any(o.xQ1 or o.xQ4 for _, o, _, _ in trace))

    def test_08_auto_return_disabled_still_transfers_if_active_lost(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        plant.set_on(2)
        base = AVRInputs(auto_return=False, u1_ok=True, u2_ok=False, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=18)
        self.assertEqual(plant.on, [True, False, False])
        self.assert_no_crossing(trace)

    def test_09_input_3_works_without_generator_sent_signal(self):
        input_names = {field.name for field in fields(AVRInputs)}
        forbidden = {"xDGUSent", "xDguSent", "xGenStartSent", "xGeneratorSent", "xInput3SignalSent", "dgu_sent"}
        self.assertTrue(forbidden.isdisjoint(input_names))
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=2)
        base = AVRInputs(u1_ok=False, u2_ok=False, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=12)
        self.assertEqual(plant.on, [False, False, True])
        self.assertTrue(any(o.xQ5 for _, o, _, _ in trace))

    def test_10_manual_selector_blocks_automatic_commands(self):
        avr = AVR3In1()
        base = AVRInputs(manual_selector=True, u1_ok=True, u2_ok=True, u3_ok=True)
        outputs = avr.step(base)
        self.assertTrue(outputs.xManualMode)
        self.assertFalse(outputs.xAutoMode)
        self.assertFalse(outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6)

    def test_11_qf1_fault_sets_emergency_manual_mode(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True, qf1_fault=True))
        self.assertTrue(outputs.xAlarmFault)
        self.assertTrue(outputs.xManualMode)

    def test_12_qf2_fault_sets_emergency_manual_mode(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True, qf2_fault=True))
        self.assertTrue(outputs.xAlarmFault)
        self.assertTrue(outputs.xManualMode)

    def test_13_qf3_fault_sets_emergency_manual_mode(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True, qf3_fault=True))
        self.assertTrue(outputs.xAlarmFault)
        self.assertTrue(outputs.xManualMode)

    def test_14_fault_mode_clears_automatically_after_fault_contact_normal(self):
        avr = AVR3In1()
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True, qf1_fault=True)
        self.assertTrue(avr.step(base).xManualMode)
        base.qf1_fault = False
        outputs = avr.step(base)
        self.assertFalse(outputs.xManualMode)
        self.assertTrue(outputs.xAutoMode)
        self.assertFalse(outputs.xAlarmFault)

    def test_15_fault_mode_stays_while_fault_contact_is_active(self):
        avr = AVR3In1()
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True, qf1_fault=True)
        self.assertTrue(avr.step(base).xManualMode)
        outputs = avr.step(base)
        self.assertTrue(outputs.xManualMode)
        self.assertTrue(outputs.xAlarmFault)

    def test_16_parallel_inputs_1_and_2_send_only_off_commands(self):
        avr = AVR3In1()
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True, qf1_on=True, qf1_off=False, qf2_on=True, qf2_off=False)
        outputs = avr.step(base)
        self.assertTrue(outputs.xAlarmParallel)
        self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5)
        self.assertTrue(outputs.xQ2)
        self.assertTrue(outputs.xQ4)
        self.assertFalse(outputs.xQ6)

    def test_17_parallel_all_inputs_send_all_off_commands(self):
        avr = AVR3In1()
        base = AVRInputs(
            u1_ok=True,
            u2_ok=True,
            u3_ok=True,
            qf1_on=True,
            qf1_off=False,
            qf2_on=True,
            qf2_off=False,
            qf3_on=True,
            qf3_off=False,
        )
        outputs = avr.step(base)
        self.assertTrue(outputs.xAlarmParallel)
        self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5)
        self.assertTrue(outputs.xQ2 and outputs.xQ4 and outputs.xQ6)

    def test_18_qf1_on_and_off_both_true_is_undefined(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, qf1_on=True, qf1_off=True))
        self.assertTrue(outputs.xQF1Undefined)
        self.assertTrue(outputs.xAlarmUndefined)
        self.assertTrue(outputs.xManualMode)

    def test_19_qf2_on_and_off_both_true_is_undefined(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u2_ok=True, qf2_on=True, qf2_off=True))
        self.assertTrue(outputs.xQF2Undefined)
        self.assertTrue(outputs.xAlarmUndefined)
        self.assertTrue(outputs.xManualMode)

    def test_20_qf3_on_and_off_both_true_is_undefined(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u3_ok=True, qf3_on=True, qf3_off=True))
        self.assertTrue(outputs.xQF3Undefined)
        self.assertTrue(outputs.xAlarmUndefined)
        self.assertTrue(outputs.xManualMode)

    def test_21_qf1_no_position_without_command_is_undefined(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, qf1_on=False, qf1_off=False))
        self.assertTrue(outputs.xQF1Undefined)
        self.assertTrue(outputs.xManualMode)

    def test_22_qf2_no_position_without_command_is_undefined(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u2_ok=True, qf2_on=False, qf2_off=False))
        self.assertTrue(outputs.xQF2Undefined)
        self.assertTrue(outputs.xManualMode)

    def test_23_qf3_no_position_without_command_is_undefined(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u3_ok=True, qf3_on=False, qf3_off=False))
        self.assertTrue(outputs.xQF3Undefined)
        self.assertTrue(outputs.xManualMode)

    def test_24_qf1_no_position_during_off_command_is_allowed(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=False, u2_ok=True, qf1_on=True, qf1_off=False))
        self.assertTrue(outputs.xQ2)
        outputs = avr.step(AVRInputs(u1_ok=False, u2_ok=True, qf1_on=False, qf1_off=False))
        self.assertFalse(outputs.xAlarmUndefined)
        self.assertTrue(outputs.xQ2)

    def test_25_qf2_no_position_during_on_command_is_allowed(self):
        avr = AVR3In1()
        base = AVRInputs(u1_ok=False, u2_ok=True, u3_ok=False)
        self.assertFalse(avr.step(base).xQ3)
        self.assertTrue(avr.step(base).xQ3)
        moving = AVRInputs(u1_ok=False, u2_ok=True, u3_ok=False, qf2_on=False, qf2_off=False)
        outputs = avr.step(moving)
        self.assertFalse(outputs.xAlarmUndefined)
        self.assertTrue(outputs.xQ3)

    def test_26_unknown_other_breaker_blocks_target_closing(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, qf2_on=False, qf2_off=False))
        self.assertTrue(outputs.xAlarmUndefined)
        self.assertFalse(outputs.xQ1)

    def test_27_no_on_command_until_all_other_off_contacts_confirmed(self):
        avr = AVR3In1()
        outputs = avr.step(AVRInputs(u1_ok=True, qf2_on=False, qf2_off=False, qf3_off=True))
        self.assertFalse(outputs.xQ1)
        self.assertTrue(outputs.xManualMode)

    def test_28_no_crossing_during_slow_off_and_on_sequence(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=5)
        plant.set_on(1)
        base = AVRInputs(u1_ok=False, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=30)
        self.assertEqual(plant.on, [False, True, False])
        self.assert_no_crossing(trace)
        self.assert_no_command_conflict(trace)

    def test_29_no_command_conflicts_in_priority_walk(self):
        avr = AVR3In1()
        plant = MotorPlant(delay_cycles=3)
        base = AVRInputs(u1_ok=True, u2_ok=True, u3_ok=True)
        trace = self.run_closed_loop(avr, plant, base, cycles=12)
        base.u1_ok = False
        trace += self.run_closed_loop(avr, plant, base, cycles=12)
        base.u2_ok = False
        trace += self.run_closed_loop(avr, plant, base, cycles=12)
        self.assert_no_command_conflict(trace)
        self.assert_no_crossing(trace)

    def test_30_source_lost_during_on_command_stops_closing(self):
        avr = AVR3In1()
        base = AVRInputs(u1_ok=True)
        avr.step(base)
        self.assertTrue(avr.step(base).xQ1)
        base.u1_ok = False
        outputs = avr.step(base)
        self.assertFalse(outputs.xQ1)

    def test_31_st_code_has_no_timer_based_logic(self):
        code = (SRC_DIR / "FB_AVR_3IN1_PR200.st").read_text(encoding="utf-8")
        forbidden = ["SYS.TON", "udiDeadMs", "udiTimeoutMs", "xAlarmTimeout", "UDINT_TO_TIME"]
        for token in forbidden:
            self.assertNotIn(token, code)

    def test_32_st_code_exposes_undefined_alarm_outputs(self):
        code = (SRC_DIR / "FB_AVR_3IN1_PR200.st").read_text(encoding="utf-8")
        for token in ["xAlarmUndefined", "xQF1Undefined", "xQF2Undefined", "xQF3Undefined"]:
            self.assertIn(token, code)

    def test_33_short_input_1_voltage_dip_does_not_switch_with_delay(self):
        avr = AVR3In1()
        normal = AVRInputs(input_delay_sec=3, u1_ok=True, u2_ok=True, u3_ok=True, qf1_on=True, qf1_off=False)
        outputs = avr.step(normal)
        self.assertEqual(outputs.udiTarget, 1)

        dip = AVRInputs(input_delay_sec=3, u1_ok=False, u2_ok=True, u3_ok=True, qf1_on=True, qf1_off=False)
        for _ in range(2):
            outputs = avr.step(dip)
            self.assertTrue(outputs.xTargetDelayActive)
            self.assertEqual(outputs.udiRawTarget, 2)
            self.assertEqual(outputs.udiTarget, 1)
            self.assertFalse(outputs.xQ2 or outputs.xQ3)

        restored = AVRInputs(input_delay_sec=3, u1_ok=True, u2_ok=True, u3_ok=True, qf1_on=True, qf1_off=False)
        outputs = avr.step(restored)
        self.assertFalse(outputs.xTargetDelayActive)
        self.assertEqual(outputs.udiTarget, 1)
        self.assertFalse(outputs.xQ2 or outputs.xQ3)

    def test_34_sustained_input_1_loss_switches_after_delay(self):
        avr = AVR3In1()
        normal = AVRInputs(input_delay_sec=3, u1_ok=True, u2_ok=True, u3_ok=True, qf1_on=True, qf1_off=False)
        avr.step(normal)

        lost = AVRInputs(input_delay_sec=3, u1_ok=False, u2_ok=True, u3_ok=True, qf1_on=True, qf1_off=False)
        outputs = avr.step(lost)
        self.assertTrue(outputs.xTargetDelayActive)
        self.assertFalse(outputs.xQ2)

        outputs = None
        for _ in range(3):
            outputs = avr.step(lost)

        self.assertIsNotNone(outputs)
        self.assertFalse(outputs.xTargetDelayActive)
        self.assertEqual(outputs.udiTarget, 2)
        self.assertTrue(outputs.xQ2)

    def test_35_st_code_exposes_integer_delay_without_library_timer(self):
        code = (SRC_DIR / "FB_AVR_3IN1_PR200.st").read_text(encoding="utf-8")
        self.assertIn("udiInputDelaySec : UDINT", code)
        self.assertNotIn("xSecondPulse", code)
        self.assertIn("udiDelayCounterSec := udiDelayCounterSec + 1", code)
        self.assertIn("udiRawTarget", code)
        self.assertIn("xTargetDelayActive", code)
        for token in ("DelayTimer", "TON", "T#1s", "SYS.TON", "TON(", "UDINT_TO_TIME", "TIME_TO"):
            self.assertNotIn(token, code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
