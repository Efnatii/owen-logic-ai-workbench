import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from owen_logic_com_emulator import DeviceState, Emulator
from pr200_avr_runtime import AVR3In1DebugRuntime


PROJECT_DIR = Path(__file__).resolve().parent
SYMBOL_MAP = PROJECT_DIR / "pr200_reverse" / "avr3in1_debug_symbol_map.json"


def command_block_from_symbol_map() -> bytes:
    data = json.loads(SYMBOL_MAP.read_text(encoding="utf-8-sig"))
    return b"".join(int(point["word"]).to_bytes(2, "little") for point in data["debug_points"])


class AVR3In1RuntimeTests(unittest.TestCase):
    def require_symbol_map(self) -> None:
        if not SYMBOL_MAP.exists():
            self.skipTest(f"{SYMBOL_MAP} is missing")

    def make_inputs_file(self, values: dict[str, object]) -> Path:
        path = Path(tempfile.gettempdir()) / "avr3in1_runtime_inputs_test.json"
        path.write_text(json.dumps(values, indent=2), encoding="utf-8")
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return path

    def make_runtime(self, values: dict[str, object]) -> AVR3In1DebugRuntime:
        self.require_symbol_map()
        return AVR3In1DebugRuntime(SYMBOL_MAP, self.make_inputs_file(values))

    def test_priority_one_command_is_published_to_real_debug_cells(self) -> None:
        runtime = self.make_runtime(
            {
                "input_delay_sec": 3,
                "u1_ok": True,
                "u2_ok": True,
                "u3_ok": True,
                "qf1_off": True,
                "qf2_off": True,
                "qf3_off": True,
            }
        )

        runtime.update()
        runtime.update()
        values = runtime.values_for_read_points([SimpleNamespace(read_index=index) for index in range(1, 60)])

        self.assertEqual(values[5], 3)
        self.assertEqual(values[7], 1)
        self.assertEqual(values[27], 1)
        self.assertEqual(values[50], 1)
        self.assertEqual(values[29], 0)
        self.assertEqual(values[38], 31)
        self.assertEqual(values[40], 1)
        self.assertEqual(values[42], 0)

    def test_alarm_state_is_published_to_manual_alarm_debug_cells(self) -> None:
        runtime = self.make_runtime(
            {
                "input_delay_sec": 3,
                "u1_ok": True,
                "qf1_off": True,
                "qf1_fault": True,
                "qf2_off": True,
                "qf3_off": True,
            }
        )

        runtime.update()
        values = runtime.values_for_read_points([SimpleNamespace(read_index=index) for index in range(1, 60)])

        self.assertEqual(values[38], 90)
        self.assertEqual(values[40], 0)
        self.assertEqual(values[41], 1)
        self.assertEqual(values[42], 1)
        self.assertEqual(values[43], 1)
        self.assertEqual(values[27], 0)
        self.assertEqual(values[50], 0)

    def test_emulator_builds_debug_cells_from_runtime_and_symbol_map(self) -> None:
        runtime = self.make_runtime(
            {
                "input_delay_sec": 3,
                "u1_ok": True,
                "u2_ok": True,
                "u3_ok": True,
                "qf1_off": True,
                "qf2_off": True,
                "qf3_off": True,
            }
        )
        runtime.update()
        runtime.update()
        emulator = Emulator(
            DeviceState(address=16),
            PROJECT_DIR / "owen_logic_com_emulator_virtual_port.log",
            debug_runtime=runtime,
        )

        data = emulator.build_debug_read_data(command_block_from_symbol_map())

        def cell(read_index: int) -> int:
            start = (read_index - 1) * 4
            return int.from_bytes(data[start : start + 4], "little")

        self.assertEqual(cell(27), 1)
        self.assertEqual(cell(50), 1)
        self.assertEqual(cell(38), 31)
        self.assertEqual(cell(42), 0)
        self.assertEqual(cell(5), 3)

    def test_emulator_default_debug_cells_use_runtime_map_without_command_block(self) -> None:
        runtime = self.make_runtime(
            {
                "input_delay_sec": 3,
                "u1_ok": True,
                "u2_ok": True,
                "u3_ok": True,
                "qf1_off": True,
                "qf2_off": True,
                "qf3_off": True,
            }
        )
        runtime.update()
        runtime.update()
        emulator = Emulator(
            DeviceState(address=16),
            PROJECT_DIR / "owen_logic_com_emulator_virtual_port.log",
            debug_runtime=runtime,
        )

        data = emulator.build_debug_pattern_cells(59)

        def cell(read_index: int) -> int:
            start = (read_index - 1) * 4
            return int.from_bytes(data[start : start + 4], "little")

        self.assertEqual(cell(5), 3)
        self.assertEqual(cell(27), 1)
        self.assertEqual(cell(38), 31)
        self.assertEqual(cell(42), 0)

    def test_runtime_reset_id_restarts_scan_state(self) -> None:
        inputs_path = self.make_inputs_file(
            {
                "_reset_id": "a",
                "input_delay_sec": 3,
                "u1_ok": True,
                "qf1_off": True,
                "qf2_off": True,
                "qf3_off": True,
            }
        )
        self.require_symbol_map()
        runtime = AVR3In1DebugRuntime(SYMBOL_MAP, inputs_path)
        runtime.update()
        runtime.update()
        self.assertEqual(runtime.outputs.udiState, 31)

        inputs_path.write_text(
            json.dumps(
                {
                    "_reset_id": "b",
                    "input_delay_sec": 3,
                    "u1_ok": False,
                    "u2_ok": True,
                    "qf1_off": True,
                    "qf2_off": True,
                    "qf3_off": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        runtime.update()
        runtime.update()
        self.assertEqual(runtime.outputs.udiState, 32)


if __name__ == "__main__":
    unittest.main(verbosity=2)
