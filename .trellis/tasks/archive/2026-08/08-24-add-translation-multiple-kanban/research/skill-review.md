# Skill review notes

## Repository rules consulted

- `.trellis/spec/index.md`
- `.trellis/spec/skill-design-principles.md`
- `AGENTS.md`
- `scripts/validate-skills.mjs`

## Initial findings

- The skill directory used the canonical-looking `fifine-translation-multiple-kanban` name, but the frontmatter still said `multiple-translation`.
- `agents/openai.yaml` had `display_name` but no validator-required `short_description`.
- `SKILL.md` lacked the required first `Trigger check` section.
- The skill was absent from `skills.json`, `scripts/publishable-skills.json`, the postinstall fallback list, and the project routing docs.
- The job script rejected a plain input with no `--target` before its documented `zh-CN` fallback could run.
- The hard splitter could emit one character over `chunk-max` when a delimiter occurred exactly at the boundary.
- Translation-row duplicate IDs were silently overwritten during status checks.

## Verification plan

1. Run repository skill validation after removing generated `__pycache__` directories.
2. Run `python -B` compile checks for both bundled scripts.
3. Create a temporary multi-target JobID, populate translations deterministically, run status, merge, and render both HTML and Markdown.
4. Assert default-target behavior and hard-split size limits with a small Python smoke test.
