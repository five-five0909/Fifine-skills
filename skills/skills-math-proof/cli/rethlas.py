#!/usr/bin/env python3
"""
Rethlas CLI — AI math-proving system runner.

Usage:
  python cli/rethlas.py prove   <problem> [--max-iter N]
  python cli/rethlas.py serve   [--port PORT] [--json]
  python cli/rethlas.py stop    [--port PORT] [--json]
  python cli/rethlas.py status  [--port PORT] [--json]
  python cli/rethlas.py results [problem]    [--json]
  python cli/rethlas.py new     <name>       [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

ROOT         = Path(__file__).resolve().parents[1]
GEN          = ROOT / "agents" / "generation"
CLI          = ROOT / "cli"
PID_FILE     = ROOT / ".verify_service.pid"
ORCHESTRATOR = CLI / "orchestrate.py"

# ── Helpers ────────────────────────────────────────────────────────────────────

def out_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False))


def die(msg: str, code: int = 1) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)


def service_up(port: int) -> bool:
    try:
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def resolve_problem_path(raw: str) -> tuple[str, Path]:
    """Return (relative_data_path, absolute_path). Dies if not found."""
    if ".." in raw:
        die(f"Path must not contain '..': {raw}")
    p = raw.replace("\\", "/")
    if not p.startswith("data/"):
        p = f"data/{p}"
    if not p.endswith(".md"):
        p = f"{p}.md"
    abs_path = GEN / p.replace("/", os.sep)
    if not abs_path.exists():
        die(f"Problem file not found: {abs_path}")
    return p, abs_path


def make_slug(prob_id: str) -> str:
    slug = re.sub(r"[/\\]", "-", prob_id)
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    return slug


def find_proof_dirs(search_root: Path) -> tuple[list[str], list[str]]:
    """Scan search_root for subdirs that contain blueprint files."""
    verified, drafts = [], []
    if not search_root.is_dir():
        return verified, drafts
    for child in sorted(search_root.iterdir()):
        if not child.is_dir():
            continue
        v = child / "blueprint_verified.md"
        d = child / "blueprint.md"
        if v.exists():
            verified.append(child.name)
        elif d.exists():
            drafts.append(child.name)
    return verified, drafts


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> None:
    port    = args.port
    up      = service_up(port)
    url     = f"http://127.0.0.1:{port}"
    python  = shutil.which("python") or shutil.which("python3")
    bash    = shutil.which("bash")
    cwd     = Path.cwd()
    verified, drafts = find_proof_dirs(cwd)

    if args.json:
        out_json({
            "verify_service": {"running": up, "url": url},
            "python":         python,
            "bash":           bash,
            "verified_count": len(verified),
            "draft_count":    len(drafts),
        })
    else:
        print()
        print("── Rethlas Status ──────────────────────────────────")
        print(f"  verify_service ({url}): {'running' if up else 'not running'}")
        print(f"  python : {python or 'not found'}")
        print(f"  bash   : {bash or 'not found'}")
        print(f"  verified proofs (cwd) : {len(verified)}")
        print(f"  draft proofs    (cwd) : {len(drafts)}")
        print("────────────────────────────────────────────────────")
        print()


def cmd_serve(args: argparse.Namespace) -> None:
    # Verification is done in-context by Claude Code — no external service needed.
    msg = "Verification is done in-context by Claude Code. No external service required."
    if args.json:
        out_json({"started": False, "in_context": True, "message": msg})
    else:
        print(f"[INFO] {msg}")


def cmd_stop(args: argparse.Namespace) -> None:
    port    = args.port
    stopped = False
    pid     = None

    # Try PID file first
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True, check=False)
            else:
                os.kill(pid, signal.SIGTERM)
            stopped = True
        except Exception:
            pass
        PID_FILE.unlink(missing_ok=True)

    # Fallback: kill whatever is listening on the port (Windows only)
    if not stopped and sys.platform == "win32":
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, check=False
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = int(parts[-1])
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                                   capture_output=True, check=False)
                    stopped = True
                    break
        except Exception:
            pass

    if args.json:
        out_json({"stopped": stopped, "port": port, "pid": pid})
    elif stopped:
        print(f"[OK]   Stopped service on port {port} (pid={pid}).")
    else:
        print(f"[INFO] No service found on port {port}.")


def cmd_results(args: argparse.Namespace) -> None:
    cwd = Path.cwd()

    if args.problem:
        slug      = make_slug(args.problem.replace("data/", "").replace(".md", ""))
        out_dir   = cwd / slug
        v_path    = out_dir / "blueprint_verified.md"
        d_path    = out_dir / "blueprint.md"

        if args.json:
            content, state = None, "none"
            if v_path.exists():
                content = v_path.read_text(encoding="utf-8")
                state   = "verified"
            elif d_path.exists():
                content = d_path.read_text(encoding="utf-8")
                state   = "draft"
            out_json({"problem_id": slug, "state": state, "content": content})
        elif v_path.exists():
            print(f"── Verified proof: {slug} ──")
            print(v_path.read_text(encoding="utf-8"))
        elif d_path.exists():
            print("[WARN] Draft only:")
            print(d_path.read_text(encoding="utf-8"))
        else:
            print(f"No results for '{slug}'.")
    else:
        verified, drafts = find_proof_dirs(cwd)
        if args.json:
            out_json({"verified": verified, "drafts": drafts})
        else:
            print()
            print("── Proof Results (current directory) ────────────────")
            print(f"Verified ({len(verified)}):")
            for v in verified:
                print(f"  [V] {v}")
            print(f"Draft only ({len(drafts)}):")
            for d in drafts:
                print(f"  [D] {d}")
            print("─────────────────────────────────────────────────────")
            print()


def cmd_new(args: argparse.Namespace) -> None:
    if not args.name:
        die("'new' requires a name, e.g.: rethlas new my_problem")

    safe = re.sub(r"[^a-zA-Z0-9_/\-]", "_", args.name)
    dest = GEN / "data" / safe.replace("/", os.sep)
    if not dest.suffix:
        dest = dest.with_suffix(".md")
    if dest.exists():
        die(f"File already exists: {dest}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f"# Problem: {safe}\n\n"
        "## Statement\n\n"
        "<!-- Write the complete formal or informal statement of the math problem here. -->\n\n"
        "## Notes\n\n"
        "<!-- Optional: background context, known partial results, or hints. -->\n",
        encoding="utf-8",
    )

    rel_path = f"agents/generation/data/{safe.replace(os.sep, '/')}.md"
    if args.json:
        out_json({"created": True, "path": str(dest), "relative": rel_path})
    else:
        print(f"[OK]   Created: {dest}")
        print(f"       Edit the file, then run: python cli/rethlas.py prove {safe}")


def cmd_prove(args: argparse.Namespace) -> None:
    if not args.problem:
        die("'prove' requires a problem path, e.g.: rethlas prove example.md")

    rel_path, prob_abs = resolve_problem_path(args.problem)
    prob_id   = re.sub(r"^data/", "", rel_path).removesuffix(".md")
    slug      = make_slug(prob_id)
    port      = args.port
    verify_url = f"http://127.0.0.1:{port}"

    # Output lives in <user-cwd>/<slug>/
    cwd           = Path.cwd()
    out_dir       = cwd / slug
    draft_path    = out_dir / "blueprint.md"
    verified_path = out_dir / "blueprint_verified.md"
    memory_dir    = out_dir / "memory"
    problem_copy  = out_dir / "problem.md"
    agents_md     = GEN / "AGENTS.md"
    ref_dir       = GEN / "data" / f"{prob_id}.refs"
    pipeline_state = out_dir / ".pipeline_state.json"

    # Create folder structure
    out_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Copy problem file (once)
    if not problem_copy.exists():
        shutil.copy2(prob_abs, problem_copy)

    verify_up    = service_up(port)
    has_refs     = ref_dir.exists()
    has_verified = verified_path.exists()
    has_draft    = draft_path.exists()

    # Set RETHLAS_MEMORY_ROOT so MCP server writes here
    os.environ["RETHLAS_MEMORY_ROOT"] = str(memory_dir)

    # Initialize or resume orchestrator
    orchestrator_cmd = f'python "{ORCHESTRATOR}"'
    init_instruction = None
    try:
        if not pipeline_state.exists():
            raw = subprocess.check_output(
                [sys.executable, str(ORCHESTRATOR), "init", str(out_dir), prob_id,
                 "--max-iter", str(args.max_iter)],
                text=True, stderr=subprocess.DEVNULL,
            )
        else:
            raw = subprocess.check_output(
                [sys.executable, str(ORCHESTRATOR), "next", str(out_dir)],
                text=True, stderr=subprocess.DEVNULL,
            )
        init_instruction = json.loads(raw)
    except Exception:
        pass

    result = {
        "problem_id":          prob_id,
        "slug":                slug,
        "problem_file":        str(problem_copy),
        "agents_md":           str(agents_md),
        "output_dir":          str(out_dir),
        "draft_path":          str(draft_path),
        "verified_path":       str(verified_path),
        "memory_dir":          str(memory_dir),
        "rethlas_memory_root": str(memory_dir),
        "ref_dir":             str(ref_dir) if has_refs else None,
        "verify_service":      {"running": verify_up, "url": verify_url},
        "already_verified":    has_verified,
        "has_draft":           has_draft,
        "mcp_server_cmd":      f'python "{GEN / "mcp" / "server.py"}"',
        "orchestrator": {
            "cmd":           orchestrator_cmd,
            "pipeline_state": str(pipeline_state),
            "current_stage": init_instruction,
        },
    }

    # prove always emits JSON (Claude Code needs structured output)
    out_json(result)


# ── Entry point ────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    # Shared flags inherited by every subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--port", type=int, default=8091, help="Verification service port")
    common.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    p = argparse.ArgumentParser(
        prog="rethlas",
        description="Rethlas CLI — AI math-proving system runner.",
        parents=[common],
    )

    sub = p.add_subparsers(dest="command", required=True)

    # prove
    sp = sub.add_parser("prove", parents=[common], help="Set up a proof session")
    sp.add_argument("problem", help="Problem filename (relative to agents/generation/data/)")
    sp.add_argument("--max-iter", type=int, default=10)

    # serve
    sub.add_parser("serve", parents=[common], help="Start the verification service")

    # stop
    sub.add_parser("stop", parents=[common], help="Stop the verification service")

    # status
    sub.add_parser("status", parents=[common], help="Show system status")

    # results
    sp = sub.add_parser("results", parents=[common], help="List or show proof results")
    sp.add_argument("problem", nargs="?", default=None, help="Problem name to inspect")

    # new
    sp = sub.add_parser("new", parents=[common], help="Create a new problem file")
    sp.add_argument("name", help="Problem name, e.g. algebra/my_theorem")

    return p


COMMANDS = {
    "prove":   cmd_prove,
    "serve":   cmd_serve,
    "stop":    cmd_stop,
    "status":  cmd_status,
    "results": cmd_results,
    "new":     cmd_new,
}

if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()
    COMMANDS[args.command](args)
