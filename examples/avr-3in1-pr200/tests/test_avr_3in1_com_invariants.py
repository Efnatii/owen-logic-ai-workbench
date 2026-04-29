import socket
import threading
import time
import unittest
from dataclasses import fields

import serial

from avr_3in1_sim import AVR3In1, AVRInputs, AVROutputs
from owen_logic_com_emulator import add_crc, has_valid_crc
from test_avr_3in1_invariants import (
    INPUT_FIELDS,
    STATES,
    active_input,
    all_inputs,
    target_input,
    undefined_flags,
)


OUTPUT_BIT_FIELDS = (
    "xQ1",
    "xQ2",
    "xQ3",
    "xQ4",
    "xQ5",
    "xQ6",
    "xAutoMode",
    "xManualMode",
    "xAlarm",
    "xAlarmFault",
    "xAlarmParallel",
    "xAlarmUndefined",
    "xQF1Undefined",
    "xQF2Undefined",
    "xQF3Undefined",
    "xNoSource",
    "xTargetDelayActive",
)


def free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TcpNullModemPair:
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
                        data = src.recv(65536)
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
                time.sleep(0.01)
        except BaseException as exc:
            self.error = exc
            self.ready.set()


class AvrComInvariantDevice:
    ADDRESS = 0x10
    FUNCTION_BATCH = 0x46
    CASE_SIZE = 9
    RESULT_SIZE = 12

    def __init__(self, port_url: str) -> None:
        self.port_url = port_url
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.error: BaseException | None = None

    def start(self) -> None:
        self.thread.start()
        if not self.ready.wait(2.0):
            raise RuntimeError("AVR COM invariant device did not start")

    def close(self) -> None:
        self.stop.set()
        self.thread.join(2.0)

    def _run(self) -> None:
        try:
            with serial.serial_for_url(
                self.port_url,
                baudrate=115200,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=0.1,
                write_timeout=1.0,
            ) as ser:
                self.ready.set()
                while not self.stop.is_set():
                    header = ser.read(4)
                    if not header:
                        continue
                    if len(header) < 4:
                        continue
                    address, function = header[0], header[1]
                    count = int.from_bytes(header[2:4], "big")
                    rest = ser.read(count * self.CASE_SIZE + 2)
                    frame = header + rest
                    if address != self.ADDRESS or function != self.FUNCTION_BATCH or not has_valid_crc(frame):
                        continue
                    response = bytearray((self.ADDRESS, self.FUNCTION_BATCH))
                    response.extend(count.to_bytes(2, "big"))
                    body = frame[4:-2]
                    for offset in range(0, len(body), self.CASE_SIZE):
                        response.extend(self._run_case(body[offset : offset + self.CASE_SIZE]))
                    ser.write(add_crc(bytes(response)))
                    ser.flush()
        except BaseException as exc:
            self.error = exc
            self.ready.set()

    def _run_case(self, data: bytes) -> bytes:
        state = int.from_bytes(data[0:2], "big", signed=False)
        stable_target = data[2]
        pending_target = data[3]
        delay_counter = data[4]
        input_delay = int.from_bytes(data[5:7], "big", signed=False)
        input_bits = int.from_bytes(data[7:9], "big", signed=False)

        values = {name: bool(input_bits & (1 << index)) for index, name in enumerate(INPUT_FIELDS)}
        values["input_delay_sec"] = input_delay

        avr = AVR3In1()
        avr.state = state
        avr.target_initialized = True
        avr.stable_target = stable_target
        avr.pending_target = pending_target
        avr.delay_counter_sec = delay_counter
        outputs = avr.step(AVRInputs(**values))
        return encode_outputs(outputs)


