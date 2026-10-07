# Journal - fifine (Part 1)

> AI development session journal
> Started: 2026-06-13

---



## Session 1: make repository installable as skills collection

**Date**: 2026-06-23
**Task**: make repository installable as skills collection
**Branch**: `main`

### Summary

Converted the repository into a skills collection layout, validated the scanner-facing structure, and pushed the result to origin/main.

### Main Changes

- Added the installable `skills/` collection layout and root `skills.json` index.
- Added package installation, publishing, and validation scripts.
- Moved existing skills into scanner-compatible directories with OpenAI metadata.

### Git Commits

| Hash | Message |
|------|---------|
| `4da2307` | (see git log) |
| `HEAD` | (see git log) |

### Testing

- The implementation commit added `scripts/validate-skills.mjs`; command-level output was not retained in this historical session record.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 2: Update prompt template documentation

**Date**: 2026-08-10
**Task**: Update prompt template documentation
**Branch**: `main`

### Summary

Documented all prompt templates available in the integrated clean checkout, corrected the task delivery boundary, and passed repository validation.

### Main Changes

- Updated `README.md` with a categorized directory covering all 22 prompt templates tracked after integration commit `f00318b`.
- Left the two general templates and twenty role templates unchanged.
- Removed nine unrelated Trellis paths from the task's net delivery without deleting their working-tree files.
- Replaced seed-only task context and placeholder journal content with the specs, implementation details, and checks actually used.

### Git Commits

| Hash | Message |
|------|---------|
| `58bcc4f` | (see git log) |
| `f00318b` | Integrated the twenty role prompt templates referenced by the final catalog. |
| `9eca832` | Completed the reproducible 22/22 README catalog and synchronized Trellis evidence. |

### Testing

- [OK] `npm run validate` passed for 22 publishable skills.
- [OK] Commit `9eca832` prompt-link closure passed: 22 links, 22 tracked targets, 0 unresolved, 0 stale.
- [OK] Reproduction baseline is fixed at `9eca832` (`9eca8326df5fa54f91d6e3c518f5b8a52ae093e2`).
- [OK] Range, README-only, and working-tree `git diff --check` commands passed.
- [OK] Archived task status and context manifests passed consistency checks.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: Add and validate multiple translation kanban skill

**Date**: 2026-08-24
**Task**: Add and validate multiple translation kanban skill
**Branch**: `main`

### Summary

Added fifine-translation-multiple-kanban, synchronized publishable indexes and routing docs, fixed metadata and JobID boundary validation, and passed npm validation plus script smoke tests.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `27e4cd7` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete

## Session 4: Add fifine-adaptive-runtime-orchestrator skill

**Date**: 2026-09-05
**Task**: Add fifine-adaptive-runtime-orchestrator skill
**Branch**: `main`

### Summary

Added the fifine-adaptive-runtime-orchestrator skill, which makes an agent discover its real execution environment, choose an executor and shell without asking, launch long jobs with a durable Job ID, and poll adaptively instead of guessing `sleep` values. Registered it across skills.json, publishable-skills.json, postinstall.js fallback, README.md, and AGENTS.md. `npm run validate` passes with 26 skills.

### Main Changes

**New skill: `skills/fifine-adaptive-runtime-orchestrator/`**

Adapted a 36-section source document into the repository's publishable skill conventions. Source was ~6000+ words, above the 5000-word body limit in `.trellis/spec/skill-design-principles.md`, so the executable core went into SKILL.md (2378 words) and deep-dive material was split into four lazily-loaded references:

- `SKILL.md` — Trigger check, the 10-step core loop (discovery → capability discovery → profile → executor+shell → launch → Job ID → baseline → wait window → adaptive poll → remember), autonomy rule, and all 25 hard rules.
- `references/runtime-discovery.md` — target-type detection signals, POSIX/Windows probe commands, WSL/container/SSH boundary rules.
- `references/profile-schema.md` — full 29-field profile schema, worked JSON example, per-target isolation, invalidation triggers, secret allow/deny list.
- `references/executor-selection.md` — executor candidate scoring, 7-tier preference order, launch patterns per platform, Job ID mapping.
- `references/polling-playbook.md` — L/G/I_cap/I0 formulas, the dynamic algorithm with all numeric factors, copy-ready bash and PowerShell `KEY=VALUE` probes, stall diagnosis.

