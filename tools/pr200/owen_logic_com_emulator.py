#!/usr/bin/env python3
"""Read/write-safe COM emulator for OWEN Logic experiments.

This script emulates a simple Modbus RTU slave. It is intended to be attached
to one side of a virtual null-modem pair while OWEN Logic opens the other side.

Example:
  python owen_logic_com_emulator.py --port COM14 --address 16 --baudrate 9600

Then configure OWEN Logic to use the paired port, for example COM13.
"""

from __future__ import annotations

import argparse
import ast
import json
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import serial
from serial.tools import list_ports


DEFAULT_LOG = Path(__file__).with_name("owen_logic_com_emulator.log")


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def add_crc(payload: bytes) -> bytes:
    crc = crc16_modbus(payload)
    return payload + bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def has_valid_crc(frame: bytes) -> bool:
    if len(frame) < 4:
        return False
    expected = frame[-2] | (frame[-1] << 8)
    actual = crc16_modbus(frame[:-2])
    return expected == actual


def u16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, "big")


def get_u16(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def pack_bits(values: list[bool]) -> bytes:
    packed = bytearray((len(values) + 7) // 8)
    for index, value in enumerate(values):
        if value:
            packed[index // 8] |= 1 << (index % 8)
    return bytes(packed)


def pack_registers(values: list[int]) -> bytes:
    return b"".join(u16(value) for value in values)


def encode_owen_modbus_string(value: str, register_count: int = 16, encoding: str = "cp1251") -> list[int]:
    """Encode a string exactly as OWEN Logic reads service Modbus strings.

    OWEN Logic converts each 16-bit Modbus register back to bytes with
    little-endian BitConverter.GetBytes(ushort), so every byte pair must be
    reversed inside the register value.
    """
    byte_count = register_count * 2
    raw = value.encode(encoding, errors="replace")[:byte_count]
    raw = raw + (b"\x00" * (byte_count - len(raw)))
    return [raw[index] | (raw[index + 1] << 8) for index in range(0, byte_count, 2)]


OWEN_NIBBLE_BASE = ord("G")


def owen_protocol_crc(data: list[int] | bytes, size: int | None = None) -> int:
    if size is None:
        size = len(data)
    crc = 0
    for index in range(size):
        crc = owen_protocol_hash_byte(int(data[index]), 8, crc)
    return crc & 0xFFFF


def owen_protocol_hash_byte(value: int, nbit: int, crc: int) -> int:
    value &= 0xFF
    crc &= 0xFFFF
    for _ in range(nbit):
        if ((value ^ (crc >> 8)) & 0x80) == 0x80:
            crc = ((crc << 1) & 0xFFFF) ^ 0x8F57
        else:
            crc = (crc << 1) & 0xFFFF
        value = (value << 1) & 0xFF
    return crc & 0xFFFF


def owen_parameter_hash(name: str) -> int:
    values = [78, 78, 78, 78, 0]
    out_index = 0
    for in_index, char in enumerate(name.upper()):
        if out_index > 4:
            break
        if char == "." and in_index > 0:
            values[out_index - 1] += 1
        elif char == " ":
            values[out_index] = 78
            out_index += 1
        elif char == "_":
            values[out_index] = 74
            out_index += 1
        elif char == "-":
            values[out_index] = 72
            out_index += 1
        elif char.isalpha():
            values[out_index] = 2 * (ord(char) - ord("A") + 10)
            out_index += 1
        elif char.isdigit():
            values[out_index] = 2 * (ord(char) - ord("0"))
            out_index += 1
    return owen_protocol_hash_byte(
        (values[3] << 1) & 0xFF,
        7,
        owen_protocol_hash_byte(
            (values[2] << 1) & 0xFF,
            7,
            owen_protocol_hash_byte(
                (values[1] << 1) & 0xFF,
                7,
                owen_protocol_hash_byte((values[0] << 1) & 0xFF, 7, 0),
            ),
        ),
    )


def encode_owen_protocol(raw: bytes | bytearray | list[int]) -> bytes:
    encoded = bytearray(b"#")
    for value in raw:
        encoded.append(((int(value) >> 4) & 0x0F) + OWEN_NIBBLE_BASE)
        encoded.append((int(value) & 0x0F) + OWEN_NIBBLE_BASE)
    encoded.append(13)
    return bytes(encoded)


def encode_owen_nibbles(raw: bytes | bytearray | list[int], terminator: int) -> bytes:
    encoded = bytearray()
    for value in raw:
        encoded.append(((int(value) >> 4) & 0x0F) + OWEN_NIBBLE_BASE)
        encoded.append((int(value) & 0x0F) + OWEN_NIBBLE_BASE)
    encoded.append(terminator)
    return bytes(encoded)


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


def decode_owen_protocol(frame: bytes) -> bytes:
    if len(frame) < 4 or frame[0] != ord("#") or frame[-1] != 13:
        raise ValueError("bad owen ascii frame")
    encoded = frame[1:-1]
    if len(encoded) % 2 != 0:
        raise ValueError("odd owen ascii payload")
    raw = bytearray()
    for index in range(0, len(encoded), 2):
        high = encoded[index] - OWEN_NIBBLE_BASE
        low = encoded[index + 1] - OWEN_NIBBLE_BASE
        if high < 0 or high > 15 or low < 0 or low > 15:
            raise ValueError("bad owen ascii nibble")
        raw.append((high << 4) | low)
    if len(raw) < 6:
        raise ValueError("short owen ascii payload")
    expected = (raw[-2] << 8) | raw[-1]
    actual = owen_protocol_crc(raw, len(raw) - 2)
    if expected != actual:
        raise ValueError("bad owen ascii crc")
    return bytes(raw)


def build_owen_protocol_frame(address: int, mode: int, parameter_hash: int, data: bytes) -> bytes:
    raw = bytearray(
        (
            address & 0xFF,
            ((mode & 0x0F) << 4) | (len(data) & 0x0F),
            (parameter_hash >> 8) & 0xFF,
            parameter_hash & 0xFF,
        )
    )
    raw.extend(data)
    crc = owen_protocol_crc(raw)
    raw.extend(((crc >> 8) & 0xFF, crc & 0xFF))
    return encode_owen_protocol(raw)


@dataclass
class DeviceState:
    address: int = 16
    vendor: str = "OWEN"
    product: str = "PR200ADA"
    revision: str = "2.80"
    serial_number: str = "100896240332139440"
    coils: list[bool] = field(default_factory=lambda: [False] * 65536)
    discretes: list[bool] = field(default_factory=lambda: [False] * 65536)
    holding: list[int] = field(default_factory=lambda: [0] * 65536)
    inputs: list[int] = field(default_factory=lambda: [0] * 65536)
    program_hash: int = 0
    debug_block_number: int = 0
    debug_command_block: bytearray = field(default_factory=bytearray)
    debug_read_data: bytes = b""
    debug_update_counter: int = 0
    debug_default_block_number: int = 1
    debug_default_cells: int = 0
    d_sel: int = 0
    plc_l: int = 1
    starting_address: int = 131072
    program_memory: bytearray = field(default_factory=bytearray)

    def __post_init__(self) -> None:
        # Friendly defaults for exploratory reads. These values are not meant to
        # mirror firmware memory; they just keep common read requests coherent.
        self.inputs[0] = 0x0200
        self.inputs[1] = 0x0080
        self.holding[0] = 16
        self.holding[1] = 9600
        self.write_owen_identity_registers()

    def write_owen_identity_registers(self) -> None:
        """Populate PR200 service identity registers used by OWEN Logic."""
        for offset, value in enumerate(encode_owen_modbus_string(self.product)):
            self.holding[0xF000 + offset] = value
        for offset, value in enumerate(encode_owen_modbus_string(self.revision)):
            self.holding[0xF010 + offset] = value
        for offset, value in enumerate(encode_owen_modbus_string(self.serial_number)):
            self.holding[0xF084 + offset] = value


class Emulator:
    def __init__(
        self,
        state: DeviceState,
        log_path: Path,
        allow_writes: bool = True,
        debug_values_file: Path | None = None,
        debug_runtime: object | None = None,
    ) -> None:
        self.state = state
        self.log_path = log_path
        self.allow_writes = allow_writes
        self.debug_values_file = debug_values_file
        self.debug_runtime = debug_runtime
        self.running = True
        self.owen_parameter_by_hash = {
            owen_parameter_hash("DEV"): ("DEV", "string", lambda: self.state.product, None),
            owen_parameter_hash("VER"): ("VER", "string", lambda: self.state.revision, None),
            owen_parameter_hash("d.sel"): (
                "d.sel",
                "byte",
                lambda: self.state.d_sel,
                lambda value: setattr(self.state, "d_sel", value),
            ),
            owen_parameter_hash("plc.l"): (
                "plc.l",
                "byte",
                lambda: self.state.plc_l,
                lambda value: setattr(self.state, "plc_l", value),
            ),
            owen_parameter_hash("LOAD"): ("LOAD", "byte", lambda: 0, lambda _value: None),
            owen_parameter_hash("Addr"): ("Addr", "byte", lambda: self.state.address, None),
            owen_parameter_hash("bPS"): ("bPS", "uint", lambda: 9600, None),
            owen_parameter_hash("Sbit"): ("Sbit", "byte", lambda: 0, None),
        }

    def log(self, event: str, **payload: object) -> None:
        record = {"ts": datetime.now().isoformat(timespec="milliseconds"), "event": event, **payload}
        line = json.dumps(record, ensure_ascii=False)
        print(line, flush=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def exception(self, address: int, function: int, code: int) -> bytes:
        return add_crc(bytes((address, function | 0x80, code)))

    def read_values(self, store: list[int] | list[bool], start: int, quantity: int) -> list[int] | list[bool]:
        if quantity <= 0 or start < 0 or start + quantity > len(store):
            raise ValueError("range")
        return store[start : start + quantity]

    def handle_read_bits(self, function: int, start: int, quantity: int) -> bytes:
        store = self.state.coils if function == 0x01 else self.state.discretes
        values = self.read_values(store, start, quantity)
        return bytes((len(pack_bits(values)),)) + pack_bits(values)

    def handle_read_registers(self, function: int, start: int, quantity: int) -> bytes:
        store = self.state.holding if function == 0x03 else self.state.inputs
        values = self.read_values(store, start, quantity)
        payload = pack_registers(values)
        return bytes((len(payload),)) + payload

    def handle_report_slave_id(self) -> bytes:
        text = f"{self.state.vendor} {self.state.product} {self.state.revision} SN {self.state.serial_number}"
        data = text.encode("ascii", errors="replace")
        return bytes((len(data) + 1, 0xFF)) + data

    def handle_device_id(self, request: bytes) -> bytes:
        # Modbus Encapsulated Interface Transport, Read Device Identification.
        if len(request) < 5 or request[2] != 0x0E:
            raise ValueError("bad device id request")
        read_device_id_code = request[3]
        first_object_id = request[4]
        objects = [
            (0x00, self.state.vendor),
            (0x01, self.state.product),
            (0x02, self.state.revision),
            (0x03, self.state.serial_number),
        ]
        selected = [(oid, value) for oid, value in objects if oid >= first_object_id]
        if read_device_id_code == 0x01:
            selected = [item for item in selected if item[0] <= 0x02]
        selected = selected[:8]
        payload = bytearray((0x0E, read_device_id_code, 0x01, 0x00, 0x00, len(selected)))
        for oid, value in selected:
            encoded = value.encode("ascii", errors="replace")
            payload.extend((oid, len(encoded)))
            payload.extend(encoded)
        return bytes(payload)

    def encode_owen_value(self, value: object, value_type: str) -> bytes:
        if value_type == "string":
            return str(value).encode("cp1251", errors="replace")[::-1]
        if value_type == "byte":
            return bytes((int(value) & 0xFF,))
        if value_type == "uint":
            return int(value).to_bytes(4, "little", signed=False)
        raise ValueError("unsupported owen value type")

    def decode_owen_value(self, data: bytes, value_type: str) -> int | str:
        if value_type == "string":
            return data[::-1].decode("cp1251", errors="replace")
        if value_type == "byte":
            return data[0] if data else 0
        if value_type == "uint":
            return int.from_bytes(data[:4].ljust(4, b"\x00"), "little", signed=False)
        raise ValueError("unsupported owen value type")

    def handle_owen_ascii_frame(self, frame: bytes) -> bytes | None:
        try:
            raw = decode_owen_protocol(frame)
        except ValueError as exc:
            self.log("bad_owen_ascii", rx=frame.hex(" "), error=str(exc))
            return None

        address = raw[0]
        if address != self.state.address:
            self.log("ignore_owen_ascii_address", rx=frame.hex(" "), address=address)
            return None

        mode_len = raw[1]
        mode = mode_len >> 4
        data_len = mode_len & 0x0F
        parameter_hash = (raw[2] << 8) | raw[3]
        data = raw[4 : 4 + data_len]
        parameter = self.owen_parameter_by_hash.get(parameter_hash)
        if parameter is None:
            if mode == 0:
                self.log("owen_ascii_unknown_write_accepted", hash=f"{parameter_hash:04X}", size=len(data))
                return build_owen_protocol_frame(self.state.address, mode, parameter_hash, data)
            # OWEN uses n.Err to report "parameter not found" in the native
            # protocol. Error 40 is the value OWEN Logic itself checks for.
            response = build_owen_protocol_frame(
                self.state.address,
                1,
                owen_parameter_hash("n.Err"),
                bytes((40,)),
            )
            self.log("owen_ascii_unknown_parameter", hash=f"{parameter_hash:04X}")
            return response

        name, value_type, getter, setter = parameter
        if mode == 0:
            if setter is not None:
                setter(self.decode_owen_value(data, value_type))
            response_data = data
        else:
            response_data = self.encode_owen_value(getter(), value_type)
        response = build_owen_protocol_frame(self.state.address, mode, parameter_hash, response_data)
        self.log("owen_ascii", parameter=name, mode=("write" if mode == 0 else "read"))
        return response

    def handle_online_debug(self, pdu: bytes) -> bytes:
        if len(pdu) < 4:
            raise ValueError("bad online debug request")
        data_len = get_u16(pdu, 2)
        data = pdu[4 : 4 + data_len]
        if len(data) != data_len or not data:
            raise ValueError("bad online debug size")

        header = data[0]
        command_number = header >> 1
        status_ok = 0
        custom = b""

        if command_number == 1:
            custom = int(self.state.program_hash & 0xFFFFFFFF).to_bytes(4, "little")
        elif command_number == 2:
            custom = bytes((1, 0, 0)) + int(1024).to_bytes(2, "little") + int(1024).to_bytes(2, "little")
        elif command_number == 4:
            # WriteUserProgramCommandBlock packs: header, 2-byte fragment
            # offset, command block number, command bytes. ReadDataCommand
            # must later echo this block number or OWEN Logic aborts with
            # CommandBlockNumberException.
            if len(data) >= 4:
                offset = int.from_bytes(data[1:3], "little", signed=False)
                block_number = data[3]
                command_chunk = data[4:]
                if block_number != self.state.debug_block_number or offset == 0:
                    self.state.debug_command_block = bytearray()
                self.state.debug_block_number = block_number
                required = offset + len(command_chunk)
                if len(self.state.debug_command_block) < required:
                    self.state.debug_command_block.extend(b"\x00" * (required - len(self.state.debug_command_block)))
                self.state.debug_command_block[offset:required] = command_chunk
                self.state.debug_read_data = self.build_debug_read_data(bytes(self.state.debug_command_block))
        elif command_number == 6:
            block_number = self.state.debug_block_number
            read_data = self.state.debug_read_data
            if not read_data and self.state.debug_default_cells > 0:
                block_number = self.state.debug_default_block_number
                read_data = self.build_debug_pattern_cells(self.state.debug_default_cells)
            custom = (
                bytes((block_number & 0xFF, 0, 0))
                + read_data
            )
        elif command_number == 5:
            self.state.debug_update_counter += 1
            if self.debug_runtime is not None:
                self.debug_runtime.update()
                snapshot = getattr(self.debug_runtime, "snapshot_by_symbol", lambda: {})()
                self.log("debug_runtime_update", scan=self.state.debug_update_counter, values=snapshot)
            if self.state.debug_command_block:
                self.state.debug_read_data = self.build_debug_read_data(bytes(self.state.debug_command_block))
            custom = b""
        elif command_number in (3, 8):
            custom = b""
        else:
            status_ok = 2

        response_data = bytes((header, status_ok)) + custom
        return bytes((len(response_data) >> 8, len(response_data) & 0xFF)) + response_data

    def debug_pattern_value(self, read_index: int) -> int:
        phase = (self.state.debug_update_counter // 5) & 1
        return 1 if ((read_index + phase) % 2 == 0) else 0

    def load_debug_values(self) -> list[int]:
        if self.debug_values_file is None or not self.debug_values_file.exists():
            return []
        try:
            text = self.debug_values_file.read_text(encoding="utf-8-sig").strip()
            if not text:
                return []
            loaded = ast.literal_eval(text)
            if not isinstance(loaded, list):
                return []
            return [int(value) for value in loaded]
        except (OSError, SyntaxError, ValueError, TypeError):
            return []

    def build_debug_pattern_cells(self, cell_count: int) -> bytes:
        values = bytearray()
        runtime_values: dict[int, int] = {}
        if self.debug_runtime is not None and hasattr(self.debug_runtime, "values_by_read_index"):
            runtime_values = self.debug_runtime.values_by_read_index()
        file_values = self.load_debug_values()
        for read_index in range(cell_count):
            one_based_index = read_index + 1
            if one_based_index in runtime_values:
                value = runtime_values[one_based_index]
            elif read_index < len(file_values):
                value = file_values[read_index]
            else:
                value = self.debug_pattern_value(read_index)
            values.extend(int(value).to_bytes(4, "little", signed=False))
        return bytes(values)

    def build_debug_read_data(self, command_block: bytes) -> bytes:
        """Build stack values for OWEN Logic online debug reads.

        ProgramStackReadingCommand is a 2-byte little-endian word with bit 0
        set. Each read command expects one 4-byte stack cell in ReadData.
        Returning these cells is what makes OWEN Logic draw text in the value
        boxes instead of leaving them blank. When a debug runtime is attached,
        values are matched by the real read-index/stack-id map extracted from
        OWEN Logic's command block.
        """
        values = bytearray()
        from pr200_debug_extract import parse_debug_command_block

        read_points = parse_debug_command_block(command_block)
        runtime_values: dict[int, int] = {}
        if self.debug_runtime is not None:
            runtime_values = self.debug_runtime.values_for_read_points(read_points)
        file_values = self.load_debug_values()
        for zero_index, point in enumerate(read_points):
            if point.read_index in runtime_values:
                value = runtime_values[point.read_index]
            elif zero_index < len(file_values):
                value = file_values[zero_index]
            else:
                value = self.debug_pattern_value(zero_index)
            values.extend(int(value).to_bytes(4, "little", signed=False))
        return bytes(values)

    def handle_loader_protocol_block(self, frame: bytes) -> bytes:
        try:
            raw = decode_owen_nibbles(frame, 10)
            self.capture_program_frame(raw)
        except ValueError as exc:
            self.log("bad_loader_protocol_block", rx_len=len(frame), error=str(exc))
        return b"\x55"

    def capture_program_frame(self, raw: bytes) -> None:
        # PR200 loader frames contain: 14-byte frame header, N*8 program bytes,
        # and a 4-byte Fletcher complement. The first frame begins at the device
        # starting address, so it carries the PrHandler header with program CRC.
        if len(raw) < 14 + 8 + 4:
            return
        block_count = raw[0]
        address = int.from_bytes(raw[2:6], "little", signed=False)
        data_len = block_count * 8
        if data_len <= 0 or len(raw) < 14 + data_len:
            return
        offset = address - self.state.starting_address
        if offset < 0:
            return
        data = raw[14 : 14 + data_len]
        required = offset + data_len
        if len(self.state.program_memory) < required:
            self.state.program_memory.extend(b"\xFF" * (required - len(self.state.program_memory)))
        self.state.program_memory[offset:required] = data
        if len(self.state.program_memory) >= 12:
            self.state.program_hash = int.from_bytes(self.state.program_memory[8:12], "little", signed=False)
        self.log(
            "loader_program_frame",
            address=address,
            blocks=block_count,
            program_size=len(self.state.program_memory),
            program_hash=f"0x{self.state.program_hash:08X}",
        )

    def handle_write_single(self, function: int, pdu: bytes) -> bytes:
        start = get_u16(pdu, 2)
        value = get_u16(pdu, 4)
        if not self.allow_writes:
            return self.exception(pdu[0], function, 0x01)
        if function == 0x05:
            if start >= len(self.state.coils):
                return self.exception(pdu[0], function, 0x02)
            self.state.coils[start] = value == 0xFF00
        else:
            if start >= len(self.state.holding):
                return self.exception(pdu[0], function, 0x02)
            self.state.holding[start] = value
        return pdu

    def handle_write_multiple(self, function: int, pdu: bytes) -> bytes:
        start = get_u16(pdu, 2)
        quantity = get_u16(pdu, 4)
        byte_count = pdu[6]
        data = pdu[7 : 7 + byte_count]
        if not self.allow_writes:
            return self.exception(pdu[0], function, 0x01)
        if function == 0x0F:
            if start + quantity > len(self.state.coils):
                return self.exception(pdu[0], function, 0x02)
            bits: list[bool] = []
            for byte in data:
                for bit in range(8):
                    bits.append(bool(byte & (1 << bit)))
            for offset, bit_value in enumerate(bits[:quantity]):
                self.state.coils[start + offset] = bit_value
        else:
            if start + quantity > len(self.state.holding) or len(data) < quantity * 2:
                return self.exception(pdu[0], function, 0x02)
            for offset in range(quantity):
                self.state.holding[start + offset] = get_u16(data, offset * 2)
        return pdu[:6]

    def handle_frame(self, frame: bytes) -> bytes | None:
        if frame.startswith(b"#"):
            return self.handle_owen_ascii_frame(frame)
        if frame and OWEN_NIBBLE_BASE <= frame[0] <= OWEN_NIBBLE_BASE + 15 and frame.endswith(b"\n"):
            return self.handle_loader_protocol_block(frame)
        if len(frame) < 4:
            return None
        if not has_valid_crc(frame):
            self.log("bad_crc", rx=frame.hex(" "))
            return None

        pdu = frame[:-2]
        address, function = pdu[0], pdu[1]
        if address not in (self.state.address, 0):
            self.log("ignore_address", rx=frame.hex(" "), address=address)
            return None

        try:
            if function in (0x01, 0x02, 0x03, 0x04):
                start = get_u16(pdu, 2)
                quantity = get_u16(pdu, 4)
                body = (
                    self.handle_read_bits(function, start, quantity)
                    if function in (0x01, 0x02)
                    else self.handle_read_registers(function, start, quantity)
                )
                response = add_crc(bytes((address, function)) + body)
            elif function in (0x05, 0x06):
                response = add_crc(self.handle_write_single(function, pdu))
            elif function in (0x0F, 0x10):
                response = add_crc(self.handle_write_multiple(function, pdu))
            elif function == 0x11:
                response = add_crc(bytes((address, function)) + self.handle_report_slave_id())
            elif function == 0x2B:
                response = add_crc(bytes((address, function)) + self.handle_device_id(pdu))
            elif function == 0x41:
                response = add_crc(bytes((address, function)) + self.handle_online_debug(pdu))
            else:
                response = self.exception(address, function, 0x01)
        except ValueError:
            response = self.exception(address, function, 0x02)

        if address == 0:
            return None
        return response

    def read_request(self, ser: serial.Serial) -> bytes | None:
        first = ser.read(2)
        if not first:
            return None
        if len(first) < 2:
            return first
        if first[0] == ord("#"):
            payload = bytearray(first)
            while len(payload) < 128 and payload[-1] != 13:
                chunk = ser.read(1)
                if not chunk:
                    break
                payload.extend(chunk)
            return bytes(payload)
        if OWEN_NIBBLE_BASE <= first[0] <= OWEN_NIBBLE_BASE + 15:
            payload = bytearray(first)
            while len(payload) < 8192 and payload[-1] != 10:
                chunk = ser.read(1)
                if not chunk:
                    break
                payload.extend(chunk)
            return bytes(payload)
        function = first[1]
        if function in (0x01, 0x02, 0x03, 0x04, 0x05, 0x06):
            rest_len = 6
        elif function in (0x0F, 0x10):
            header_rest = ser.read(5)
            if len(header_rest) < 5:
                return first + header_rest
            byte_count = header_rest[4]
            return first + header_rest + ser.read(byte_count + 2)
        elif function == 0x11:
            rest_len = 2
        elif function == 0x2B:
            rest_len = 5
        elif function == 0x41:
            size_bytes = ser.read(2)
            if len(size_bytes) < 2:
                return first + size_bytes
            data_len = get_u16(size_bytes, 0)
            return first + size_bytes + ser.read(data_len + 2)
        else:
            time.sleep(0.05)
            return first + ser.read(254)
        return first + ser.read(rest_len)

    def serve(self, port: str, baudrate: int, timeout: float) -> None:
        self.log(
            "start",
            port=port,
            baudrate=baudrate,
            address=self.state.address,
            allow_writes=self.allow_writes,
            log=str(self.log_path),
        )
        serial_kwargs = {
            "baudrate": baudrate,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": timeout,
            "write_timeout": timeout,
        }
        if "://" in port:
            serial_kwargs["url"] = port
            open_serial = serial.serial_for_url
        else:
            serial_kwargs["port"] = port
            open_serial = serial.Serial

        with open_serial(
            **serial_kwargs,
        ) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            while self.running:
                try:
                    request = self.read_request(ser)
                except serial.SerialException as exc:
                    self.log("serial_closed", error=str(exc))
                    break
                if not request:
                    continue
                response = self.handle_frame(request)
                if response:
                    ser.write(response)
                    ser.flush()
                    self.log("frame", rx=request.hex(" "), tx=response.hex(" "))
                else:
                    self.log("frame", rx=request.hex(" "), tx=None)


def list_available_ports() -> int:
    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports visible to pyserial.")
        return 1
    for port in ports:
        print(f"{port.device}: {port.description} [{port.hwid}]")
    return 0


def self_test() -> int:
    state = DeviceState(address=16)
    emulator = Emulator(state, Path("NUL") if sys.platform.startswith("win") else Path("/dev/null"))
    request = add_crc(bytes.fromhex("10 03 00 00 00 02"))
    response = emulator.handle_frame(request)
    assert response is not None and has_valid_crc(response), response
    assert response[:3] == bytes((0x10, 0x03, 0x04)), response.hex(" ")
    request = add_crc(bytes.fromhex("10 11"))
    response = emulator.handle_frame(request)
    assert response is not None and has_valid_crc(response), response
    request = add_crc(bytes.fromhex("10 2b 0e 01 00"))
    response = emulator.handle_frame(request)
    assert response is not None and has_valid_crc(response), response
    print("Self-test OK")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OWEN Logic COM device emulator")
    parser.add_argument("--port", help="Emulator-side COM port, for example COM14")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--address", type=int, default=16)
    parser.add_argument("--serial-number", default="100896240332139440")
    parser.add_argument("--product", default="PR200ADA")
    parser.add_argument("--revision", default="2.80")
    parser.add_argument("--program-hash", default="0", help="Online-debug program hash, decimal or 0x-prefixed hex")
    parser.add_argument("--debug-default-block-number", type=int, default=1)
    parser.add_argument("--debug-default-cells", type=int, default=0)
    parser.add_argument("--debug-values-file", type=Path)
    parser.add_argument("--avr3in1-runtime", action="store_true", help="Publish AVR 3-in-1 runtime values to online-debug cells")
    parser.add_argument("--avr3in1-inputs-file", type=Path, help="JSON file with AVR 3-in-1 input values")
    parser.add_argument("--debug-symbol-map", type=Path, help="JSON map generated by pr200_debug_extract.py")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--read-only-writes", action="store_true", help="Reject Modbus write functions")
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_ports:
        return list_available_ports()
    if args.self_test:
        return self_test()
    if not args.port:
        print("ERROR: --port is required unless --list-ports or --self-test is used", file=sys.stderr)
        return 2

    state = DeviceState(
        address=args.address,
        product=args.product,
        revision=args.revision,
        serial_number=args.serial_number,
        program_hash=int(str(args.program_hash), 0),
        debug_default_block_number=args.debug_default_block_number,
        debug_default_cells=args.debug_default_cells,
    )
    debug_runtime = None
    if args.avr3in1_runtime:
        if args.debug_symbol_map:
            symbol_map_path = args.debug_symbol_map
        else:
            from owen_artifact_paths import resolve_pr200_reverse_file

            symbol_map_path = resolve_pr200_reverse_file(__file__, "avr3in1_debug_symbol_map.json")
        from pr200_avr_runtime import AVR3In1DebugRuntime

        debug_runtime = AVR3In1DebugRuntime(symbol_map_path, args.avr3in1_inputs_file)
    emulator = Emulator(
        state,
        args.log,
        allow_writes=not args.read_only_writes,
        debug_values_file=args.debug_values_file,
        debug_runtime=debug_runtime,
    )

    def stop(_signum: int, _frame: object) -> None:
        emulator.running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        emulator.serve(args.port, args.baudrate, args.timeout)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
