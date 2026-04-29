import unittest
from pathlib import Path

from pr200_debug_extract import (
    infer_avr3in1_symbol_map,
    latest_debug_command_block_from_log,
    reconstruct_program_from_log,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIVE_LOG = PROJECT_DIR / "owen_logic_com_emulator_COM22_live.log"
OWLE_PROJECT = Path(
    r"C:\Users\Alexandra\YandexDisk-egory.forward\2 В РАБОТУ 2020\0091-0821 СТРОЙПРОМТОРГ ООО Восточный (0254)\2 РАБОЧАЯ\0091-0821 Щитовуха\0091-0821 ГРЩ корпус 17\АВР на 3 ввода feat. Егор Гороховицкий.owle"
)


class PR200DebugExtractTests(unittest.TestCase):
    def require_live_artifacts(self) -> None:
        if not LIVE_LOG.exists():
            self.skipTest(f"{LIVE_LOG} is missing")
        if not OWLE_PROJECT.exists():
            self.skipTest(f"{OWLE_PROJECT} is missing")

    def test_reconstructs_uploaded_program_image_from_real_com_log(self) -> None:
        self.require_live_artifacts()

        program, image = reconstruct_program_from_log(LIVE_LOG)

        self.assertEqual(len(image), 10856)
        self.assertEqual(program.size, 10856)
        self.assertEqual(program.program_hash, 0xA1A91428)

    def test_extracts_latest_online_debug_command_block(self) -> None:
        self.require_live_artifacts()

        command = latest_debug_command_block_from_log(LIVE_LOG)
        ids = [point.stack_instruction_id for point in command.read_points]

        self.assertGreaterEqual(command.block_number, 1)
        self.assertEqual(len(ids), 59)
        self.assertEqual(ids[:5], [1, 3, 5, 6, 7])
        self.assertEqual(ids[26:32], [70, 73, 76, 79, 82, 85])
        self.assertEqual(ids[37], 103)
        self.assertEqual(ids[41], 115)

    def test_maps_owen_debug_points_to_avr3in1_symbols(self) -> None:
        self.require_live_artifacts()

        program, _ = reconstruct_program_from_log(LIVE_LOG)
        command = latest_debug_command_block_from_log(LIVE_LOG)
        symbol_map = infer_avr3in1_symbol_map(OWLE_PROJECT, command, program)
        symbols = symbol_map["symbols"]

        self.assertEqual([entry["read_index"] for entry in symbols["xQ1"]], [27, 50])
        self.assertEqual([entry["read_index"] for entry in symbols["xQ6"]], [32, 55])
        self.assertEqual(symbols["udiState"][0]["read_index"], 38)
        self.assertEqual(symbols["xAlarm"][0]["read_index"], 42)
        self.assertEqual(symbols["xNoSource"][0]["read_index"], 49)
        self.assertEqual(symbols["xManualSelector"][0]["read_index"], 3)
        self.assertTrue(all(entry["confidence"] == "high" for entry in symbols["xQ1"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