**Index and doc registration**

- `skills.json` — new entry with full trigger-word description.
- `scripts/publishable-skills.json` and the `postinstall.js` fallback list — added.
- `README.md` — added to the Skills prose section.
- `AGENTS.md` — added to the publishable skills table and two Skill Routing rows.

### Git Commits

| Hash | Message |
|------|---------|
| `11b7a3e` | feat(skills): add adaptive runtime orchestrator skill |
| `adad508` | chore(skills): register adaptive runtime orchestrator in indexes and docs |
| `1e20a24` | docs(spec): document validator forbidden-dir false positives |

### Testing

- [OK] `npm run validate` passes; 26 skills listed including the new one.
- [OK] Frontmatter parses under both the repo's line-based reader and strict PyYAML; `name` matches directory, `description` is a quoted single 640-char line.
- [OK] `agents/openai.yaml` passes validator (`interface.display_name` = directory name).
- [OK] `## Trigger check` is the first H2 in the body.
- [OK] All 25 hard rules present; numeric factors verified in both SKILL.md and polling-playbook.md (`L×0.15`, `L×0.20`, `I×1.2`, `I×1.5`, `I×2`, `I/2`, `stale>=2`, `stale>=3`, `ETA×0.20–0.33`).
- [OK] All three indexes and both docs contain the skill; verified programmatically.
- [OK] Cleaned `__pycache__` dirs under `.trellis/` (gitignored build artifacts) that were failing the validator's forbidden-directory check. Recurs after every Trellis script run; documented the distinction in spec section 7.1.
- [OK] Quality check found 4 real defects, all fixed and re-verified:
  - launch snippet left `<TASK_DIR>` as a literal inside single quotes, so `exit_code` was never written — reproduced the failure, then confirmed `exit_code=0` after the fix. This is the DONE/FAILED signal, so the bug silently defeated the state machine.
  - `ls -1 <result-glob>` is a shell syntax error (`<` is a redirect) that aborted the whole probe round; hoisted to a quoted `GLOB` variable.
  - PowerShell `Get-Date "1970-01-01"` parses as local midnight, skewing `AGE_SEC` by the UTC offset (verified as +8h on UTC+8) and risking false stall reports; added the `Z` suffix.
  - `I_min` was used in the ETA clamp but never defined.
- [NOTE] GLOB-variable expansion returns 0 under zsh (no unquoted-variable globbing) but works under bash. The docs already say to adapt to the selected shell, and the POSIX path is bash, so this is not a defect — just a real shell difference worth remembering when testing here.
- [NOTE] The PowerShell epoch fix is verified by semantics, not execution — no `pwsh` on this machine.

### Status

[OK] **Completed**

### Next Steps

- Commit the journal, then run `/trellis:finish-work` to archive the task.


## Session 4: Add fifine-adaptive-runtime-orchestrator skill

**Date**: 2026-09-05
**Task**: Add fifine-adaptive-runtime-orchestrator skill
**Branch**: `main`

### Summary

Added the fifine-adaptive-runtime-orchestrator skill: adaptive runtime discovery, executor/shell selection, long-job launching and adaptive polling. Source was 36 sections, split into a 2477-word SKILL.md plus four lazily-loaded references to stay within the 5000-word body guideline. Registered in skills.json, publishable whitelist, postinstall fallback, README, and AGENTS.md. Quality check found and fixed 4 real defects, most severely a launch snippet where TASK_DIR stayed literal inside single quotes so exit_code was never written, silently defeating the DONE/FAILED state machine. Also synced the Trellis 0.6.10 framework upgrade and platform-local payloads that were already dirty in the tree.

