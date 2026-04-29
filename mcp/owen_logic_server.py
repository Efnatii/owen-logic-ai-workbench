#!/usr/bin/env python3
"""Local MCP server for basic OWEN Logic smoke testing on Windows.

The server intentionally has no third-party MCP dependency. It implements the
small stdio JSON-RPC subset Codex needs for tools/list and tools/call.
"""

from __future__ import annotations

import csv
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Any


SERVER_NAME = "owen_logic"
SERVER_VERSION = "0.1.0"
DEFAULT_EXE = Path(r"C:\Program Files\Owen\OWEN Logic\ProgramRelayFBD.exe")
DEFAULT_CONVERTER_EXE = Path(
    r"C:\Program Files\Owen\OWEN Logic\ProjectJsonConverter\ProgramRelayFBD.exe"
)
SCREENSHOT_DIR = Path.home() / ".codex" / "tmp" / "owen_logic_screenshots"


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


user32 = ctypes.windll.user32 if os.name == "nt" else None


TOOLS: list[dict[str, Any]] = [
    {
        "name": "owen_logic_find_installation",
        "description": "Find the local OWEN Logic installation and report executable paths and versions.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_list_windows",
        "description": "List top-level Windows windows, optionally filtered to OWEN Logic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owen_only": {
                    "type": "boolean",
                    "description": "When true, return only windows likely owned by OWEN Logic.",
                    "default": True,
                },
                "include_invisible": {
                    "type": "boolean",
                    "description": "Include invisible top-level windows.",
                    "default": False,
                },
                "pid": {"type": "integer", "description": "Optional process id filter."},
                "title_filter": {
                    "type": "string",
                    "description": "Case-insensitive substring filter for window titles.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_list_processes",
        "description": "List running ProgramRelayFBD.exe processes and matching visible windows.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_launch",
        "description": "Launch OWEN Logic, optionally opening a project file, then report its windows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional project file path to pass to OWEN Logic.",
                },
                "exe_path": {
                    "type": "string",
                    "description": "Override path to ProgramRelayFBD.exe.",
                },
                "wait_seconds": {
                    "type": "number",
                    "description": "Seconds to wait before enumerating windows.",
                    "default": 5,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_screenshot",
        "description": "Capture a screenshot of the first matching OWEN Logic window.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional PNG output path. Defaults to ~/.codex/tmp/owen_logic_screenshots.",
                },
                "pid": {"type": "integer", "description": "Optional process id filter."},
                "title_filter": {
                    "type": "string",
                    "description": "Case-insensitive substring filter for the window title.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_focus_window",
        "description": "Bring a matching OWEN Logic window to the foreground.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "Optional process id filter."},
                "title_filter": {
                    "type": "string",
                    "description": "Case-insensitive substring filter for the window title.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_send_hotkey",
        "description": "Send a simple hotkey to a matching OWEN Logic window, for example CTRL+O.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys to press together, for example ['CTRL', 'O'].",
                },
                "pid": {"type": "integer", "description": "Optional process id filter."},
                "title_filter": {
                    "type": "string",
                    "description": "Case-insensitive substring filter for the window title.",
                },
                "delay_ms": {
                    "type": "integer",
                    "description": "Delay in milliseconds after focusing before pressing keys.",
                    "default": 200,
                },
            },
            "required": ["keys"],
            "additionalProperties": False,
        },
    },
    {
        "name": "owen_logic_smoke_test",
        "description": "Run a non-destructive smoke test: find installation, launch if needed, wait for a window, and optionally screenshot it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional project file path to open during the smoke test.",
                },
                "launch_if_needed": {
                    "type": "boolean",
                    "description": "Launch OWEN Logic when no matching window exists.",
                    "default": True,
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "Maximum time to wait for an OWEN Logic window.",
                    "default": 20,
                },
                "screenshot": {
                    "type": "boolean",
                    "description": "Capture a screenshot when a window is found.",
                    "default": True,
                },
            },
            "additionalProperties": False,
        },
    },
]


