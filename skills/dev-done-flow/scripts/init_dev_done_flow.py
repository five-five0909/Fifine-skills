#!/usr/bin/env python3
"""Initialize or update local dev-done-flow workflow documents.

active.md holds a compact summary + TODO block.
Per-stage details live in stages/<stage-name>.md (created as skeletons here).
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

START = "<!-- dev-done-flow:start -->"
END = "<!-- dev-done-flow:end -->"

ARTIFACTS = {
    "requirements.md": "# Requirements\n\n## Functional Requirements\n\n## Non-functional Requirements\n\n## Acceptance Criteria\n\n## Open Questions\n",
    "flow-design.md": "# Flow Design\n\n## Main Flow\n\n## Alternative Flows\n\n## Error / Recovery Flows\n\n## State Model\n",
    "tech-spec.md": "# Technical Design\n\n## Current Architecture\n\n## Proposed Architecture\n\n## API / Interface Design\n\n## Data Model\n\n## Error Handling\n\n## Security\n\n## Performance\n\n## Observability\n\n## Rollback\n",
    "task-plan.md": "# Task Planning\n\n## Milestones\n\n## Epics\n\n## Issues\n\n## Dependencies\n\n## Risks\n",
    "tdd-plan.md": "# TDD Plan\n\n## Test Strategy\n\n## Unit Tests\n\n## Integration Tests\n\n## Regression Tests\n\n## Definition of Done\n",
    "eval-plan.md": "# Evaluation Plan\n\nUse this for LLM, Agent, RAG, prompt, or other evaluation-driven work.\n\n## Evaluation Dataset\n\n## Golden Cases\n\n## Bad Cases\n\n## Metrics\n\n## Regression Evaluation\n",
    "release-plan.md": "# Release Plan\n\n## Version / Scope\n\n## Deployment Steps\n\n## Migration\n\n## Feature Flags\n\n## Rollback Plan\n\n## Release Notes\n",
    "observability-plan.md": "# Observability Plan\n\n## Logs\n\n## Metrics\n\n## Traces\n\n## Alerts\n\n## Dashboards\n\n## LLM / Tool Traces\n",
}

# active.md is a compact summary + TODO; per-stage detail lives in stages/
ACTIVE_TEMPLATE = """\
# Dev Done Flow — Active Session

## Metadata

- Task Name: {task_name}
- Task Type: {task_type}
- Current Stage: {current_stage}
- Status: active
- Created At: {now}
- Updated At: {now}

## Goal

{goal}

## TODO
<!-- updated by update_stage.py — do not hand-edit this block -->
{todo_block}

## Stage Summaries

_AI appends a one-paragraph summary here after each stage completes._
_Full per-stage detail is in stages/<stage-name>.md_

## Decision Log

_See decisions.md for durable decisions._

## Raw Notes

### {now}

Initial request:

> {user_request}
"""

STAGE_FILE_TEMPLATE = """\
# Stage: {stage}

## Status: {status}

## Questions Asked

_pending_

## User Answers

_pending_

## Assumptions

_pending_

## Open Questions

_pending_

## Output / Decisions

_pending_
"""

SKIPPED_FILE_TEMPLATE = """\
# Skipped / Merged Stages

Record every optional stage that was skipped or merged, including the reason.
AI must write here before advancing past an optional stage.

| Stage | Action | Reason |
|-------|--------|--------|
"""


def render_todo_block(stages: List[dict]) -> str:
    lines = []
    for s in stages:
        status = s["status"]
        name = s["name"]
        req_tag = "" if s["required"] else " _(optional)_"
        if status == "done":
            marker = "- [x]"
        elif status == "skipped":
            marker = "- [~]"
        elif status == "in_progress":
            marker = "- [▶]"
        else:
            marker = "- [ ]"
        lines.append(f"{marker} **{name}**{req_tag}")
    return "\n".join(lines)


def load_manifest(flow_dir: Path) -> List[dict]:
    manifest_path = flow_dir / "manifest.json"
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return data.get("stages", [])
    return []


def first_existing_agent_file(root: Path) -> Path:
    for name in ("AGENTS.md", "Agents.md", "agents.md"):
        p = root / name
        if p.exists():
            return p
    return root / "Agents.md"


def update_agents(root: Path, workflow_dir: str) -> Path:
    path = first_existing_agent_file(root)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Agents\n\n"
    block = f"""{START}

