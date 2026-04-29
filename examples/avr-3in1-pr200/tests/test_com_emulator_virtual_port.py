import socket
import threading
import time
import unittest
from pathlib import Path

import serial

from owen_logic_com_emulator import (
    DeviceState,
    Emulator,
    add_crc,
    decode_owen_protocol,
    encode_owen_nibbles,
    encode_owen_modbus_string,
    has_valid_crc,
    owen_parameter_hash,
)


def free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TcpNullModemPair:
    """Two TCP endpoints that forward bytes both ways, like a null-modem pair."""

    def __init__(self) -> None:
        self.left_port = free_tcp_port()
        self.right_port = free_tcp_port()
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.sockets: list[socket.socket] = []
        self.error: BaseException | None = None

    def start(self) -> None:
        self.thread.start()
        if not self.ready.wait(2.0):
            raise RuntimeError("TCP null-modem bridge did not start")

    def close(self) -> None:
        self.stop.set()
        for sock in list(self.sockets):
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        self.thread.join(2.0)

    def _run(self) -> None:
        try:
            left_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            right_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sockets.extend([left_listener, right_listener])
            left_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            right_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            left_listener.bind(("127.0.0.1", self.left_port))
            right_listener.bind(("127.0.0.1", self.right_port))
            left_listener.listen(1)
            right_listener.listen(1)
            self.ready.set()
            left, _ = left_listener.accept()
            right, _ = right_listener.accept()
            self.sockets.extend([left, right])

            def forward(src: socket.socket, dst: socket.socket) -> None:
                while not self.stop.is_set():
                    try:
                        data = src.recv(4096)
                    except OSError:
                        break
                    if not data:
                        break
                    try:
                        dst.sendall(data)
                    except OSError:
                        break

            t1 = threading.Thread(target=forward, args=(left, right), daemon=True)
            t2 = threading.Thread(target=forward, args=(right, left), daemon=True)
            t1.start()
            t2.start()
            while not self.stop.is_set() and (t1.is_alive() or t2.is_alive()):
                time.sleep(0.02)
        except BaseException as exc:
            self.error = exc
            self.ready.set()


class VirtualPortEmulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = TcpNullModemPair()
        self.bridge.start()
        self.emulator = Emulator(
            DeviceState(address=16),
            Path(__file__).with_name("owen_logic_com_emulator_virtual_port.log"),
        )
        self.emulator_thread = threading.Thread(
            target=self.emulator.serve,
            args=(f"socket://127.0.0.1:{self.bridge.right_port}", 9600, 0.05),
            daemon=True,
        )
        self.emulator_thread.start()
        self.client = serial.serial_for_url(
            f"socket://127.0.0.1:{self.bridge.left_port}",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1.0,
            write_timeout=1.0,
        )
        time.sleep(0.05)

    def tearDown(self) -> None:
        try:
            self.client.close()
        finally:
            self.emulator.running = False
            self.bridge.close()
            self.emulator_thread.join(2.0)
        if self.bridge.error:
            raise self.bridge.error

    def transact(self, payload_hex: str, expected_min_len: int = 5) -> bytes:
        frame = add_crc(bytes.fromhex(payload_hex))
        self.client.reset_input_buffer()
        self.client.write(frame)
        self.client.flush()
        response = self.client.read(256)
        self.assertGreaterEqual(len(response), expected_min_len)
        self.assertTrue(has_valid_crc(response), response.hex(" "))
        return response

    def ascii_transact(self, frame: bytes) -> bytes:
        self.client.reset_input_buffer()
        self.client.write(frame)
        self.client.flush()
        response = self.client.read_until(b"\r", 128)
        self.assertTrue(response.startswith(b"#"), response)
        self.assertTrue(response.endswith(b"\r"), response)
        return response

    def test_01_report_slave_id_through_virtual_port(self):
        response = self.transact("10 11")
        self.assertEqual(response[0], 0x10)
        self.assertEqual(response[1], 0x11)

    def test_02_read_holding_registers_through_virtual_port(self):
        response = self.transact("10 03 00 00 00 02")
        self.assertEqual(response[:3], bytes.fromhex("10 03 04"))
        self.assertEqual(response[3:7], bytes.fromhex("00 10 25 80"))

    def test_03_read_input_registers_through_virtual_port(self):
        response = self.transact("10 04 00 00 00 02")
        self.assertEqual(response[:3], bytes.fromhex("10 04 04"))
        self.assertEqual(response[3:7], bytes.fromhex("02 00 00 80"))

    def test_04_write_and_read_single_coil_through_virtual_port(self):
        response = self.transact("10 05 00 05 ff 00")
        self.assertEqual(response[:-2], bytes.fromhex("10 05 00 05 ff 00"))
        response = self.transact("10 01 00 00 00 08")
        self.assertEqual(response[:3], bytes.fromhex("10 01 01"))
        self.assertEqual(response[3] & (1 << 5), 1 << 5)

    def test_05_write_and_read_single_register_through_virtual_port(self):
        response = self.transact("10 06 00 0a 12 34")
        self.assertEqual(response[:-2], bytes.fromhex("10 06 00 0a 12 34"))
        response = self.transact("10 03 00 0a 00 01")
        self.assertEqual(response[:3], bytes.fromhex("10 03 02"))
        self.assertEqual(response[3:5], bytes.fromhex("12 34"))

    def test_06_wrong_address_is_ignored(self):
        frame = add_crc(bytes.fromhex("11 03 00 00 00 01"))
        self.client.reset_input_buffer()
        self.client.write(frame)
        self.client.flush()
        self.assertEqual(self.client.read(64), b"")

    def test_07_bad_crc_is_ignored(self):
        self.client.reset_input_buffer()
        self.client.write(bytes.fromhex("10 03 00 00 00 01 00 00"))
        self.client.flush()
        self.assertEqual(self.client.read(64), b"")

    def test_08_identity_register_encoding_matches_owen_logic(self):
        self.assertEqual(
            encode_owen_modbus_string("PR200ADA")[:4],
            [0x5250, 0x3032, 0x4130, 0x4144],
        )

    def test_09_pr200ada_device_identity_registers_through_virtual_port(self):
        response = self.transact("10 03 f0 00 00 10", expected_min_len=37)
        self.assertEqual(response[:3], bytes.fromhex("10 03 20"))
        self.assertEqual(self.decode_owen_string_response(response), "PR200ADA")

    def test_10_pr200ada_version_registers_through_virtual_port(self):
        response = self.transact("10 03 f0 10 00 10", expected_min_len=37)
        self.assertEqual(response[:3], bytes.fromhex("10 03 20"))
        self.assertEqual(self.decode_owen_string_response(response), "2.80")

    def test_11_pr200ada_serial_registers_through_virtual_port(self):
        response = self.transact("10 03 f0 84 00 10", expected_min_len=37)
        self.assertEqual(response[:3], bytes.fromhex("10 03 20"))
        self.assertEqual(
            self.decode_owen_string_response(response),
            self.emulator.state.serial_number,
        )

    def test_12_native_owen_protocol_reads_version(self):
        response = self.ascii_transact(b"#HGHGITLRJVKN\r")
        raw = decode_owen_protocol(response)
        self.assertEqual(raw[0], 16)
        self.assertEqual((raw[2] << 8) | raw[3], owen_parameter_hash("VER"))
        self.assertEqual(raw[4:8][::-1].decode("cp1251"), "2.80")

    def test_13_native_owen_protocol_reads_d_sel(self):
        response = self.ascii_transact(b"#HGHGTGVQNSOG\r")
        raw = decode_owen_protocol(response)
        self.assertEqual((raw[2] << 8) | raw[3], owen_parameter_hash("d.sel"))
        self.assertEqual(raw[4], 0)

    def test_14_online_debug_verify_command_uses_function_41(self):
        response = self.transact("10 41 00 01 02", expected_min_len=10)
        self.assertEqual(response[:6], bytes.fromhex("10 41 00 06 02 00"))
        self.assertEqual(int.from_bytes(response[6:10], "little"), self.emulator.state.program_hash)

    def test_15_online_debug_read_info_command_uses_function_41(self):
        response = self.transact("10 41 00 01 04", expected_min_len=13)
        self.assertEqual(response[:6], bytes.fromhex("10 41 00 09 04 00"))
        self.assertEqual(response[6:9], bytes((1, 0, 0)))
        self.assertEqual(int.from_bytes(response[9:11], "little"), 1024)
        self.assertEqual(int.from_bytes(response[11:13], "little"), 1024)

    def test_16_loader_protocol_block_is_acknowledged(self):
        self.client.reset_input_buffer()
        self.client.write(b"GHIJKLMNOP\n")
        self.client.flush()
        self.assertEqual(self.client.read(1), b"\x55")

    def test_17_loader_protocol_captures_program_hash_for_debug_verify(self):
        program = bytearray(b"\x00" * 16)
        program[8:12] = int(0x12345678).to_bytes(4, "little")

        raw = bytearray(14 + len(program) + 4)
        raw[0] = len(program) // 8
        raw[1] = 1
        raw[2:6] = int(131072).to_bytes(4, "little")
        raw[14 : 14 + len(program)] = program

        self.client.reset_input_buffer()
        self.client.write(encode_owen_nibbles(raw, 10))
        self.client.flush()
        self.assertEqual(self.client.read(1), b"\x55")
        self.assertEqual(self.emulator.state.program_hash, 0x12345678)

        response = self.transact("10 41 00 01 02", expected_min_len=10)
        self.assertEqual(int.from_bytes(response[6:10], "little"), 0x12345678)

    def test_18_online_debug_read_data_echoes_written_command_block_number(self):
        response = self.transact("10 41 00 08 09 00 00 01 03 00 07 00", expected_min_len=8)
        self.assertEqual(response[:6], bytes.fromhex("10 41 00 02 09 00"))
        self.assertEqual(self.emulator.state.debug_block_number, 1)

        response = self.transact("10 41 00 01 0d", expected_min_len=19)
        self.assertEqual(response[:8], bytes.fromhex("10 41 00 0d 0d 00 01 00"))
        self.assertEqual(response[8], 0)
        self.assertEqual(response[9:17], b"\x01\x00\x00\x00\x00\x00\x00\x00")

        for _ in range(5):
            self.transact("10 41 00 01 0b", expected_min_len=8)
        response = self.transact("10 41 00 01 0d", expected_min_len=19)
        self.assertEqual(response[9:17], b"\x00\x00\x00\x00\x01\x00\x00\x00")

    def test_19_online_debug_default_cells_are_returned_without_command_block(self):
        self.emulator.state.debug_default_block_number = 1
        self.emulator.state.debug_default_cells = 2

        response = self.transact("10 41 00 01 0d", expected_min_len=19)
        self.assertEqual(response[:8], bytes.fromhex("10 41 00 0d 0d 00 01 00"))
        self.assertEqual(response[8], 0)
        self.assertEqual(response[9:17], b"\x01\x00\x00\x00\x00\x00\x00\x00")

    def test_20_online_debug_default_cells_can_come_from_values_file(self):
        values_path = Path(__file__).with_name("owen_logic_debug_values_test.tmp")
        values_path.write_text("[7, 8]", encoding="utf-8")
        self.addCleanup(lambda: values_path.unlink(missing_ok=True))
        self.emulator.debug_values_file = values_path
        self.emulator.state.debug_default_block_number = 1
        self.emulator.state.debug_default_cells = 2

        response = self.transact("10 41 00 01 0d", expected_min_len=19)
        self.assertEqual(response[:8], bytes.fromhex("10 41 00 0d 0d 00 01 00"))
        self.assertEqual(response[8], 0)
        self.assertEqual(response[9:17], b"\x07\x00\x00\x00\x08\x00\x00\x00")

    def test_21_online_debug_command_block_cells_can_come_from_values_file(self):
        values_path = Path(__file__).with_name("owen_logic_debug_values_test.tmp")
        values_path.write_text("[7, 8]", encoding="utf-8")
        self.addCleanup(lambda: values_path.unlink(missing_ok=True))
        self.emulator.debug_values_file = values_path

        self.transact("10 41 00 08 09 00 00 01 03 00 07 00", expected_min_len=8)
        response = self.transact("10 41 00 01 0d", expected_min_len=19)
        self.assertEqual(response[9:17], b"\x07\x00\x00\x00\x08\x00\x00\x00")

    def test_22_online_debug_values_file_accepts_utf8_bom(self):
        values_path = Path(__file__).with_name("owen_logic_debug_values_test.tmp")
        values_path.write_bytes("[7, 8]".encode("utf-8-sig"))
        self.addCleanup(lambda: values_path.unlink(missing_ok=True))
        self.emulator.debug_values_file = values_path
        self.emulator.state.debug_default_block_number = 1
        self.emulator.state.debug_default_cells = 2

        response = self.transact("10 41 00 01 0d", expected_min_len=19)
        self.assertEqual(response[9:17], b"\x07\x00\x00\x00\x08\x00\x00\x00")

    @staticmethod
    def decode_owen_string_response(response: bytes) -> str:
        body = response[3:-2]
        raw = bytearray()
        for index in range(0, len(body), 2):
            register = int.from_bytes(body[index : index + 2], "big")
            raw.extend(register.to_bytes(2, "little"))
        return bytes(byte for byte in raw if byte == 10 or byte >= 32).decode("cp1251")


if __name__ == "__main__":
    unittest.main(verbosity=2)