def read_exact(length: int) -> bytes | None:
    chunks: list[bytes] = []
    remaining = length
    while remaining > 0:
        chunk = sys.stdin.buffer.read(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_message() -> dict[str, Any] | None:
    header = bytearray()
    while True:
        char = sys.stdin.buffer.read(1)
        if not char:
            return None
        header.extend(char)
        if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
            break
        if len(header) > 65536:
            raise ValueError("MCP header is too large")

    header_text = header.decode("ascii", errors="replace").replace("\r\n", "\n")
    content_length = None
    for line in header_text.split("\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length is None:
        raise ValueError("Missing Content-Length header")

    body = read_exact(content_length)
    if body is None:
        return None
    return json.loads(body.decode("utf-8"))


def send_message(message: dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def rpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def tool_result(data: Any, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(data, ensure_ascii=False, indent=2),
            }
        ],
        "isError": is_error,
    }


def file_version(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    script = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8;"
        f"$v=(Get-Item -LiteralPath {json.dumps(str(path))}).VersionInfo;"
        "[PSCustomObject]@{"
        "FileVersion=$v.FileVersion;"
        "ProductVersion=$v.ProductVersion;"
        "ProductName=$v.ProductName;"
        "CompanyName=$v.CompanyName;"
        "FileDescription=$v.FileDescription"
        "} | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
        )
    except Exception as exc:
        return {"error": str(exc)}

    if completed.returncode != 0:
        return {"error": completed.stderr.decode("utf-8", errors="replace").strip()}
    text = completed.stdout.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def find_installation_data() -> dict[str, Any]:
    env_exe = os.environ.get("OWEN_LOGIC_EXE")
    candidates: list[Path] = []
    if env_exe:
        candidates.append(Path(env_exe))
    candidates.append(DEFAULT_EXE)
    candidates.append(Path(r"C:\Program Files (x86)\OWEN\OWEN Logic\ProgramRelayFBD.exe"))

    seen: set[str] = set()
    normalized: list[Path] = []
    for candidate in candidates:
        key = str(candidate).lower()
        if key not in seen:
            seen.add(key)
            normalized.append(candidate)

    installed = [path for path in normalized if path.exists()]
    exe = installed[0] if installed else normalized[0]
    install_dir = exe.parent if exe.exists() else None
    converter = DEFAULT_CONVERTER_EXE if DEFAULT_CONVERTER_EXE.exists() else None

    return {
        "found": bool(installed),
        "executable": str(exe),
        "install_dir": str(install_dir) if install_dir else None,
        "converter_executable": str(converter) if converter else None,
        "version": file_version(exe) if exe.exists() else None,
        "converter_version": file_version(converter) if converter else None,
        "checked_candidates": [str(path) for path in normalized],
    }


def require_windows() -> None:
    if user32 is None:
        raise RuntimeError("OWEN Logic GUI tools are available only on Windows")


def enum_windows(
    include_invisible: bool = False,
    pid: int | None = None,
    title_filter: str | None = None,
    owen_only: bool = True,
) -> list[dict[str, Any]]:
    require_windows()
    results: list[dict[str, Any]] = []
    title_filter_lower = title_filter.lower() if title_filter else None

    enum_proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd: wintypes.HWND, _lparam: wintypes.LPARAM) -> bool:
        visible = bool(user32.IsWindowVisible(hwnd))
        if not include_invisible and not visible:
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, length + 1)
        title = title_buffer.value

        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buffer, 256)
        class_name = class_buffer.value

        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        process_id_int = int(process_id.value)

        if pid is not None and process_id_int != int(pid):
            return True
        if title_filter_lower and title_filter_lower not in title.lower():
            return True
        if owen_only:
            marker = f"{title} {class_name}".lower()
            if "owen" not in marker and "programrelayfbd" not in marker:
                return True

        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width = int(rect.right - rect.left)
        height = int(rect.bottom - rect.top)
        if not include_invisible and (width <= 0 or height <= 0):
            return True

        results.append(
            {
                "hwnd": int(hwnd),
                "pid": process_id_int,
                "title": title,
                "class_name": class_name,
                "visible": visible,
                "rect": {
                    "left": int(rect.left),
                    "top": int(rect.top),
                    "right": int(rect.right),
                    "bottom": int(rect.bottom),
                    "width": width,
                    "height": height,
                },
            }
        )
        return True

    user32.EnumWindows(enum_proc_type(callback), 0)
    return results


