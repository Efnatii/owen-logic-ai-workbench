#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


SERVER = Path(__file__).with_name("owen_logic_server.py")


def write_message(stream: Any, message: dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
    stream.flush()


def read_exact(stream: Any, length: int) -> bytes:
    chunks: list[bytes] = []
    remaining = length
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise EOFError("server stdout closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_message(stream: Any) -> dict[str, Any]:
    headers: list[bytes] = []
    while True:
        line = stream.readline()
        if not line:
            raise EOFError("server stdout closed before headers")
        if line in {b"\r\n", b"\n"}:
            break
        headers.append(line)
    content_length = None
    for line in headers:
        if line.lower().startswith(b"content-length:"):
            content_length = int(line.split(b":", 1)[1].strip())
            break
    if content_length is None:
        raise RuntimeError("missing Content-Length header")
    return json.loads(read_exact(stream, content_length).decode("utf-8"))


def main() -> int:
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
    process = subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdin is not None and process.stdout is not None
    responses: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()

    def reader() -> None:
        try:
            while True:
                responses.put(read_message(process.stdout))
        except BaseException as exc:
            responses.put(exc)

    threading.Thread(target=reader, daemon=True).start()
    started = time.perf_counter()
    try:
        write_message(process.stdin, {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "owen-native-concurrency-test", "version": "1"}}})
        initialized = responses.get(timeout=10)
        if isinstance(initialized, BaseException) or initialized.get("id") != 0:
            raise AssertionError(f"initialize failed: {initialized!r}")
        write_message(process.stdin, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        write_message(process.stdin, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "owen_logic_program_file_analysis", "arguments": {"include_process_command_lines": False, "max_strings": 1, "max_matches": 1}}})
        write_message(process.stdin, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "owen_logic_find_installation", "arguments": {}}})
        first = responses.get(timeout=15)
        if isinstance(first, BaseException):
            raise first
        fast_latency_ms = round((time.perf_counter() - started) * 1000)
        if first.get("id") != 2:
            raise AssertionError(f"fast request was head-of-line blocked; first response id={first.get('id')}")
        result = first.get("result") or {}
        if result.get("_meta", {}).get("output_contract_tool") != "owen_logic_find_installation":
            raise AssertionError("concurrent response lost per-request tool context")

        write_message(process.stdin, {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1, "reason": "native concurrency test complete"}})
        write_message(process.stdin, {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}})
        ping = responses.get(timeout=5)
        if isinstance(ping, BaseException) or ping.get("id") != 3:
            raise AssertionError(f"server stopped serving control traffic after cancellation: {ping!r}")
        print(json.dumps({"status": "PASS", "first_tool_response_id": 2, "cancelled_request_id": 1, "ping_after_cancel": True, "fast_latency_ms": fast_latency_ms}, ensure_ascii=False))
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