class AvrComClient:
    def __init__(self, port_url: str) -> None:
        self.ser = serial.serial_for_url(
            port_url,
            baudrate=115200,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2.0,
            write_timeout=2.0,
        )

    def close(self) -> None:
        self.ser.close()

    def run_cases(self, cases: list[tuple[int, int, int, int, AVRInputs]]) -> list[AVROutputs]:
        request = bytearray((AvrComInvariantDevice.ADDRESS, AvrComInvariantDevice.FUNCTION_BATCH))
        request.extend(len(cases).to_bytes(2, "big"))
        for state, stable_target, pending_target, delay_counter, inputs in cases:
            request.extend(int(state).to_bytes(2, "big", signed=False))
            request.append(stable_target & 0xFF)
            request.append(pending_target & 0xFF)
            request.append(delay_counter & 0xFF)
            request.extend(int(inputs.input_delay_sec).to_bytes(2, "big", signed=False))
            request.extend(pack_input_bits(inputs).to_bytes(2, "big", signed=False))

        self.ser.reset_input_buffer()
        self.ser.write(add_crc(bytes(request)))
        self.ser.flush()
        expected_len = 4 + len(cases) * AvrComInvariantDevice.RESULT_SIZE + 2
        response = self.ser.read(expected_len)
        if len(response) != expected_len:
            raise AssertionError(f"short COM response: expected {expected_len}, got {len(response)}")
        if not has_valid_crc(response):
            raise AssertionError(f"bad COM response CRC: {response.hex(' ')}")
        if response[:2] != bytes((AvrComInvariantDevice.ADDRESS, AvrComInvariantDevice.FUNCTION_BATCH)):
            raise AssertionError(f"bad COM response header: {response.hex(' ')}")
        count = int.from_bytes(response[2:4], "big", signed=False)
        if count != len(cases):
            raise AssertionError(f"bad COM response count: expected {len(cases)}, got {count}")

        body = response[4:-2]
        return [
            decode_outputs(body[index : index + AvrComInvariantDevice.RESULT_SIZE])
            for index in range(0, len(body), AvrComInvariantDevice.RESULT_SIZE)
        ]


def pack_input_bits(inputs: AVRInputs) -> int:
    result = 0
    for index, name in enumerate(INPUT_FIELDS):
        if getattr(inputs, name):
            result |= 1 << index
    return result


def encode_outputs(outputs: AVROutputs) -> bytes:
    bits = 0
    for index, name in enumerate(OUTPUT_BIT_FIELDS):
        if getattr(outputs, name):
            bits |= 1 << index
    data = bytearray()
    data.extend(bits.to_bytes(4, "little", signed=False))
    data.append(outputs.udiActive & 0xFF)
    data.append(outputs.udiRawTarget & 0xFF)
    data.append(outputs.udiTarget & 0xFF)
    data.append(outputs.udiPendingTarget & 0xFF)
    data.extend(outputs.udiDelayCounterSec.to_bytes(2, "big", signed=False))
    data.extend(outputs.udiState.to_bytes(2, "big", signed=False))
    return bytes(data)


def decode_outputs(data: bytes) -> AVROutputs:
    bits = int.from_bytes(data[0:4], "little", signed=False)
    values = {field.name: False for field in fields(AVROutputs)}
    for index, name in enumerate(OUTPUT_BIT_FIELDS):
        values[name] = bool(bits & (1 << index))
    values["udiActive"] = data[4]
    values["udiRawTarget"] = data[5]
    values["udiTarget"] = data[6]
    values["udiPendingTarget"] = data[7]
    values["udiDelayCounterSec"] = int.from_bytes(data[8:10], "big", signed=False)
    values["udiState"] = int.from_bytes(data[10:12], "big", signed=False)
    return AVROutputs(**values)


def expected_outputs(state: int, stable_target: int, pending_target: int, delay_counter: int, inputs: AVRInputs) -> AVROutputs:
    avr = AVR3In1()
    avr.state = state
    avr.target_initialized = True
    avr.stable_target = stable_target
    avr.pending_target = pending_target
    avr.delay_counter_sec = delay_counter
    return avr.step(inputs)


