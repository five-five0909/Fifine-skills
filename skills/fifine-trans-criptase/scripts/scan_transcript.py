#!/usr/bin/env python3
"""Cross-platform CLI adapter for the trans_scan and trans_list MCP tools."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List or scan Claude Code and Codex session transcripts."
    )
    parser.add_argument("session_id", nargs="?", help="Session UUID or prefix")
    parser.add_argument("--id", dest="session_id_flag", help="Session UUID or prefix")
    parser.add_argument("--list", action="store_true", help="List candidate sessions")
    parser.add_argument("--path", help="Transcript file path")
    parser.add_argument("--project", help="Project path; defaults to the current directory")
    parser.add_argument("--tail", type=int, default=60, help="Tail record count")
    parser.add_argument("--max-msgs", type=int, default=60, help="Maximum user messages")
    parser.add_argument("--detail", type=int, help="Breakpoint detail anchor line")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    node = shutil.which("node")
    if not node:
        print("error: Node.js is required to run the bundled transcript parser.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parent.parent
    method = "trans_list" if args.list else "trans_scan"
    if args.list:
        arguments = {"limit": args.max_msgs}
    else:
        arguments = {
            "id": args.session_id_flag or args.session_id,
            "path": args.path,
            "tail": args.tail,
            "maxMsgs": args.max_msgs,
            "detailLine": args.detail,
        }
    if args.project:
        arguments["project"] = args.project
    arguments = {key: value for key, value in arguments.items() if value is not None}
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": method, "arguments": arguments},
    }
    result = subprocess.run(
        [node, str(root / "mcp" / "server.mjs")],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        print(result.stderr.strip() or "error: MCP server exited unexpectedly.", file=sys.stderr)
        return result.returncode
    try:
        response = json.loads(next(line for line in result.stdout.splitlines() if line.strip()))
        content = response["result"]["content"][0]["text"]
    except (KeyError, StopIteration, json.JSONDecodeError) as error:
        print(f"error: invalid MCP response: {error}", file=sys.stderr)
        return 1
    print(content)
    return 1 if response.get("result", {}).get("isError") else 0


if __name__ == "__main__":
    raise SystemExit(main())
