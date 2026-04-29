import unittest

from debug_emulator_audit import SCENARIOS, run_packet_audit


class DebugEmulatorAuditTests(unittest.TestCase):
    def test_all_main_scenarios_match_runtime_symbol_map_and_modbus_packet(self) -> None:
        failures: list[str] = []
        for scenario in SCENARIOS:
            result = run_packet_audit(scenario)
            if not result["ok"]:
                failures.extend(result["errors"])
            self.assertEqual(result["cell_count"], 59)
            self.assertTrue(result["packet_crc_ok"])
            self.assertTrue(result["write_crc_ok"])
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