class AVR3In1ComInvariantTests(unittest.TestCase):
    CHUNK_SIZE = 2048

    def setUp(self) -> None:
        self.bridge = TcpNullModemPair()
        self.bridge.start()
        self.device = AvrComInvariantDevice(f"socket://127.0.0.1:{self.bridge.right_port}")
        self.device.start()
        self.client = AvrComClient(f"socket://127.0.0.1:{self.bridge.left_port}")

    def tearDown(self) -> None:
        self.client.close()
        self.device.close()
        self.bridge.close()
        if self.device.error:
            raise self.device.error
        if self.bridge.error:
            raise self.bridge.error

    def test_exhaustive_scheme_invariants_over_com(self):
        checked = 0
        chunk: list[tuple[int, int, int, int, AVRInputs]] = []

        def flush() -> None:
            nonlocal checked, chunk
            if not chunk:
                return
            outputs = self.client.run_cases(chunk)
            for case, output in zip(chunk, outputs):
                state, stable_target, pending_target, delay_counter, inputs = case
                expected = expected_outputs(state, stable_target, pending_target, delay_counter, inputs)
                self.assertEqual(output, expected, (state, stable_target, pending_target, delay_counter, inputs, output, expected))
                self.assert_scheme_invariants(state, inputs, output)
                checked += 1
            chunk = []

        for state in STATES:
            for inputs in all_inputs():
                chunk.append((state, 0, 0, 0, inputs))
                if len(chunk) >= self.CHUNK_SIZE:
                    flush()
        flush()

        for state in STATES:
            for stable_target in (0, 1, 2, 3):
                for inputs in all_inputs():
                    inputs.input_delay_sec = 3
                    pending = target_input(inputs)
                    chunk.append((state, stable_target, pending, 1, inputs))
                    if len(chunk) >= self.CHUNK_SIZE:
                        flush()
        flush()

        self.assertEqual(checked, 819200)

    def test_exhaustive_scheme_invariants_over_com_input_delay_3(self):
        checked = 0
        chunk: list[tuple[int, int, int, int, AVRInputs]] = []

        def flush() -> None:
            nonlocal checked, chunk
            if not chunk:
                return
            outputs = self.client.run_cases(chunk)
            for case, output in zip(chunk, outputs):
                state, stable_target, pending_target, delay_counter, inputs = case
                expected = expected_outputs(state, stable_target, pending_target, delay_counter, inputs)
                self.assertEqual(output, expected, (state, stable_target, pending_target, delay_counter, inputs, output, expected))
                self.assert_scheme_invariants(state, inputs, output)
                self.assert_delay_3_invariants(inputs, output)
                checked += 1
            chunk = []

        for state in STATES:
            for stable_target, pending_target, delay_counter in reachable_delay_memory_states():
                for inputs in all_inputs():
                    inputs.input_delay_sec = 3
                    chunk.append((state, stable_target, pending_target, delay_counter, inputs))
                    if len(chunk) >= self.CHUNK_SIZE:
                        flush()
        flush()

        self.assertEqual(checked, 6553600)

    def assert_scheme_invariants(self, state: int, inputs: AVRInputs, outputs: AVROutputs) -> None:
        self.assertFalse(outputs.xQ1 and outputs.xQ2, (state, inputs, outputs))
        self.assertFalse(outputs.xQ3 and outputs.xQ4, (state, inputs, outputs))
        self.assertFalse(outputs.xQ5 and outputs.xQ6, (state, inputs, outputs))
        self.assertLessEqual(int(outputs.xQ1) + int(outputs.xQ3) + int(outputs.xQ5), 1, (state, inputs, outputs))

        if outputs.xQ1 or outputs.xQ3 or outputs.xQ5:
            self.assertTrue(outputs.xAutoMode, (state, inputs, outputs))
            self.assertFalse(outputs.xManualMode, (state, inputs, outputs))
            self.assertFalse(outputs.xAlarm, (state, inputs, outputs))

        if outputs.xQ1:
            self.assertTrue(inputs.u1_ok and not inputs.qf1_fault, (state, inputs, outputs))
            self.assertTrue(inputs.qf2_off and inputs.qf3_off, (state, inputs, outputs))
        if outputs.xQ3:
            self.assertTrue(inputs.u2_ok and not inputs.qf2_fault, (state, inputs, outputs))
            self.assertTrue(inputs.qf1_off and inputs.qf3_off, (state, inputs, outputs))
        if outputs.xQ5:
            self.assertTrue(inputs.u3_ok and not inputs.qf3_fault, (state, inputs, outputs))
            self.assertTrue(inputs.qf1_off and inputs.qf2_off, (state, inputs, outputs))

        parallel = int(inputs.qf1_on) + int(inputs.qf2_on) + int(inputs.qf3_on) > 1
        if parallel:
            self.assertTrue(outputs.xAlarmParallel, (state, inputs, outputs))
            self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5, (state, inputs, outputs))
            self.assertEqual(outputs.xQ2, inputs.qf1_on, (state, inputs, outputs))
            self.assertEqual(outputs.xQ4, inputs.qf2_on, (state, inputs, outputs))
            self.assertEqual(outputs.xQ6, inputs.qf3_on, (state, inputs, outputs))

        self.assertEqual(outputs.xAlarm, outputs.xAlarmFault or outputs.xAlarmParallel or outputs.xAlarmUndefined, (state, inputs, outputs))
        self.assertEqual(outputs.xAlarmFault, inputs.qf1_fault or inputs.qf2_fault or inputs.qf3_fault, (state, inputs, outputs))
        self.assertEqual(outputs.udiActive, active_input(inputs), (state, inputs, outputs))
        if inputs.input_delay_sec == 0:
            self.assertEqual(outputs.udiTarget, target_input(inputs), (state, inputs, outputs))
            self.assertEqual(outputs.udiRawTarget, target_input(inputs), (state, inputs, outputs))
            self.assertEqual(outputs.udiPendingTarget, outputs.udiTarget, (state, inputs, outputs))
            self.assertEqual(outputs.udiDelayCounterSec, 0, (state, inputs, outputs))
        self.assertEqual(outputs.xNoSource, outputs.udiTarget == 0, (state, inputs, outputs))
        self.assertNotEqual(outputs.xManualMode, outputs.xAutoMode, (state, inputs, outputs))
        if inputs.manual_selector:
            self.assertFalse(outputs.xQ1 or outputs.xQ3 or outputs.xQ5, (state, inputs, outputs))

        qf1_undef, qf2_undef, qf3_undef = undefined_flags(inputs, state)
        self.assertEqual(outputs.xQF1Undefined, qf1_undef, (state, inputs, outputs))
        self.assertEqual(outputs.xQF2Undefined, qf2_undef, (state, inputs, outputs))
        self.assertEqual(outputs.xQF3Undefined, qf3_undef, (state, inputs, outputs))
        self.assertEqual(outputs.xAlarmUndefined, qf1_undef or qf2_undef or qf3_undef, (state, inputs, outputs))

        if outputs.xAlarmUndefined and not outputs.xAlarmParallel:
            self.assertFalse(outputs.xQ1 or outputs.xQ2 or outputs.xQ3 or outputs.xQ4 or outputs.xQ5 or outputs.xQ6, (state, inputs, outputs))

        known_states = {0, 11, 12, 13, 20, 31, 32, 33, 90}
        self.assertIn(outputs.udiState, known_states, (state, inputs, outputs))

    def assert_delay_3_invariants(self, inputs: AVRInputs, outputs: AVROutputs) -> None:
        self.assertEqual(inputs.input_delay_sec, 3)
        self.assertIn(outputs.udiRawTarget, (0, 1, 2, 3), (inputs, outputs))
        self.assertIn(outputs.udiTarget, (0, 1, 2, 3), (inputs, outputs))
        self.assertIn(outputs.udiPendingTarget, (0, 1, 2, 3), (inputs, outputs))
        self.assertLess(outputs.udiDelayCounterSec, 3, (inputs, outputs))
        self.assertEqual(outputs.xTargetDelayActive, outputs.udiRawTarget != outputs.udiTarget, (inputs, outputs))


def reachable_delay_memory_states():
    for stable_target in (0, 1, 2, 3):
        yield stable_target, stable_target, 0
        for pending_target in (0, 1, 2, 3):
            if pending_target == stable_target:
                continue
            for delay_counter in (0, 1, 2):
                yield stable_target, pending_target, delay_counter


if __name__ == "__main__":
    unittest.main(verbosity=2)