## Dev Done Flow

This project uses `{workflow_dir}/` as local workflow memory for structured development work.

Rules for agents working in this project:

- Read `{workflow_dir}/active.md` before any planning, design, implementation, diagnosis, or iteration work.
- Per-stage details (questions, answers, assumptions) are in `{workflow_dir}/stages/<stage-name>.md`.
- Stable stage outputs go under `{workflow_dir}/artifacts/`.
- Stage order is fixed by `{workflow_dir}/manifest.json`. Do not skip required stages.
- Optional stages may be skipped or merged — record the reason in `{workflow_dir}/stages/skipped.md`.
- After completing a stage, run `update_stage.py` to mark it done and refresh the TODO block.

{END}"""
    if START in existing and END in existing:
        before = existing.split(START, 1)[0].rstrip()
        after = existing.split(END, 1)[1].lstrip()
        new_text = before + "\n\n" + block + "\n\n" + after
    else:
        new_text = existing.rstrip() + "\n\n" + block + "\n"
    path.write_text(new_text, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize dev-done-flow files in a project root.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--task-name", default="Untitled Development Task")
    parser.add_argument("--task-type", default="unclassified")
    parser.add_argument("--stage", default="goal", help="Current stage name (from manifest).")
    parser.add_argument("--user-request", default="_not provided_")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    flow_dir = root / ".dev-done-flow"
    artifacts_dir = flow_dir / "artifacts"
    stages_dir = flow_dir / "stages"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    stages_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    goal = args.user_request.strip() or "_pending_"

    # Load stage list from manifest (written by plan_flow.py)
    stage_list = load_manifest(flow_dir)
    todo_block = render_todo_block(stage_list) if stage_list else "_Run plan_flow.py first to populate stages._"

    active = flow_dir / "active.md"
    if active.exists():
        text = active.read_text(encoding="utf-8")
        text = re.sub(r"(- Updated At: ).+", rf"\g<1>{now}", text, count=1)
        # Refresh TODO block between the comment markers
        text = re.sub(
            r"(<!-- updated by update_stage\.py.*?-->\n).*?(\n\n## Stage Summaries)",
            rf"\g<1>{todo_block}\g<2>",
            text,
            flags=re.DOTALL,
        )
        append = f"\n\n### {now}\n\nWorkflow resumed.\n\nUser request:\n\n> {args.user_request}\n"
        active.write_text(text.rstrip() + append, encoding="utf-8")
    else:
        active.write_text(
            ACTIVE_TEMPLATE.format(
                task_name=args.task_name,
                task_type=args.task_type,
                current_stage=args.stage,
                now=now,
                goal=goal,
                todo_block=todo_block,
                user_request=args.user_request,
            ),
            encoding="utf-8",
        )

    # Pre-build per-stage skeleton files (skip if already exist)
    for s in stage_list:
        stage_file = stages_dir / f"{s['name']}.md"
        if not stage_file.exists():
            stage_file.write_text(
                STAGE_FILE_TEMPLATE.format(stage=s["name"], status=s["status"]),
                encoding="utf-8",
            )

    # skipped.md scaffold
    skipped_file = stages_dir / "skipped.md"
    if not skipped_file.exists():
        skipped_file.write_text(SKIPPED_FILE_TEMPLATE, encoding="utf-8")

    decisions = flow_dir / "decisions.md"
    if not decisions.exists():
        decisions.write_text("# Decision Log\n\n", encoding="utf-8")

    for name, content in ARTIFACTS.items():
        p = artifacts_dir / name
        if not p.exists():
            p.write_text(content, encoding="utf-8")

    agents_path = update_agents(root, ".dev-done-flow")

    print(f"created_or_updated={flow_dir}")
    print(f"active={active}")
    print(f"stages_dir={stages_dir}")
    print(f"agents={agents_path}")


if __name__ == "__main__":
    main()
