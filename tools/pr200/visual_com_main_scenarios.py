#!/usr/bin/env python3
"""Run a short visual COM test set for the AVR 3-in-1 OWEN Logic project."""

from __future__ import annotations

import json
import re
import time
import ctypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import ImageGrab


PROJECT_DIR = Path(__file__).resolve().parent
INPUTS_PATH = PROJECT_DIR / "pr200_reverse" / "avr3in1_live_inputs.json"
SYMBOL_MAP_PATH = PROJECT_DIR / "pr200_reverse" / "avr3in1_debug_symbol_map.json"
COM_LOG_PATH = PROJECT_DIR / "owen_logic_com_emulator_COM22_runtime.stdout.log"
FBD_TAB_RELATIVE_X = 595
FBD_TAB_RELATIVE_Y = 58


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

    @property
    def filename_slug(self) -> str:
        text = f"{self.code}_{self.title}"
        text = text.replace("40F", "40F").replace("50F", "50F").replace("60F", "60F")
        return re.sub(r"[^A-Za-z0-9А-Яа-я_]+", "_", text).strip("_")


SCENARIOS = [
    Scenario(
        "01",
        "AUTO_PRIORITY_1_CLOSE_40F_Q1_STATE31",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True},
        {"udiInputDelaySec": 3, "xQ1": 1, "xQ2": 0, "xQ3": 0, "xQ5": 0, "udiState": 31, "xAutoMode": 1, "xAlarm": 0},
    ),
    Scenario(
        "02",
        "ACTIVE_40F_HEALTHY_NO_COMMANDS",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": False},
        {"udiActive": 1, "xQ1": 0, "xQ2": 0, "xQ3": 0, "xQ4": 0, "xQ5": 0, "xQ6": 0, "udiState": 0, "xAlarm": 0},
    ),
    Scenario(
        "03",
        "U1_LOST_ACTIVE_40F_OPEN_40F_Q2_STATE11",
        {"u1_ok": False, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": False},
        {"udiActive": 1, "udiTarget": 2, "xQ1": 0, "xQ2": 1, "xQ3": 0, "udiState": 11, "xAlarm": 0},
    ),
    Scenario(
        "04",
        "U1_LOST_ALL_OFF_CLOSE_50F_Q3_STATE32",
        {"u1_ok": False, "u2_ok": True, "u3_ok": True},
        {"udiTarget": 2, "xQ1": 0, "xQ2": 0, "xQ3": 1, "xQ4": 0, "xQ5": 0, "udiState": 32, "xAlarm": 0},
    ),
    Scenario(
        "05",
        "U1_U2_LOST_ALL_OFF_CLOSE_60F_Q5_STATE33",
        {"u1_ok": False, "u2_ok": False, "u3_ok": True},
        {"udiTarget": 3, "xQ1": 0, "xQ3": 0, "xQ5": 1, "xQ6": 0, "udiState": 33, "xAlarm": 0},
    ),
    Scenario(
        "06",
        "NO_SOURCES_ALL_OFF_NO_SOURCE",
        {"u1_ok": False, "u2_ok": False, "u3_ok": False},
        {"udiTarget": 0, "xQ1": 0, "xQ3": 0, "xQ5": 0, "udiState": 0, "xNoSource": 1, "xAlarm": 0},
    ),
    Scenario(
        "07",
        "UNDEFINED_QF1_ON_AND_OFF_ALARM",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": True},
        {"xAlarm": 1, "xAlarmUndefined": 1, "xQF1Undefined": 1, "xManualMode": 1, "xAutoMode": 0, "udiState": 90, "xQ1": 0},
    ),
    Scenario(
        "08",
        "UNDEFINED_QF2_NO_POSITION_ALARM",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf2_on": False, "qf2_off": False},
        {"xAlarm": 1, "xAlarmUndefined": 1, "xQF2Undefined": 1, "xManualMode": 1, "xAutoMode": 0, "udiState": 90, "xQ3": 0},
    ),
    Scenario(
        "09",
        "PARALLEL_40F_50F_ONLY_OFF_COMMANDS",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf1_on": True, "qf1_off": False, "qf2_on": True, "qf2_off": False},
        {"xAlarm": 1, "xAlarmParallel": 1, "xQ1": 0, "xQ2": 1, "xQ3": 0, "xQ4": 1, "xQ5": 0, "udiState": 90},
    ),
    Scenario(
        "10",
        "BREAKER_FAULT_QF3_MANUAL_ALARM",
        {"u1_ok": True, "u2_ok": True, "u3_ok": True, "qf3_fault": True},
        {"xAlarm": 1, "xAlarmFault": 1, "xManualMode": 1, "xAutoMode": 0, "udiState": 90, "xQ5": 0},
    ),
    Scenario(
        "11",
        "MANUAL_SELECTOR_BLOCKS_AUTO",
        {"manual_selector": True, "u1_ok": True, "u2_ok": True, "u3_ok": True},
        {"xManualMode": 1, "xAutoMode": 0, "xAlarm": 0, "udiState": 90, "xQ1": 0, "xQ3": 0, "xQ5": 0},
    ),
]


