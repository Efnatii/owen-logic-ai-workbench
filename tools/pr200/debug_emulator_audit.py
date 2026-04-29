#!/usr/bin/env python3
"""Audit OWEN Logic online-debug values produced by the COM emulator.

This is intentionally byte-level: scenarios are written to the AVR runtime,
then the emulator is driven through real Modbus function 0x41 packets:
WriteCommandBlock, UpdateData, ReadData. The resulting 59 debug cells are
compared with the extracted symbol map.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from owen_logic_com_emulator import DeviceState, Emulator, add_crc, has_valid_crc
from pr200_avr_runtime import AVR3In1DebugRuntime, INPUT_SYMBOL_TO_FIELD


PROJECT_DIR = Path(__file__).resolve().parent
SYMBOL_MAP_PATH = PROJECT_DIR / "pr200_reverse" / "avr3in1_debug_symbol_map.json"
AUDIT_ROOT = PROJECT_DIR / "debug_emulator_audit"


BASE_INPUTS = {
    "manual_selector": False,
    "auto_return": True,
    "input_delay_sec": 3,
    "u1_ok": False,
    "u2_ok": False,
    "u3_ok": False,
    "qf1_on": False,
    "qf1_off": True,
    "qf1_fault": False,
    "qf2_on": False,
    "qf2_off": True,
    "qf2_fault": False,
    "qf3_on": False,
    "qf3_off": True,
    "qf3_fault": False,
}


@dataclass(frozen=True)
class Scenario:
    code: str
    title: str
    inputs: dict[str, Any]
    expected: dict[str, int]


SCENARIOS = [
    Scenario(
        "01",
        "priority_1_close_40f",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True},
        {"xQ1": 1, "xQ2": 0, "xQ3": 0, "xQ5": 0, "udiState": 31, "xAutoMode": 1, "xAlarm": 0},
    ),
    Scenario(
        "02",
        "active_40f_no_commands",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": False},
        {"udiActive": 1, "xQ1": 0, "xQ2": 0, "xQ3": 0, "xQ4": 0, "xQ5": 0, "xQ6": 0, "udiState": 0},
    ),
    Scenario(
        "03",
        "u1_lost_open_40f",
        {"u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": False},
        {"udiActive": 1, "udiTarget": 2, "xQ1": 0, "xQ2": 1, "xQ3": 0, "udiState": 11, "xAlarm": 0},
    ),
    Scenario(
        "04",
        "u1_lost_close_50f",
        {"u2_ok": True, "u3_ok": True},
        {"udiTarget": 2, "xQ1": 0, "xQ3": 1, "xQ4": 0, "xQ5": 0, "udiState": 32, "xAlarm": 0},
    ),
    Scenario(
        "05",
        "u1_u2_lost_close_60f",
        {"u3_ok": True},
        {"udiTarget": 3, "xQ1": 0, "xQ3": 0, "xQ5": 1, "xQ6": 0, "udiState": 33, "xAlarm": 0},
    ),
    Scenario(
        "06",
        "no_sources",
        {},
        {"udiTarget": 0, "xQ1": 0, "xQ3": 0, "xQ5": 0, "udiState": 0, "xNoSource": 1, "xAlarm": 0},
    ),
    Scenario(
        "07",
        "undefined_qf1_on_and_off",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": True},
        {"xAlarm": 1, "xAlarmUndefined": 1, "xQF1Undefined": 1, "xManualMode": 1, "xAutoMode": 0, "udiState": 90},
    ),
    Scenario(
        "08",
        "undefined_qf2_no_position",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf2_on": False, "qf2_off": False},
        {"xAlarm": 1, "xAlarmUndefined": 1, "xQF2Undefined": 1, "xManualMode": 1, "xAutoMode": 0, "udiState": 90},
    ),
    Scenario(
        "09",
        "parallel_40f_50f_only_off",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": False, "qf2_on": True, "qf2_off": False},
        {"xAlarm": 1, "xAlarmParallel": 1, "xQ1": 0, "xQ2": 1, "xQ3": 0, "xQ4": 1, "xQ5": 0, "udiState": 90},
    ),
    Scenario(
        "10",
        "qf3_fault",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf3_fault": True},
        {"xAlarm": 1, "xAlarmFault": 1, "xManualMode": 1, "xAutoMode": 0, "udiState": 90, "xQ5": 0},
    ),
    Scenario(
        "11",
        "manual_selector_blocks_auto",
        {"manual_selector": True, "u1_ok": True, "u2_ok": True, "u3_ok": True},
        {"xManualMode": 1, "xAutoMode": 0, "xAlarm": 0, "udiState": 90, "xQ1": 0, "xQ3": 0, "xQ5": 0},
    ),
]


def load_symbol_map() -> dict[str, Any]:
    return json.loads(SYMBOL_MAP_PATH.read_text(encoding="utf-8-sig"))


def command_block_from_symbol_map(symbol_map: dict[str, Any]) -> bytes:
    return b"".join(int(point["word"]).to_bytes(2, "little") for point in symbol_map["debug_points"])


def make_inputs(scenario: Scenario) -> dict[str, Any]:
    values = dict(BASE_INPUTS)
    values.update(scenario.inputs)
    values["_reset_id"] = scenario.code
    return values


def make_runtime(inputs: dict[str, Any]) -> tuple[AVR3In1DebugRuntime, Path]:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    path = Path(handle.name)
    with handle:
        json.dump(inputs, handle, indent=2)
    runtime = AVR3In1DebugRuntime(SYMBOL_MAP_PATH, path)
    return runtime, path


def modbus_41_frame(data: bytes, address: int = 16) -> bytes:
    return add_crc(bytes((address, 0x41)) + len(data).to_bytes(2, "big") + data)


def decode_read_data_response(response: bytes) -> tuple[int, dict[int, int]]:
    if not has_valid_crc(response):
        raise AssertionError("bad response CRC")
    pdu = response[:-2]
    if pdu[:2] != bytes((16, 0x41)):
        raise AssertionError(f"bad response header: {pdu[:2].hex(' ')}")
    data_len = int.from_bytes(pdu[2:4], "big")
    data = pdu[4 : 4 + data_len]
    if len(data) != data_len:
        raise AssertionError("bad response data length")
    if data[:2] != bytes((0x0D, 0x00)):
        raise AssertionError(f"bad ReadData status: {data[:2].hex(' ')}")
    block_number = data[2]
    cells = data[5:]
    if len(cells) % 4 != 0:
        raise AssertionError("debug cell payload is not 4-byte aligned")
    decoded = {
        read_index + 1: int.from_bytes(cells[read_index * 4 : read_index * 4 + 4], "little")
        for read_index in range(len(cells) // 4)
    }
    return block_number, decoded


def expected_symbol_values(runtime: AVR3In1DebugRuntime) -> dict[str, int]:
    snapshot = runtime.snapshot_by_symbol()
    by_symbol: dict[str, int] = {}
    for symbol in runtime.symbol_map["symbols"]:
        if symbol in INPUT_SYMBOL_TO_FIELD:
            by_symbol[symbol] = int(snapshot[INPUT_SYMBOL_TO_FIELD[symbol]])
        elif symbol in snapshot:
            by_symbol[symbol] = int(snapshot[symbol])
    return by_symbol


def compare_cells_to_symbols(symbol_map: dict[str, Any], cells: dict[int, int], by_symbol: dict[str, int]) -> list[str]:
    errors: list[str] = []
    for symbol, entries in symbol_map["symbols"].items():
        if symbol not in by_symbol:
            continue
        expected = by_symbol[symbol]
        for entry in entries:
            read_index = int(entry["read_index"])
            actual = cells.get(read_index)
            if actual != expected:
                errors.append(f"{symbol}@{read_index}: expected {expected}, got {actual}")
    return errors


def assert_scenario_expectations(symbol_map: dict[str, Any], cells: dict[int, int], scenario: Scenario) -> list[str]:
    errors: list[str] = []
    for symbol, expected in scenario.expected.items():
        for entry in symbol_map["symbols"][symbol]:
            read_index = int(entry["read_index"])
            actual = cells.get(read_index)
            if actual != expected:
                errors.append(f"{scenario.code} {symbol}@{read_index}: expected {expected}, got {actual}")
    return errors


def run_packet_audit(scenario: Scenario) -> dict[str, Any]:
    symbol_map = load_symbol_map()
    command_block = command_block_from_symbol_map(symbol_map)
    runtime, inputs_path = make_runtime(make_inputs(scenario))
    try:
        emulator = Emulator(
            DeviceState(address=16, program_hash=int(str(symbol_map["program_hash"]), 0)),
            PROJECT_DIR / "debug_emulator_audit.tmp.log",
            debug_runtime=runtime,
        )

        write_data = bytes((0x09, 0x00, 0x00, 0x01)) + command_block
        write_response = emulator.handle_frame(modbus_41_frame(write_data))
        if write_response is None or not has_valid_crc(write_response):
            raise AssertionError("WriteCommandBlock response is missing or has bad CRC")

        for _ in range(3):
            update_response = emulator.handle_frame(modbus_41_frame(bytes((0x0B,))))
            if update_response is None or not has_valid_crc(update_response):
                raise AssertionError("UpdateData response is missing or has bad CRC")

        read_response = emulator.handle_frame(modbus_41_frame(bytes((0x0D,))))
        if read_response is None:
            raise AssertionError("ReadData response is missing")
        block_number, packet_cells = decode_read_data_response(read_response)

        default_data = emulator.build_debug_pattern_cells(int(symbol_map["debug_point_count"]))
        default_cells = {
            read_index + 1: int.from_bytes(default_data[read_index * 4 : read_index * 4 + 4], "little")
            for read_index in range(len(default_data) // 4)
        }

        by_symbol = expected_symbol_values(runtime)
        packet_errors = compare_cells_to_symbols(symbol_map, packet_cells, by_symbol)
        default_errors = compare_cells_to_symbols(symbol_map, default_cells, by_symbol)
        scenario_errors = assert_scenario_expectations(symbol_map, packet_cells, scenario)
        duplicate_errors = []
        for symbol in ("xQ1", "xQ2", "xQ3", "xQ4", "xQ5", "xQ6"):
            values = [packet_cells[int(entry["read_index"])] for entry in symbol_map["symbols"][symbol]]
            if len(set(values)) != 1:
                duplicate_errors.append(f"{symbol} duplicate mismatch: {values}")

        key_symbols = sorted(set(scenario.expected) | {"udiState", "xAlarm", "xAutoMode", "xManualMode"})
        observed = {}
        for symbol in key_symbols:
            if symbol in symbol_map["symbols"]:
                observed[symbol] = [
                    packet_cells[int(entry["read_index"])]
                    for entry in symbol_map["symbols"][symbol]
                ]

        all_errors = packet_errors + default_errors + scenario_errors + duplicate_errors
        return {
            "scenario": scenario.code,
            "title": scenario.title,
            "ok": not all_errors,
            "block_number": block_number,
            "cell_count": len(packet_cells),
            "packet_crc_ok": has_valid_crc(read_response),
            "write_crc_ok": has_valid_crc(write_response),
            "errors": all_errors,
            "observed": observed,
        }
    finally:
        inputs_path.unlink(missing_ok=True)


def write_report(results: list[dict[str, Any]]) -> Path:
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = AUDIT_ROOT / f"EMULATOR_DEBUG_POINTS_AUDIT_{stamp}.md"
    lines = [
        "# Emulator Debug Points Audit",
        "",
        f"Started: {datetime.now().isoformat(timespec='seconds')}",
        f"Symbol map: `{SYMBOL_MAP_PATH}`",
        "",
        "This audit drives the emulator through real Modbus function `0x41` packets and decodes the returned `ReadData` cells.",
        "",
        "| # | Scenario | Result | Cells | Block | CRC | Observed key values |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for result in results:
        status = "OK" if result["ok"] else "FAIL"
        crc = "OK" if result["packet_crc_ok"] and result["write_crc_ok"] else "FAIL"
        lines.append(
            f"| {result['scenario']} | `{result['title']}` | {status} | {result['cell_count']} | "
            f"{result['block_number']} | {crc} | `{json.dumps(result['observed'], ensure_ascii=False)}` |"
        )
        if result["errors"]:
            for error in result["errors"]:
                lines.append(f"| {result['scenario']} | error | FAIL |  |  |  | `{error}` |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    results = [run_packet_audit(scenario) for scenario in SCENARIOS]
    report_path = write_report(results)
    failed = [result for result in results if not result["ok"]]
    print(json.dumps({"ok": not failed, "scenarios": len(results), "failed": len(failed), "report": str(report_path)}, ensure_ascii=False, indent=2))
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
