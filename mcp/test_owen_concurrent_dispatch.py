#!/usr/bin/env python3
from __future__ import annotations

import threading
import time
import unittest

import owen_logic_server as server


class OwenConcurrentDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_call_tool = server.call_tool
        self.original_send_message = server.send_message
        self.messages: list[dict] = []
        self.messages_lock = threading.Lock()

        def capture(message: dict) -> None:
            with self.messages_lock:
                self.messages.append(message)

        server.send_message = capture

    def tearDown(self) -> None:
        server.call_tool = self.original_call_tool
        server.send_message = self.original_send_message
        with server._ACTIVE_REQUESTS_LOCK:
            active = list(server._ACTIVE_REQUESTS.values())
        for future, event in active:
            event.set()
            future.cancel()

    def wait_for(self, predicate, timeout: float = 3.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return
            time.sleep(0.01)
        self.fail("timed out waiting for concurrent dispatcher state")

    def test_general_calls_can_complete_out_of_order_with_isolated_context(self) -> None:
        slow_started = threading.Event()
        release_slow = threading.Event()

        def fake_call_tool(name: str, arguments: dict) -> dict:
            if arguments.get("slow"):
                slow_started.set()
                release_slow.wait(3)
            return server.tool_result({"ok": True, "value": arguments["value"]})

        server.call_tool = fake_call_tool
        server._dispatch_tool_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "owen_logic_find_installation", "arguments": {"slow": True, "value": "slow"}}})
        self.assertTrue(slow_started.wait(1))
        server._dispatch_tool_request({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "owen_logic_find_installation", "arguments": {"value": "fast"}}})
        self.wait_for(lambda: any(message.get("id") == 2 for message in self.messages))
        self.assertFalse(any(message.get("id") == 1 for message in self.messages))
        release_slow.set()
        self.wait_for(lambda: any(message.get("id") == 1 for message in self.messages))
        self.assertEqual([message["id"] for message in self.messages[:2]], [2, 1])
        for message in self.messages[:2]:
            self.assertEqual(message["result"]["structuredContent"]["tool"], "owen_logic_find_installation")

    def test_cancelled_queued_gui_call_never_runs_or_responds(self) -> None:
        first_started = threading.Event()
        release_first = threading.Event()
        executed: list[str] = []

        def fake_call_tool(name: str, arguments: dict) -> dict:
            executed.append(arguments["value"])
            if arguments["value"] == "first":
                first_started.set()
                release_first.wait(3)
            return server.tool_result({"ok": True, "value": arguments["value"]})

        server.call_tool = fake_call_tool
        server._dispatch_tool_request({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "owen_logic_focus_window", "arguments": {"value": "first"}}})
        self.assertTrue(first_started.wait(1))
        server._dispatch_tool_request({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "owen_logic_focus_window", "arguments": {"value": "second"}}})
        server._cancel_request(4)
        release_first.set()
        self.wait_for(lambda: any(message.get("id") == 3 for message in self.messages))
        time.sleep(0.1)
        self.assertEqual(executed, ["first"])
        self.assertFalse(any(message.get("id") == 4 for message in self.messages))


if __name__ == "__main__":
    unittest.main()
