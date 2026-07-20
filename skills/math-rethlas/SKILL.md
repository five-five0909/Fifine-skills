---
name: math-rethlas
description: Use this skill when the user wants to prove a math problem using the Rethlas formal verification system. Trigger: /rethlas, prove, math proof, 证明, 形式化证明. Drives full proof workflow via MCP tools; output lands in a folder named after the problem.
tools: PowerShell, Read, Write
---

# Rethlas — Math Proving Skill

You are the reasoning agent. All output files go to one folder: `<user-cwd>/<problem-slug>/`.

The skill directory is shown at the top of this file as "Base directory for this skill: <skill_dir>".
Use `<skill_dir>` to construct all CLI command paths below.

---

## Trigger check
This skill applies when the user wants formal verification or proof of a math problem using the Rethlas system. If the user is asking about general math concepts, code, or writing — stop, this skill doesn't apply.

## Output file structure

```
<user-cwd>/<problem-slug>/
├── problem.md                  ← problem statement (copied in automatically)
├── .pipeline_state.json        ← orchestrator state (managed by orchestrate.py)
├── blueprint.md                ← proof draft (you write this)
├── blueprint_verified.md       ← final verified proof (you write this after passing verification)
└── memory/                     ← reasoning artifacts (MCP tools write here)
    ├── immediate_conclusions.jsonl
    ├── toy_examples.jsonl
    ├── counterexamples.jsonl
    ├── big_decisions.jsonl
    ├── subgoals.jsonl
    ├── proof_steps.jsonl
    ├── failed_paths.jsonl
    ├── verification_reports.jsonl
    ├── branch_states.jsonl
    ├── events.jsonl
    └── meta.json
```

---

## Step 0 — Ask for the problem

If the user hasn't specified a problem, ask: "Which problem would you like to prove? Give me a filename (e.g. `example.md`) or a name to create a new one."

To create a new problem file:
```powershell
python "<skill_dir>/cli/rethlas.py" new <name> --json
```
Then read the created file and write the problem statement into it.

---

## Step 1 — Set up the session

```powershell
python "<skill_dir>/cli/rethlas.py" prove <problem> --json
```

Parse the JSON. Save these values — you'll use them throughout:

| Field | Use |
|-------|-----|
| `output_dir` | Root of all output — e.g. `C:\Users\...\test_sum_of_odds` |
| `problem_id` | Key for all MCP memory calls — e.g. `test_sum_of_odds` |
| `slug` | Folder name — e.g. `test_sum_of_odds` |
| `problem_file` | Read this as the problem statement |
| `agents_md` | Read this for your operating instructions |
| `draft_path` | Write `blueprint.md` here |
| `verified_path` | Write `blueprint_verified.md` here after verification passes |
| `memory_dir` | MCP server writes memory here (set via `RETHLAS_MEMORY_ROOT`) |
| `verify_service.running` | Informational only — verification is done in-context |
| `already_verified` | If `true`, skip to showing results |
| `orchestrator.cmd` | Base command for the Python orchestrator |
| `orchestrator.current_stage` | First stage instruction (already initialized) |

---

## Step 2 — Verification is in-context (no service needed)

Verification is performed by **you** (Claude Code) reading `blueprint.md` and reasoning through the proof. No external service is needed. Skip any `serve` step.

---

## Step 3 — Read your instructions

Read `agents_md` (= `<skill_dir>/agents/generation/AGENTS.md`) for your full operating manual.

Also read `problem_file` (= `output_dir/problem.md`) for the problem statement.

---

## Step 4 — Execute the orchestrated proving workflow

The Python orchestrator enforces the proof pipeline. You MUST follow its stage instructions exactly.

### Orchestrator commands

