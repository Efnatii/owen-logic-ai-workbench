#!/usr/bin/env python3
"""Extract PR200 program and OWEN Logic online-debug read points.

The PR200 binary uploaded by OWEN Logic does not contain human-readable signal
names. The stable bridge between a visible FBD value box and the emulator is the
online-debug command block: each ProgramStackReadingCommand names a stack
instruction id. This module reconstructs that list and combines it with the
project's function-block metadata when a project file is available.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

OWEN_NIBBLE_BASE = ord("G")
DEFAULT_STARTING_ADDRESS = 131072


@dataclass(frozen=True)
class DebugReadPoint:
    read_index: int
    command_offset: int
    word: int
    stack_instruction_id: int


@dataclass(frozen=True)
class DebugCommandBlock:
    block_number: int
    command_block: bytes
    read_points: list[DebugReadPoint]


@dataclass(frozen=True)
class ProgramImage:
    starting_address: int
    size: int
    program_hash: int
    bytes_hex_sha_hint: str


def decode_owen_nibbles(encoded: bytes, terminator: int) -> bytes:
    if not encoded or encoded[-1] != terminator:
        raise ValueError("bad owen nibble terminator")
    payload = encoded[:-1]
    if len(payload) % 2 != 0:
        raise ValueError("odd owen nibble payload")
    raw = bytearray()
    for index in range(0, len(payload), 2):
        high = payload[index] - OWEN_NIBBLE_BASE
        low = payload[index + 1] - OWEN_NIBBLE_BASE
        if high < 0 or high > 15 or low < 0 or low > 15:
            raise ValueError("bad owen nibble")
        raw.append((high << 4) | low)
    return bytes(raw)


def iter_log_frames(log_path: Path) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("event") == "frame":
            frames.append(record)
    return frames


def bytes_from_hex_log(value: str) -> bytes:
    return bytes(int(part, 16) for part in value.split())


def reconstruct_program_from_log(
    log_path: Path,
    output_path: Path | None = None,
    starting_address: int = DEFAULT_STARTING_ADDRESS,
) -> tuple[ProgramImage, bytes]:
    memory = bytearray()
    for frame in iter_log_frames(log_path):
        rx = frame.get("rx") or ""
        if not rx:
            continue
        try:
            encoded = bytes_from_hex_log(rx)
        except ValueError:
            continue
        if not encoded or not (OWEN_NIBBLE_BASE <= encoded[0] <= OWEN_NIBBLE_BASE + 15) or not encoded.endswith(b"\n"):
            continue
        try:
            raw = decode_owen_nibbles(encoded, 10)
        except ValueError:
            continue
        if len(raw) < 18:
            continue
        block_count = raw[0]
        address = int.from_bytes(raw[2:6], "little", signed=False)
        data_len = block_count * 8
        if data_len <= 0 or len(raw) < 14 + data_len:
            continue
        offset = address - starting_address
        if offset < 0:
            continue
        if len(memory) < offset + data_len:
            memory.extend(b"\xFF" * (offset + data_len - len(memory)))
        memory[offset : offset + data_len] = raw[14 : 14 + data_len]

    program_hash = int.from_bytes(memory[8:12], "little", signed=False) if len(memory) >= 12 else 0
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(memory)
    image = ProgramImage(
        starting_address=starting_address,
        size=len(memory),
        program_hash=program_hash,
        bytes_hex_sha_hint=memory[:32].hex(" "),
    )
    return image, bytes(memory)


def parse_debug_command_block(command_block: bytes) -> list[DebugReadPoint]:
    points: list[DebugReadPoint] = []
    index = 0
    read_index = 1
    while index + 1 < len(command_block):
        offset = index
        word = command_block[index] | (command_block[index + 1] << 8)
        index += 2
        if word & 1:
            points.append(
                DebugReadPoint(
                    read_index=read_index,
                    command_offset=offset,
                    word=word,
                    stack_instruction_id=word >> 1,
                )
            )
            read_index += 1
            continue

        if index >= len(command_block):
            break
        command_code = command_block[index]
        if command_code in (0xC0, 0xE0) or (command_code & 0xE0) in (0xC0, 0xE0):
            index += 5
        elif command_code == 0xA0:
            index += 1
        else:
            index += 1
    return points


def latest_debug_command_block_from_log(log_path: Path) -> DebugCommandBlock:
    current_block = 0
    current = bytearray()
    seen = False
    for frame in iter_log_frames(log_path):
        rx = frame.get("rx") or ""
        if not rx.startswith("10 41"):
            continue
        try:
            pdu = bytes_from_hex_log(rx)
        except ValueError:
            continue
        if len(pdu) < 8:
            continue
        data_len = (pdu[2] << 8) | pdu[3]
        data = pdu[4 : 4 + data_len]
        if len(data) != data_len or not data:
            continue
        command_number = data[0] >> 1
        if command_number != 4 or len(data) < 4:
            continue
        offset = int.from_bytes(data[1:3], "little", signed=False)
        block_number = data[3]
        chunk = data[4:]
        if block_number != current_block or offset == 0:
            current = bytearray()
        current_block = block_number
        required = offset + len(chunk)
        if len(current) < required:
            current.extend(b"\x00" * (required - len(current)))
        current[offset:required] = chunk
        seen = True
    if not seen:
        raise ValueError(f"no online-debug command block writes found in {log_path}")
    command_block = bytes(current)
    return DebugCommandBlock(current_block, command_block, parse_debug_command_block(command_block))


def read_owle_member(owle_path: Path, name: str) -> Any:
    with zipfile.ZipFile(owle_path) as archive:
        return json.loads(archive.read(name).decode("utf-8-sig"))


def extract_function_block_catalog(owle_path: Path, fb_name: str) -> dict[str, Any]:
    blocks = read_owle_member(owle_path, "StFunctionBlocks")
    for block in blocks:
        if block.get("Name") == fb_name:
            return block
    raise ValueError(f"function block {fb_name!r} not found")


def extract_fb_instance_from_project(owle_path: Path, fb_name: str) -> dict[str, Any]:
    project = read_owle_member(owle_path, "Project")
    for document in project.values():
        doc_model = document.get("DocumentModel", {})
        for element in doc_model.get("Elements", []):
            if element.get("Discriminator") == 41 and element.get("Name") == fb_name:
                return element
    raise ValueError(f"function block instance {fb_name!r} not found")


def find_stride_run(points: list[DebugReadPoint], length: int, stride: int) -> int:
    for start in range(0, len(points) - length + 1):
        first = points[start].stack_instruction_id
        if all(points[start + offset].stack_instruction_id == first + stride * offset for offset in range(length)):
            return start
    raise ValueError(f"no stride-{stride} run with length {length}")


def infer_avr3in1_symbol_map(
    owle_path: Path,
    command: DebugCommandBlock,
    program: ProgramImage | None = None,
    fb_name: str = "FB_AVR_3IN1_PR200",
) -> dict[str, Any]:
    catalog = extract_function_block_catalog(owle_path, fb_name)
    instance = extract_fb_instance_from_project(owle_path, fb_name)
    input_names = list(catalog["InputNames"])
    output_names = list(catalog["OutputNames"])
    points = command.read_points

    output_start = find_stride_run(points, len(output_names), 3)
    symbols: dict[str, list[dict[str, Any]]] = {}

    def add(symbol: str, point: DebugReadPoint, role: str, confidence: str) -> None:
        symbols.setdefault(symbol, []).append(
            {
                "read_index": point.read_index,
                "stack_instruction_id": point.stack_instruction_id,
                "word": point.word,
                "role": role,
                "confidence": confidence,
            }
        )

    # The output run is generated by OWEN Logic as one contiguous stride-3 run
    # for this ST function-block instance. This is the strongest automatic
    # mapping available without reverse-engineering the full PR200 bytecode VM.
    for offset, name in enumerate(output_names):
        add(name, points[output_start + offset], "fb_output", "high")

    # Physical output variable blocks immediately after the function-block
    # outputs duplicate the first six motor commands.
    for offset, name in enumerate(output_names[:6]):
        duplicate_index = output_start + len(output_names) + offset
        if duplicate_index < len(points):
            add(name, points[duplicate_index], "physical_output_duplicate", "high")

    # Input terminals are not encoded with names in the program/debug block.
    # For this generated AVR project their terminal read boxes are stable and
    # are verified by the extracted FBD port order. If the project shape changes
    # the extractor refuses to claim high-confidence input mapping.
    expected_inputs = [
        "xManualSelector",
        "xAutoReturn",
        "udiInputDelaySec",
        "xU1Ok",
        "xU2Ok",
        "xU3Ok",
        "xQF1On",
        "xQF1Off",
        "xQF1Fault",
        "xQF2On",
        "xQF2Off",
        "xQF2Fault",
        "xQF3On",
        "xQF3Off",
        "xQF3Fault",
    ]
    terminal_indices = [3, 4, 5, 7, 9, 11, 14, 15, 16, 19, 20, 21, 24, 25, 26]
    input_confidence = "high" if input_names == expected_inputs and output_start == 26 else "low"
    if input_confidence == "high":
        for name, read_index in zip(input_names, terminal_indices):
            add(name, points[read_index - 1], "fb_input_terminal", "high")

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "program_hash": f"0x{program.program_hash:08X}" if program is not None else None,
        "program_size": program.size if program is not None else None,
        "debug_block_number": command.block_number,
        "debug_point_count": len(points),
        "fb_name": fb_name,
        "fb_instance_unique_id": instance["ElementBlockStoreModel"]["ElementModel"]["UniqueId"],
        "input_names": input_names,
        "output_names": output_names,
        "debug_points": [asdict(point) for point in points],
        "symbols": symbols,
        "notes": [
            "Program binary contains stack instructions but no human-readable signal names.",
            "stack_instruction_id values are extracted from the real OWEN Logic online-debug command block.",
            "Function-block output symbols are inferred from the contiguous stride-3 output run in the command block.",
            "Input terminal symbols are high-confidence only for the current AVR_3IN1 project shape.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract PR200 program image and online-debug symbol map")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--owle", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--fb-name", default="FB_AVR_3IN1_PR200")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    program, _ = reconstruct_program_from_log(args.log, args.out_dir / "program_from_log.bin")
    command = latest_debug_command_block_from_log(args.log)
    (args.out_dir / "debug_command_block.bin").write_bytes(command.command_block)
    symbol_map = infer_avr3in1_symbol_map(args.owle, command, program, args.fb_name)
    (args.out_dir / "avr3in1_debug_symbol_map.json").write_text(
        json.dumps(symbol_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "program_hash": f"0x{program.program_hash:08X}",
        "program_size": program.size,
        "debug_points": len(command.read_points),
        "symbol_map": str(args.out_dir / "avr3in1_debug_symbol_map.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