def load_symbol_map() -> dict[str, Any]:
    return json.loads(SYMBOL_MAP_PATH.read_text(encoding="utf-8-sig"))


def symbol_read_indices(symbol_map: dict[str, Any], symbol: str) -> list[int]:
    return [int(entry["read_index"]) for entry in symbol_map["symbols"][symbol]]


def write_inputs(scenario: Scenario) -> None:
    data = dict(BASE_INPUTS)
    data.update(scenario.inputs)
    data["_reset_id"] = f"{scenario.code}_{time.time_ns()}"
    INPUTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_read_data_frame(record: dict[str, Any]) -> dict[int, int] | None:
    if record.get("event") != "frame" or record.get("rx") != "10 41 00 01 0d 31 aa":
        return None
    try:
        raw = bytes.fromhex(record["tx"])
    except (KeyError, TypeError, ValueError):
        return None
    if len(raw) < 11:
        return None
    body = raw[4:-2]
    if len(body) < 5:
        return None
    cells = body[5:]
    return {
        read_index + 1: int.from_bytes(cells[read_index * 4 : read_index * 4 + 4], "little")
        for read_index in range(len(cells) // 4)
    }


def expected_matches(cells: dict[int, int], symbol_map: dict[str, Any], expected: dict[str, int]) -> bool:
    for symbol, value in expected.items():
        for read_index in symbol_read_indices(symbol_map, symbol):
            if cells.get(read_index) != int(value):
                return False
    return True


def wait_for_expected_com_values(scenario: Scenario, symbol_map: dict[str, Any], timeout_sec: float = 18.0) -> dict[int, int]:
    start_size = COM_LOG_PATH.stat().st_size if COM_LOG_PATH.exists() else 0
    deadline = time.time() + timeout_sec
    offset = start_size
    last_cells: dict[int, int] = {}
    while time.time() < deadline:
        if COM_LOG_PATH.exists():
            with COM_LOG_PATH.open("r", encoding="utf-8", errors="ignore") as handle:
                handle.seek(offset)
                chunk = handle.read()
                offset = handle.tell()
            for line in chunk.splitlines():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cells = parse_read_data_frame(record)
                if cells is None:
                    continue
                last_cells = cells
                if expected_matches(cells, symbol_map, scenario.expected):
                    return cells
        time.sleep(0.15)
    raise TimeoutError(f"COM values did not match scenario {scenario.code}: last={last_cells}")


class Rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def find_owen_avr3_window() -> int:
    user32 = ctypes.windll.user32
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    found: list[int] = []

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value
        if title.startswith("Owen Logic - ") and "3 " in title and "секционир" not in title:
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(enum_proc(callback), 0)
    if not found:
        raise RuntimeError("OWEN Logic AVR 3-in-1 window was not found")
    return found[0]


def activate_fbd_tab_and_get_rect() -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    hwnd = find_owen_avr3_window()
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.25)
    rect = Rect()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    user32.SetCursorPos(rect.left + FBD_TAB_RELATIVE_X, rect.top + FBD_TAB_RELATIVE_Y)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.55)
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def capture_window(output_path: Path) -> None:
    left, top, right, bottom = activate_fbd_tab_and_get_rect()
    image = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    image.save(output_path)


def make_observed_by_symbol(cells: dict[int, int], symbol_map: dict[str, Any], expected: dict[str, int]) -> dict[str, list[int]]:
    observed: dict[str, list[int]] = {}
    for symbol in expected:
        observed[symbol] = [cells[index] for index in symbol_read_indices(symbol_map, symbol)]
    return observed


def main() -> int:
    symbol_map = load_symbol_map()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = PROJECT_DIR / f"visual_com_main_scenarios_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[str] = [
        "# Visual COM Main Scenario Test",
        "",
        f"Started: {datetime.now().isoformat(timespec='seconds')}",
        f"Input file: `{INPUTS_PATH}`",
        f"COM log: `{COM_LOG_PATH}`",
        "",
        "| # | Scenario | Result | Screenshot | Observed |",
        "|---|---|---|---|---|",
    ]

    for scenario in SCENARIOS:
        write_inputs(scenario)
        cells = wait_for_expected_com_values(scenario, symbol_map)
        screenshot = out_dir / f"{scenario.filename_slug}.png"
        capture_window(screenshot)
        observed = make_observed_by_symbol(cells, symbol_map, scenario.expected)
        rows.append(
            f"| {scenario.code} | `{scenario.title}` | OK | `{screenshot.name}` | `{json.dumps(observed, ensure_ascii=False)}` |"
        )
        print(f"OK {scenario.code}: {scenario.title} -> {screenshot}")

    report_path = out_dir / "VISUAL_COM_MAIN_SCENARIOS_REPORT.md"
    report_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