### Git Commits

| Hash | Message |
|------|---------|
| `11b7a3e` | (see git log) |
| `adad508` | (see git log) |
| `1e20a24` | (see git log) |
| `8f75d11` | (see git log) |
| `bd27e4c` | (see git log) |

### Status

[OK] **Completed**


## Session 5: Add fifine-file-naming-organizer skill

**Date**: 2026-10-07
**Task**: Add fifine-file-naming-organizer skill
**Branch**: `main`

### Summary

Added the fifine-file-naming-organizer skill, turning the 状态标签+YYYYMMDD+核心信息+版本号 convention into a checkable grammar plus a deterministic audit → confirm → dry-run → apply → mapping-log → undo pipeline. Three stdlib-only Python scripts share naming_lib.py so the read-only auditor and the executor can never disagree; SKILL.md keeps 核心信息 as the agent's semantic judgement and never scripts that part. Registered in all five publish points.

### Main Changes

- SKILL.md: mode A names new files without touching disk; mode B tidies existing folders through Step 1-5 with a mandatory confirmation table before any rename
- audit_names.py: Chinese actionable diagnostics, salvage() reuses tag/date/version from broken names, and every printed suggestion is self-validated so the tool never proposes a name it would itself reject
- apply_naming.py: LOCKED-REFUSE on 定稿/归档 main names (pure same-name moves still allowed), conflict refusal with no auto-suffixing, case-insensitive slot check, .naming-tmp two-phase hop for rename cycles, created-directory ledger powering --undo
- Fixed 7 doc/code and grammar defects found while verifying: char-counted name limit missed the 255-byte component ceiling (added a 200-byte budget); a generic two-segment extension group swallowed the dot in -V1.2.pptx and marked a documented anti-pattern compliant (now one segment plus four whitelisted composite suffixes); plan fields bump/action and helpers bump_version()/project_from_path() were documented but uncalled (removed, so the confirmed new_name is exactly what lands); --undo orphaned intermediate created dirs; the archive root's own name polluted every suggestion; an impossible date 20261332 was reused in a suggestion; and platform-safety.md advised replacing a colon with a spaced hyphen, which the grammar itself rejects

### Git Commits

| Hash | Message |
|------|---------|
| `f702f33` | (see git log) |

### Testing

- [OK] [OK] npm run validate passes; 28 publishable skills == 28 skills.json entries; postinstall fallback array matches publishable-skills.json in order and content; skills.json description is byte-identical to the SKILL.md frontmatter
- [OK] [OK] Grammar table 30/30: canonical example, locked 定稿/归档, tags outside the closed set, 6-keyword reject, V0 reject, V1.10 accepted, Windows reserved names, dot-file skip, 40-char keyword / 100-char stem / 200-byte / 240-path budgets, dir tag and version bans, depth-1 date requirement vs depth-2 exemption
- [OK] [OK] Fixture end-to-end: audit → plan → dry-run → apply → re-audit reports 6/6 compliant → re-apply the same plan yields 0 moves → --undo restores the file set byte-exactly and removes the dirs it created
- [OK] [OK] Guard paths exercised for real: 定稿 main-name edit refused, 归档 pure move allowed, duplicate target refused as CONFLICT without auto-suffix, A<->B swap completed through one temp hop with no leftover .naming-tmp and undone correctly
- [OK] [OK] Install surface simulated under node_modules/@fifine/skills: distributed to both .claude/skills and .agents/skills with a file tree identical to source, and the installed scripts run standalone from an unrelated cwd

### Status

[OK] **Completed**

### Next Steps

- The 【】 tags are legal Unicode and pass the Windows illegal-character check, but real-machine behaviour on OneDrive/坚果云 sync clients is still unverified; the skill already tells users to pilot 1-2 files before a batch
- Task 08-25-clean-publishable-skill-payloads still shows completed-but-unarchived from an earlier session
