#!/usr/bin/env python3
"""Cross-platform transcript list and scan CLI."""

from __future__ import annotations

import argparse
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
    command = [node, str(root / "scripts" / "semantic.mjs"), "list" if args.list else "scan"]
    options = {"--project": args.project}
    if args.list:
        options["--limit"] = args.max_msgs
    else:
        options.update({"--id": args.session_id_flag or args.session_id, "--path": args.path,
                        "--tail": args.tail, "--max-msgs": args.max_msgs, "--detail-line": args.detail})
    for name, value in options.items():
        if value is not None:
            command.extend([name, str(value)])
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