def tasklist_programrelay() -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq ProgramRelayFBD.exe", "/FO", "CSV", "/NH"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    rows: list[dict[str, Any]] = []
    if completed.returncode != 0:
        return [{"error": completed.stderr.strip()}]
    text = completed.stdout.strip()
    if not text or text.startswith("INFO:"):
        return []
    for row in csv.reader(text.splitlines()):
        if len(row) >= 5:
            try:
                pid = int(row[1])
            except ValueError:
                pid = None
            rows.append(
                {
                    "image_name": row[0],
                    "pid": pid,
                    "session_name": row[2],
                    "session_number": row[3],
                    "memory_usage": row[4],
                }
            )
    return rows


def launch_owen_logic(args: dict[str, Any]) -> dict[str, Any]:
    install = find_installation_data()
    exe = Path(args.get("exe_path") or install["executable"])
    if not exe.exists():
        raise FileNotFoundError(f"OWEN Logic executable not found: {exe}")

    command = [str(exe)]
    project_path = args.get("project_path")
    if project_path:
        project = Path(project_path).expanduser().resolve()
        if not project.exists():
            raise FileNotFoundError(f"Project file not found: {project}")
        command.append(str(project))

    proc = subprocess.Popen(command, cwd=str(exe.parent))
    wait_seconds = float(args.get("wait_seconds", 5))
    if wait_seconds > 0:
        time.sleep(min(wait_seconds, 60))

    return {
        "pid": proc.pid,
        "command": command,
        "windows": enum_windows(pid=proc.pid, owen_only=False),
    }


def select_window(args: dict[str, Any], owen_only: bool = True) -> dict[str, Any]:
    windows = enum_windows(
        include_invisible=False,
        pid=args.get("pid"),
        title_filter=args.get("title_filter"),
        owen_only=owen_only,
    )
    if not windows and owen_only:
        windows = enum_windows(
            include_invisible=False,
            pid=args.get("pid"),
            title_filter=args.get("title_filter"),
            owen_only=False,
        )
    if not windows:
        raise RuntimeError("No matching OWEN Logic window found")
    windows.sort(key=lambda item: (not bool(item.get("title")), -item["rect"]["width"] * item["rect"]["height"]))
    return windows[0]


def focus_window(args: dict[str, Any]) -> dict[str, Any]:
    require_windows()
    window = select_window(args)
    hwnd = wintypes.HWND(window["hwnd"])
    SW_RESTORE = 9
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    return {"focused": True, "window": window}


def screenshot_window(args: dict[str, Any]) -> dict[str, Any]:
    try:
        from PIL import ImageGrab
    except Exception as exc:
        raise RuntimeError("Pillow ImageGrab is required for screenshots") from exc

    window = select_window(args)
    rect = window["rect"]
    bbox = (rect["left"], rect["top"], rect["right"], rect["bottom"])
    image = ImageGrab.grab(bbox=bbox)

    output_path = args.get("output_path")
    if output_path:
        output = Path(output_path).expanduser().resolve()
    else:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = SCREENSHOT_DIR / f"owen_logic_{stamp}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return {"output_path": str(output), "window": window, "size": image.size}


VK_CODES: dict[str, int] = {
    "CTRL": 0x11,
    "CONTROL": 0x11,
    "ALT": 0x12,
    "SHIFT": 0x10,
    "WIN": 0x5B,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "TAB": 0x09,
    "SPACE": 0x20,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "DEL": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
}
for code in range(ord("A"), ord("Z") + 1):
    VK_CODES[chr(code)] = code
for code in range(ord("0"), ord("9") + 1):
    VK_CODES[chr(code)] = code


