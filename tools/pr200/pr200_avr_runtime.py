#!/usr/bin/env python3
"""AVR 3-in-1 runtime adapter for OWEN Logic online-debug emulation.

The real PR200 upload image does not carry user symbol names. The adapter uses
the extracted online-debug symbol map to publish values into the same read cells
that OWEN Logic requested from the controller.
"""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from avr_3in1_sim import AVR3In1, AVRInputs, AVROutputs


INPUT_SYMBOL_TO_FIELD = {
    "xManualSelector": "manual_selector",
    "xAutoReturn": "auto_return",
    "udiInputDelaySec": "input_delay_sec",
    "xU1Ok": "u1_ok",
    "xU2Ok": "u2_ok",
    "xU3Ok": "u3_ok",
    "xQF1On": "qf1_on",
    "xQF1Off": "qf1_off",
    "xQF1Fault": "qf1_fault",
    "xQF2On": "qf2_on",
    "xQF2Off": "qf2_off",
    "xQF2Fault": "qf2_fault",
    "xQF3On": "qf3_on",
    "xQF3Off": "qf3_off",
    "xQF3Fault": "qf3_fault",
}


class AVR3In1DebugRuntime:
    """Execute the AVR model and expose values by OWEN debug read index."""

    def __init__(self, symbol_map_path: Path, inputs_path: Path | None = None) -> None:
        self.symbol_map_path = symbol_map_path
        self.inputs_path = inputs_path
        self.symbol_map = json.loads(symbol_map_path.read_text(encoding="utf-8-sig"))
        self.avr = AVR3In1()
        self.reset_id = self.load_reset_id()
        self.inputs = self.load_inputs()
        self.outputs = AVROutputs()
        self.scan_count = 0

    def load_config(self) -> dict[str, Any]:
        if self.inputs_path is None or not self.inputs_path.exists():
            return {}
        loaded = json.loads(self.inputs_path.read_text(encoding="utf-8-sig"))
        if not isinstance(loaded, dict):
            raise ValueError(f"{self.inputs_path} must contain a JSON object")
        return loaded

    def load_reset_id(self) -> str:
        return str(self.load_config().get("_reset_id", ""))

    def load_inputs(self) -> AVRInputs:
        defaults = asdict(AVRInputs())
        for key, value in self.load_config().items():
            if key not in defaults:
                continue
            defaults[key] = self.coerce_value(value, type(defaults[key]))
        return AVRInputs(**defaults)

    @staticmethod
    def coerce_value(value: Any, target_type: type) -> Any:
        if target_type is bool:
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)
        if target_type is int:
            return int(value)
        return value

    def update(self) -> None:
        reset_id = self.load_reset_id()
        if reset_id != self.reset_id:
            self.avr = AVR3In1()
            self.outputs = AVROutputs()
            self.scan_count = 0
            self.reset_id = reset_id
        self.inputs = self.load_inputs()
        self.outputs = self.avr.step(self.inputs)
        self.scan_count += 1

    def values_by_read_index(self) -> dict[int, int]:
        input_values = asdict(self.inputs)
        output_values = asdict(self.outputs)
        values: dict[int, int] = {}

        for symbol, entries in self.symbol_map.get("symbols", {}).items():
            if symbol in INPUT_SYMBOL_TO_FIELD:
                raw_value = input_values[INPUT_SYMBOL_TO_FIELD[symbol]]
            elif symbol in output_values:
                raw_value = output_values[symbol]
            else:
                continue
            value = int(raw_value)
            for entry in entries:
                values[int(entry["read_index"])] = value
        return values

    def values_for_read_points(self, read_points: list[Any]) -> dict[int, int]:
        all_values = self.values_by_read_index()
        return {
            int(point.read_index): all_values[int(point.read_index)]
            for point in read_points
            if int(point.read_index) in all_values
        }

    def snapshot_by_symbol(self) -> dict[str, int]:
        input_values = asdict(self.inputs)
        output_values = asdict(self.outputs)
        snapshot: dict[str, int] = {}
        for field in fields(AVRInputs):
            snapshot[field.name] = int(input_values[field.name])
        for field in fields(AVROutputs):
            snapshot[field.name] = int(output_values[field.name])
        snapshot["scan_count"] = self.scan_count
        return snapshot
