# Make Repository Installable As Skills Collection

## Status
- Type: repo restructure
- Goal: convert the repository into a GitHub-installable multi-skill collection

## Requirements
- Keep existing repository content unless it is cache or generated junk.
- Standardize every skill under `skills/<skill-name>/`.
- Ensure every skill has `SKILL.md` and `agents/openai.yaml`.
- Add root `skills.json`, validation script, and updated install docs.
- Keep `.claude/`, `.codex/`, `.trellis/`, and other uncertain repo resources unless a safe update is obvious.

## Success Criteria
- `skills/` exists and contains the full skill set.
- `npm run validate` passes.
- Root docs and package metadata describe the repository as a skills collection.
