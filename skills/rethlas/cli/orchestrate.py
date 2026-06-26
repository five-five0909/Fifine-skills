#!/usr/bin/env python3
"""
Rethlas proof orchestrator.

Enforces the exact stage order and branching logic from AGENTS.md.
Claude Code IS the reasoning agent — it executes each stage instruction,
then calls `advance` to move the pipeline forward.

Usage:
  python orchestrate.py init          <output_dir> <problem_id> [--max-iter N]
  python orchestrate.py next          <output_dir>
  python orchestrate.py advance       <output_dir> <result>   # result: ok | solved | fail
  python orchestrate.py status        <output_dir>
  python orchestrate.py note          <output_dir> <text>
  python orchestrate.py verify-prep   <output_dir>
  python orchestrate.py verify-record <output_dir> <verdict> <summary> [--errors JSON]
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Stage definitions ──────────────────────────────────────────────────────────

STAGES = [
    "INIT",             # memory_init, read problem
    "EXPLORE",          # search + immediate conclusions + examples/counterexamples
    "PLAN",             # propose ≥2 subgoal decomposition plans
    "DIRECT_PROVE",     # direct-proving on all plans
    "RECURSIVE_PROVE",  # recursive-proving when direct failed
    "IDENTIFY_FAILURES",# identify common stuck points across all failed plans
    "REPLAN",           # propose new plans from failure analysis
    "VERIFY",           # verify_proof_service on assembled blueprint
    "REPAIR",           # repair blueprint using verification report
    "DONE",             # blueprint_verified.md produced
    "EXHAUSTED",        # max iterations reached without success
]

STATE_FILE = ".pipeline_state.json"


# ── State dataclass ────────────────────────────────────────────────────────────

@dataclass
class PipelineState:
    problem_id: str
    output_dir: str
    memory_dir: str
    verify_url: str
    stage: str = "INIT"
    iteration: int = 0              # outer iteration counter
    max_iterations: int = 10
    direct_prove_attempts: int = 0
    recursive_prove_attempts: int = 0
    verify_attempts: int = 0
    replan_count: int = 0
    max_replans: int = 3
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""                 # Claude can write free-form notes here

    def save(self, output_dir: Path) -> None:
        self.updated_at = _now()
        (output_dir / STATE_FILE).write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, output_dir: Path) -> "PipelineState":
        data = json.loads((output_dir / STATE_FILE).read_text(encoding="utf-8"))
        return cls(**data)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── Stage instructions returned to Claude Code ─────────────────────────────────

def _instruction(state: PipelineState) -> dict:
    """Return the action Claude Code must perform for the current stage."""
    base = {
        "stage":      state.stage,
        "iteration":  state.iteration,
        "problem_id": state.problem_id,
        "output_dir": state.output_dir,
        "memory_dir": state.memory_dir,
        "verify_url": state.verify_url,
        "draft_path": str(Path(state.output_dir) / "blueprint.md"),
        "verified_path": str(Path(state.output_dir) / "blueprint_verified.md"),
        "problem_file": str(Path(state.output_dir) / "problem.md"),
    }

    if state.stage == "INIT":
        base.update({
            "action": "initialize",
            "instruction": (
                f"1. Call memory_init(problem_id='{state.problem_id}') to set up all memory channels.\n"
                f"2. Read the problem file at: {base['problem_file']}\n"
                f"3. Read AGENTS.md for the full operating rules.\n"
                f"4. Read all skill SKILL.md files under agents/generation/.agents/skills/ to know what each skill does.\n"
                "When done → call: advance ok"
            ),
            "advance_options": ["ok"],
        })

    elif state.stage == "EXPLORE":
        base.update({
            "action": "explore",
            "instruction": (
                "Gather all information needed before planning. Apply skills in this order:\n"
                "  1. $obtain-immediate-conclusions — rewrite/reformulate the problem, extract easy facts.\n"
                "  2. $search-math-results — search leansearch.net and arXiv for relevant theorems, lemmas, constructions.\n"
                "  3. $construct-toy-examples — build simple examples to develop intuition.\n"
                "  4. $construct-counterexamples — test whether the statement might be false or needs extra hypotheses.\n"
                "  5. $query-memory — check if earlier runs stored useful artifacts.\n"
                "Persist EVERY artifact to memory with memory_append.\n"
                "Apply each skill at least once. Repeat search if the first round is thin.\n"
                "When you have enough background to propose multiple proof strategies → call: advance ok"
            ),
            "advance_options": ["ok"],
        })

    elif state.stage == "PLAN":
        base.update({
            "action": "propose_plans",
            "instruction": (
                "Apply $propose-subgoal-decomposition-plans.\n"
                "Requirements:\n"
                "  • Propose AT LEAST 2 materially different decomposition plans.\n"
                "  • Each plan must break the theorem into concrete, verifiable subgoals.\n"
                "  • Plans must differ in strategy (e.g. induction vs. direct construction vs. contradiction).\n"
                "  • Persist all plans to the 'subgoals' memory channel.\n"
                "When ≥2 plans are persisted → call: advance ok"
            ),
            "advance_options": ["ok"],
        })

    elif state.stage == "DIRECT_PROVE":
        base.update({
            "action": "direct_prove",
            "attempt": state.direct_prove_attempts + 1,
            "instruction": (
                "Apply $direct-proving on ALL decomposition plans from the 'subgoals' channel.\n"
                "Rules:\n"
                "  • Try each plan fully before declaring it stuck.\n"
                "  • For each stuck subgoal, immediately try $construct-counterexamples before giving up.\n"
                "  • Record each subgoal attempt in 'proof_steps' channel: status solved|partial|stuck.\n"
                "  • If ANY plan is FULLY solved → assemble the complete proof in blueprint.md,\n"
                "    then call: advance solved\n"
                "  • If ALL plans remain unsolved → call: advance fail"
            ),
            "advance_options": ["solved", "fail"],
        })

    elif state.stage == "RECURSIVE_PROVE":
        base.update({
            "action": "recursive_prove",
            "attempt": state.recursive_prove_attempts + 1,
            "instruction": (
                "Apply $recursive-proving. Spawn one sub-agent per decomposition plan to work in parallel.\n"
                "Rules:\n"
                "  • Each sub-agent works on one plan independently.\n"
                "  • Sub-agents may use any skill ($search-math-results, $construct-counterexamples, etc.).\n"
                "  • All sub-agent artifacts must be persisted to memory.\n"
                "  • If any sub-agent fully solves its plan → assemble blueprint.md and call: advance solved\n"
                "  • If all sub-agents fail → call: advance fail"
            ),
            "advance_options": ["solved", "fail"],
        })

    elif state.stage == "IDENTIFY_FAILURES":
        base.update({
            "action": "identify_failures",
            "instruction": (
                "Apply $identify-key-failures.\n"
                "Rules:\n"
                "  • Analyze ALL failed plans and stuck subgoals in proof_steps and failed_paths channels.\n"
                "  • Identify the COMMON obstruction — the real mathematical difficulty.\n"
                "  • Be concrete: name the missing lemma, the failing construction, the blocking counterexample.\n"
                "  • Persist a 'failed_paths' record with the identified common stuck points.\n"
                "  • Persist a 'big_decisions' record summarizing what has been learned.\n"
                "When failure analysis is complete → call: advance ok"
            ),
            "advance_options": ["ok"],
        })

    elif state.stage == "REPLAN":
        base.update({
            "action": "replan",
            "replan_count": state.replan_count + 1,
            "max_replans": state.max_replans,
            "instruction": (
                "Propose a NEW generation of decomposition plans informed by the failure analysis.\n"
                "Rules:\n"
                "  • The new plans MUST differ from all previous plans (read failed_paths to verify).\n"
                "  • Address the identified common obstruction directly.\n"
                "  • Propose AT LEAST 2 new materially different plans.\n"
                "  • Persist to 'subgoals' channel with clear labels distinguishing from old plans.\n"
                "When ≥2 new plans are persisted → call: advance ok"
            ),
            "advance_options": ["ok"],
        })

    elif state.stage == "VERIFY":
        base.update({
            "action": "verify",
            "attempt": state.verify_attempts + 1,
            "instruction": (
                "YOU (Claude Code, this session) are the verifier. Follow these steps exactly:\n\n"
                "  STEP 1 — Let Python parse the blueprint structure:\n"
                f"    python orchestrate.py verify-prep {base['output_dir']}\n"
                "    This returns a JSON with sections[] and checklist[].\n\n"
                "  STEP 2 — For each item in checklist[], reason through it:\n"
                "    • Read the statement and proof of that section.\n"
                "    • Check every logical step: is it valid? complete? are all cases handled?\n"
                "    • Note any errors (with location) or gaps.\n"
                "    Take as much reasoning space as needed — this is where YOUR intelligence applies.\n\n"
                "  STEP 3 — Record your verdict via Python:\n"
                f"    python orchestrate.py verify-record {base['output_dir']} <verdict> \"<summary>\"\n"
                "    Add --errors '[{\"location\":\"...\",\"description\":\"...\"}]' if any found.\n"
                "    verdict: correct | incorrect | incomplete\n\n"
                "  STEP 4 — Act on the result:\n"
                "    If verdict == 'correct':\n"
                f"      • Copy blueprint.md to: {base['verified_path']}\n"
                "      • Call: advance ok\n"
                "    Otherwise:\n"
                "      • Call: advance fail"
            ),
            "advance_options": ["ok", "fail"],
        })

    elif state.stage == "REPAIR":
        base.update({
            "action": "repair",
            "attempt": state.verify_attempts,
            "instruction": (
                "Repair the blueprint using the latest verification report.\n\n"
                "  STEP 1 — Retrieve the error list from memory:\n"
                f"    python orchestrate.py repair-context {base['output_dir']}\n"
                "    This returns the latest verification_reports entry (errors + gaps + repair_hints).\n\n"
                "  STEP 2 — Reason through each error/gap:\n"
                "    • Address CRITICAL errors first.\n"
                "    • Do NOT assume fixes are local — reconsider the proof strategy if needed.\n"
                "    • Use memory_search, search_arxiv_theorems, or construct new examples if stuck.\n\n"
                f"  STEP 3 — Rewrite the corrected proof to: {base['draft_path']}\n\n"
                "  STEP 4 — Call: advance ok"
            ),
            "advance_options": ["ok"],
        })

    elif state.stage == "DONE":
        base.update({
            "action": "done",
            "instruction": (
                f"Proof verified successfully.\n"
                f"Verified proof is at: {base['verified_path']}\n"
                "Present the proof to the user."
            ),
        })

    elif state.stage == "EXHAUSTED":
        base.update({
            "action": "exhausted",
            "instruction": (
                f"Reached maximum iterations ({state.max_iterations}) without a verified proof.\n"
                f"Best draft is at: {base['draft_path']}\n"
                "Report progress and failure summary to the user."
            ),
        })

    return base


# ── Transition logic ───────────────────────────────────────────────────────────

def _advance(state: PipelineState, result: str) -> PipelineState:
    """Apply transition rules and return the updated state."""
    s = state.stage

    if s == "INIT":
        state.stage = "EXPLORE"

    elif s == "EXPLORE":
        state.stage = "PLAN"

    elif s == "PLAN":
        state.stage = "DIRECT_PROVE"

    elif s == "DIRECT_PROVE":
        state.direct_prove_attempts += 1
        if result == "solved":
            state.stage = "VERIFY"
        elif result == "fail":
            if state.direct_prove_attempts == 1:
                state.stage = "RECURSIVE_PROVE"
            else:
                # Already tried recursive too — identify failures
                state.stage = "IDENTIFY_FAILURES"

    elif s == "RECURSIVE_PROVE":
        state.recursive_prove_attempts += 1
        if result == "solved":
            state.stage = "VERIFY"
        elif result == "fail":
            state.stage = "IDENTIFY_FAILURES"

    elif s == "IDENTIFY_FAILURES":
        if state.replan_count < state.max_replans:
            state.stage = "REPLAN"
        else:
            state.stage = "EXHAUSTED"

    elif s == "REPLAN":
        state.replan_count += 1
        state.iteration += 1
        if state.iteration >= state.max_iterations:
            state.stage = "EXHAUSTED"
        else:
            state.stage = "DIRECT_PROVE"

    elif s == "VERIFY":
        state.verify_attempts += 1
        if result == "ok":
            state.stage = "DONE"
        elif result == "fail":
            state.stage = "REPAIR"

    elif s == "REPAIR":
        if state.verify_attempts >= state.max_iterations:
            state.stage = "EXHAUSTED"
        else:
            state.stage = "VERIFY"

    elif s in ("DONE", "EXHAUSTED"):
        pass  # terminal states

    return state


# ── CLI commands ───────────────────────────────────────────────────────────────

def cmd_init(args: list[str]) -> None:
    if len(args) < 2:
        print("Usage: orchestrate.py init <output_dir> <problem_id> [--max-iter N]", file=sys.stderr)
        sys.exit(1)

    out = Path(args[0]).resolve()
    problem_id = args[1]
    max_iter = 10
    if "--max-iter" in args:
        max_iter = int(args[args.index("--max-iter") + 1])

    memory_dir = str(out / "memory")
    verify_url = "http://127.0.0.1:8091"

    state = PipelineState(
        problem_id=problem_id,
        output_dir=str(out),
        memory_dir=memory_dir,
        verify_url=verify_url,
        max_iterations=max_iter,
        created_at=_now(),
        updated_at=_now(),
    )
    out.mkdir(parents=True, exist_ok=True)
    state.save(out)
    print(json.dumps(_instruction(state), indent=2))


def cmd_next(args: list[str]) -> None:
    if not args:
        print("Usage: orchestrate.py next <output_dir>", file=sys.stderr)
        sys.exit(1)
    out = Path(args[0]).resolve()
    state = PipelineState.load(out)
    print(json.dumps(_instruction(state), indent=2))


def cmd_advance(args: list[str]) -> None:
    if len(args) < 2:
        print("Usage: orchestrate.py advance <output_dir> <ok|solved|fail>", file=sys.stderr)
        sys.exit(1)
    out    = Path(args[0]).resolve()
    result = args[1]
    state  = PipelineState.load(out)
    state  = _advance(state, result)
    state.save(out)
    # Print next instruction
    print(json.dumps(_instruction(state), indent=2))


def cmd_status(args: list[str]) -> None:
    if not args:
        print("Usage: orchestrate.py status <output_dir>", file=sys.stderr)
        sys.exit(1)
    out   = Path(args[0]).resolve()
    state = PipelineState.load(out)
    print(json.dumps(asdict(state), indent=2))


def cmd_note(args: list[str]) -> None:
    """Allow Claude Code to append a note to the pipeline state."""
    if len(args) < 2:
        print("Usage: orchestrate.py note <output_dir> <text>", file=sys.stderr)
        sys.exit(1)
    out  = Path(args[0]).resolve()
    text = " ".join(args[1:])
    state = PipelineState.load(out)
    state.notes = (state.notes + "\n" + text).strip()
    state.save(out)
    print(json.dumps({"saved": True, "notes": state.notes}))


# ── Blueprint parser ───────────────────────────────────────────────────────────

def _parse_blueprint(blueprint_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a blueprint.md into a list of sections.
    Recognises:   # lemma <id>   and   # theorem <id>
    Each section has: type, id, statement, proof
    """
    if not blueprint_path.exists():
        return []

    text = blueprint_path.read_text(encoding="utf-8")
    # Split on top-level headings that start a lemma/theorem block
    raw_sections = re.split(r"(?=^# (?:lemma|theorem|proposition|corollary)\b)", text, flags=re.MULTILINE)

    sections: List[Dict[str, Any]] = []
    for block in raw_sections:
        block = block.strip()
        if not block:
            continue

        # Match opening heading
        header_match = re.match(
            r"^# (lemma|theorem|proposition|corollary)\s+(\S+)", block, re.IGNORECASE
        )
        if not header_match:
            continue

        sec_type = header_match.group(1).lower()
        sec_id   = header_match.group(2)

        # Extract ## statement subsection
        stmt_match = re.search(
            r"^## statement\s*\n([\s\S]*?)(?=^##|\Z)", block, re.MULTILINE | re.IGNORECASE
        )
        # Extract ## proof subsection
        proof_match = re.search(
            r"^## proof\s*\n([\s\S]*?)(?=^##|\Z)", block, re.MULTILINE | re.IGNORECASE
        )

        sections.append({
            "type":      sec_type,
            "id":        sec_id,
            "statement": stmt_match.group(1).strip() if stmt_match else "",
            "proof":     proof_match.group(1).strip() if proof_match else "",
        })

    return sections