def key_to_vk(key: str) -> int:
    normalized = key.strip().upper()
    if normalized in VK_CODES:
        return VK_CODES[normalized]
    if len(normalized) == 1:
        vk = user32.VkKeyScanW(ord(normalized)) & 0xFF
        if vk != 0xFF:
            return int(vk)
    raise ValueError(f"Unsupported key: {key}")


def send_hotkey(args: dict[str, Any]) -> dict[str, Any]:
    require_windows()
    keys = args.get("keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError("'keys' must be a non-empty array")

    focused = focus_window(args)
    delay_ms = int(args.get("delay_ms", 200))
    if delay_ms > 0:
        time.sleep(min(delay_ms, 5000) / 1000)

    KEYEVENTF_KEYUP = 0x0002
    vk_codes = [key_to_vk(str(key)) for key in keys]

    for vk in vk_codes:
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.03)
    for vk in reversed(vk_codes):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.03)

    return {"sent": keys, "window": focused["window"]}


def smoke_test(args: dict[str, Any]) -> dict[str, Any]:
    install = find_installation_data()
    if not install["found"]:
        raise FileNotFoundError("OWEN Logic installation was not found")

    launch_if_needed = bool(args.get("launch_if_needed", True))
    timeout_seconds = float(args.get("timeout_seconds", 20))
    deadline = time.time() + max(1, min(timeout_seconds, 120))
    windows = enum_windows()
    launch = None

    if not windows and launch_if_needed:
        launch_args: dict[str, Any] = {"wait_seconds": 1}
        if args.get("project_path"):
            launch_args["project_path"] = args["project_path"]
        launch = launch_owen_logic(launch_args)

    while time.time() < deadline:
        windows = enum_windows()
        if windows:
            break
        time.sleep(0.5)

    if not windows:
        raise RuntimeError("OWEN Logic did not expose a matching window before timeout")

    screenshot_data = None
    if bool(args.get("screenshot", True)):
        screenshot_data = screenshot_window({})

    return {
        "ok": True,
        "installation": install,
        "launch": launch,
        "windows": windows,
        "screenshot": screenshot_data,
    }


def call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = arguments or {}
    if name == "owen_logic_find_installation":
        return tool_result(find_installation_data())
    if name == "owen_logic_list_windows":
        return tool_result(
            enum_windows(
                include_invisible=bool(args.get("include_invisible", False)),
                pid=args.get("pid"),
                title_filter=args.get("title_filter"),
                owen_only=bool(args.get("owen_only", True)),
            )
        )
    if name == "owen_logic_list_processes":
        processes = tasklist_programrelay()
        windows: list[dict[str, Any]] = []
        for process in processes:
            process_id = process.get("pid")
            if isinstance(process_id, int):
                windows.extend(enum_windows(pid=process_id, owen_only=False))
        return tool_result({"processes": processes, "windows": windows})
    if name == "owen_logic_launch":
        return tool_result(launch_owen_logic(args))
    if name == "owen_logic_screenshot":
        return tool_result(screenshot_window(args))
    if name == "owen_logic_focus_window":
        return tool_result(focus_window(args))
    if name == "owen_logic_send_hotkey":
        return tool_result(send_hotkey(args))
    if name == "owen_logic_smoke_test":
        return tool_result(smoke_test(args))
    raise KeyError(f"Unknown tool: {name}")


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")

    if method == "initialize":
        protocol = (message.get("params") or {}).get("protocolVersion", "2024-11-05")
        return rpc_result(
            request_id,
            {
                "protocolVersion": protocol,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return rpc_result(request_id, {})
    if method == "tools/list":
        return rpc_result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        try:
            result = call_tool(str(name), params.get("arguments") or {})
        except Exception as exc:
            result = tool_result({"error": str(exc), "tool": name}, is_error=True)
        return rpc_result(request_id, result)

    if request_id is None:
        return None
    return rpc_error(request_id, -32601, f"Method not found: {method}")


def main() -> int:
    while True:
        try:
            message = read_message()
            if message is None:
                return 0
            response = handle_request(message)
            if response is not None:
                send_message(response)
        except Exception as exc:
            print(f"{SERVER_NAME}: {exc}", file=sys.stderr, flush=True)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
