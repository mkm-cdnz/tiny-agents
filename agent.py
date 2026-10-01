#!/usr/bin/env python3
"""Minimal OpenAI-compatible tool-calling agent for small local models."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = os.getenv("TINY_AGENTS_URL", "http://127.0.0.1:8080/v1").rstrip("/")
MODEL = os.getenv("TINY_AGENTS_MODEL", "local-model")
MAX_STEPS = int(os.getenv("TINY_AGENTS_MAX_STEPS", "8"))
WORKSPACE = Path(os.getenv("TINY_AGENTS_WORKSPACE", "workspace")).resolve()

SYSTEM_PROMPT = """You are a compact local assistant. Use tools when needed.
Never invent tool results. Keep answers concise. File tools are confined to a
workspace; explain when a requested path is outside it."""

TOOLS = [
    {"type": "function", "function": {
        "name": "system_info",
        "description": "Return basic host, Python, memory and disk information.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "list_files",
        "description": "List files in a directory inside the agent workspace.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative directory path"}},
            "additionalProperties": False},
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a UTF-8 text file inside the agent workspace.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative file path"}},
            "required": ["path"], "additionalProperties": False},
    }},
]


def safe_path(relative: str) -> Path:
    candidate = (WORKSPACE / relative).resolve()
    if candidate != WORKSPACE and WORKSPACE not in candidate.parents:
        raise ValueError("path escapes the workspace")
    return candidate


def memory_info() -> dict[str, int] | None:
    try:
        values: dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0]) * 1024
        return {"total_bytes": values["MemTotal"], "available_bytes": values["MemAvailable"]}
    except (OSError, KeyError, ValueError):
        return None


def run_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        if name == "system_info":
            usage = shutil.disk_usage(WORKSPACE)
            return {"hostname": platform.node(), "platform": platform.platform(),
                    "python": platform.python_version(), "memory": memory_info(),
                    "disk_free_bytes": usage.free}
        if name == "list_files":
            target = safe_path(str(arguments.get("path", ".")))
            if not target.is_dir():
                raise ValueError("path is not a directory")
            return {"entries": [p.name + ("/" if p.is_dir() else "")
                                for p in sorted(target.iterdir())][:200]}
        if name == "read_file":
            target = safe_path(str(arguments["path"]))
            if not target.is_file():
                raise ValueError("path is not a file")
            if target.stat().st_size > 128_000:
                raise ValueError("file exceeds the 128 KB limit")
            return {"content": target.read_text(encoding="utf-8")}
        raise ValueError(f"unknown tool: {name}")
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        return {"error": str(exc)}


def chat(messages: list[dict[str, Any]]) -> dict[str, Any]:
    body = json.dumps({"model": MODEL, "messages": messages, "tools": TOOLS,
                       "tool_choice": "auto", "temperature": 0.1,
                       "stream": False}).encode()
    request = urllib.request.Request(f"{API_ROOT}/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach model server at {API_ROOT}: {exc}") from exc
    return payload["choices"][0]["message"]


def answer(prompt: str) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    for _ in range(MAX_STEPS):
        message = chat(messages)
        messages.append(message)
        calls = message.get("tool_calls") or []
        if not calls:
            return str(message.get("content") or "")
        for call in calls:
            function = call.get("function", {})
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError as exc:
                result = {"error": f"invalid tool arguments: {exc}"}
            else:
                result = run_tool(str(function.get("name", "")), arguments)
            messages.append({"role": "tool", "tool_call_id": call.get("id", "unknown"),
                             "content": json.dumps(result, ensure_ascii=False)})
    return f"Stopped after {MAX_STEPS} tool iterations."


def main() -> int:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        print(answer(" ".join(sys.argv[1:])))
        return 0
    print("tiny-agents (Ctrl-D or 'exit' to quit)")
    while True:
        try:
            prompt = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if prompt.lower() in {"exit", "quit"}:
            return 0
        if prompt:
            try:
                print(answer(prompt))
            except (RuntimeError, KeyError, ValueError) as exc:
                print(f"error: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