```powershell
# Get current stage instruction (already called by 'prove', use current_stage from Step 1)
python "<skill_dir>/cli/orchestrate.py" next <output_dir>

# Advance to next stage after completing current stage work
python "<skill_dir>/cli/orchestrate.py" advance <output_dir> <result>
# result is one of: ok | solved | fail

# Check pipeline status anytime
python "<skill_dir>/cli/orchestrate.py" status <output_dir>

# Add a note to pipeline state
python "<skill_dir>/cli/orchestrate.py" note <output_dir> "<text>"

# VERIFY stage helpers
python "<skill_dir>/cli/orchestrate.py" verify-prep <output_dir>
python "<skill_dir>/cli/orchestrate.py" verify-record <output_dir> <verdict> "<summary>"
# verdict: correct | incorrect | incomplete

# REPAIR stage helper
python "<skill_dir>/cli/orchestrate.py" repair-context <output_dir>
```

### Proving loop

The `current_stage` object from Step 1 contains your first instruction. Follow this loop:

```
LOOP:
  1. Read the "instruction" field from the current stage object
  2. Execute all steps described in the instruction
     - Use MCP tools (memory_init, memory_append, memory_search, search_arxiv_theorems, verify_proof_service)
     - Write/update blueprint.md when required
     - Write blueprint_verified.md only when verification passes
  3. Call advance with the appropriate result:
       python "<skill_dir>/cli/orchestrate.py" advance <output_dir> ok|solved|fail
  4. Parse the returned JSON — it contains the next stage instruction
  5. If stage == "DONE" or stage == "EXHAUSTED": stop the loop
  6. Otherwise: go to step 1 with the new instruction
```

### Stage summary

| Stage | What you do | Advance result |
|-------|-------------|---------------|
| INIT | memory_init, read problem + AGENTS.md | `ok` |
| EXPLORE | search theorems, examples, counterexamples, query memory | `ok` |
| PLAN | propose ≥2 subgoal decomposition plans | `ok` |
| DIRECT_PROVE | try all plans with direct proof; assemble blueprint if solved | `solved` / `fail` |
| RECURSIVE_PROVE | spawn parallel sub-agent proofs; assemble if any solved | `solved` / `fail` |
| IDENTIFY_FAILURES | analyze stuck points, name the common obstruction | `ok` |
| REPLAN | new plans addressing the identified failure | `ok` |
| VERIFY | YOU read blueprint.md and check the proof in-context; call verify-record to persist verdict; copy to verified_path if correct | `ok` / `fail` |
| REPAIR | repair blueprint using verification report | `ok` |
| DONE | present verified proof to user | — |
| EXHAUSTED | report progress and best draft | — |

### Memory — use `problem_id` from Step 1 for all MCP calls:
- `memory_init(problem_id=<problem_id>)` first (INIT stage)
- `memory_append(problem_id=<problem_id>, channel=..., data=...)` for every artifact
- `memory_search(problem_id=<problem_id>, query=...)` to retrieve

### Verification — YOU are the verifier (no external service):

In the VERIFY stage:
1. Call `verify-prep <output_dir>` → get sections + checklist
2. Read `blueprint.md` and reason through each checklist item in-context
3. Call `verify-record <output_dir> correct|incorrect|incomplete "<one-sentence summary>"`
4. If correct: copy blueprint.md → blueprint_verified.md; advance `ok`
5. If incorrect/incomplete: advance `fail` → pipeline moves to REPAIR

### Draft proof — write incrementally to `draft_path`:
```powershell
Set-Content "<draft_path>" "<proof content>" -Encoding UTF8
```

### Final output — only when verification passes, write to `verified_path`:
```powershell
Set-Content "<verified_path>" "<verified proof content>" -Encoding UTF8
```

---

## Step 5 — Confirm completion

```powershell
python "<skill_dir>/cli/rethlas.py" results <problem> --json
```

Report to the user:
- Location of the output folder (`output_dir`)
- Whether proof is verified or still draft
- Show the final proof content

---

## Other commands

```powershell
python "<skill_dir>/cli/rethlas.py" status --json   # system status
python "<skill_dir>/cli/rethlas.py" results --json  # list all completed proofs
```