def _build_checklist(sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate one check item per section."""
    items = []
    for s in sections:
        items.append({
            "section_id": s["id"],
            "type":       s["type"],
            "check":      (
                f"Is the proof of {s['type']} '{s['id']}' logically complete and correct? "
                "Are all steps valid? Are all cases covered? "
                "Are cited results standard or proved earlier?"
            ),
        })
    return items


# ── verify-prep / verify-record commands ──────────────────────────────────────

def cmd_verify_prep(args: list[str]) -> None:
    """
    Parse blueprint.md and return a structured verification task for Claude Code.
    Claude Code works through each checklist item, then calls verify-record.
    """
    if not args:
        print("Usage: orchestrate.py verify-prep <output_dir>", file=sys.stderr)
        sys.exit(1)

    out   = Path(args[0]).resolve()
    state = PipelineState.load(out)
    draft = Path(state.output_dir) / "blueprint.md"

    sections  = _parse_blueprint(draft)
    checklist = _build_checklist(sections)

    print(json.dumps({
        "blueprint_path": str(draft),
        "section_count":  len(sections),
        "sections":       sections,
        "checklist":      checklist,
        "instruction": (
            "Go through each checklist item. For each section:\n"
            "  1. Read the statement and proof carefully.\n"
            "  2. Verify every logical step.\n"
            "  3. Record any errors or gaps (with location and description).\n"
            "When all sections are checked, call:\n"
            "  python orchestrate.py verify-record <output_dir> <verdict> \"<summary>\" "
            "[--errors '[{\"location\":\"...\",\"description\":\"...\"}]']\n"
            "verdict: correct | incorrect | incomplete"
        ),
    }, indent=2))


def cmd_verify_record(args: list[str]) -> None:
    """
    Record Claude Code's in-context verification verdict to memory.
    Usage: verify-record <output_dir> <verdict> <summary> [--errors JSON]
    verdict: correct | incomplete | incorrect
    """
    if len(args) < 3:
        print(
            "Usage: orchestrate.py verify-record <output_dir> <verdict> <summary> [--errors JSON]",
            file=sys.stderr,
        )
        sys.exit(1)

    out     = Path(args[0]).resolve()
    verdict = args[1]
    summary = args[2]

    if verdict not in ("correct", "incorrect", "incomplete"):
        print("verdict must be: correct | incorrect | incomplete", file=sys.stderr)
        sys.exit(1)

    errors: List[Dict[str, str]] = []
    if "--errors" in args:
        idx = args.index("--errors")
        try:
            errors = json.loads(args[idx + 1])
        except (IndexError, json.JSONDecodeError) as exc:
            print(f"--errors must be a valid JSON array: {exc}", file=sys.stderr)
            sys.exit(1)

    state = PipelineState.load(out)

    # Write verdict to verification_reports JSONL
    verdict_file = out / "memory" / _problem_memory_subdir(state) / "verification_reports.jsonl"
    verdict_file.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _now(),
        "verdict":   verdict,
        "summary":   summary,
        "errors":    errors,
        "verifier":  "claude-code-in-context",
    }
    with verdict_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    passed = (verdict == "correct" and not errors)
    print(json.dumps({
        "recorded":   True,
        "verdict":    verdict,
        "passed":     passed,
        "next_step":  (
            f"python orchestrate.py advance {out} ok"
            if passed else
            f"python orchestrate.py advance {out} fail"
        ),
    }, indent=2))


def cmd_repair_context(args: list[str]) -> None:
    """Return the latest verification report so Claude Code knows exactly what to fix."""
    if not args:
        print("Usage: orchestrate.py repair-context <output_dir>", file=sys.stderr)
        sys.exit(1)

    out   = Path(args[0]).resolve()
    state = PipelineState.load(out)
    vfile = out / "memory" / _problem_memory_subdir(state) / "verification_reports.jsonl"

    latest: Optional[Dict[str, Any]] = None
    if vfile.exists():
        for line in vfile.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    latest = json.loads(line)
                except json.JSONDecodeError:
                    pass

    print(json.dumps({
        "latest_verification_report": latest,
        "instruction": (
            "Use the errors, gaps, and repair_hints above to fix blueprint.md. "
            "Then call: python orchestrate.py advance <output_dir> ok"
        ),
    }, indent=2))


def _problem_memory_subdir(state: PipelineState) -> str:
    """Return the sanitised problem_id subfolder name (mirrors mcp/server.py logic)."""
    import re as _re
    pid = state.problem_id.strip().replace("\\", "/")
    parts = []
    for p in pid.split("/"):
        p = p.strip()
        if not p or p in (".", ".."):
            continue
        p = _re.sub(r"\s+", "_", p)
        p = _re.sub(r"[^A-Za-z0-9._-]", "_", p)
        p = _re.sub(r"_+", "_", p).strip("._")
        if p:
            parts.append(p)
    return "/".join(parts) or "problem"


# ── Entry point ────────────────────────────────────────────────────────────────

COMMANDS = {
    "init":           cmd_init,
    "next":           cmd_next,
    "advance":        cmd_advance,
    "status":         cmd_status,
    "note":           cmd_note,
    "verify-prep":    cmd_verify_prep,
    "verify-record":  cmd_verify_record,
    "repair-context": cmd_repair_context,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Commands: {', '.join(COMMANDS)}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
