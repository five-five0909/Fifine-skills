# PRD: Add and validate `fifine-translation-multiple-kanban`

## Goal

Publish the newly added multiple-translation skill as a first-class Fifine skill and make its content comply with the repository's neutral `.agents` skill standard.

## Scope

- Correct the skill metadata so its directory, `SKILL.md` frontmatter, publishable name, and install paths use the canonical `fifine-translation-multiple-kanban` name.
- Make the description route-oriented, single-line, bilingual where useful, and explicit about triggers, output, and exclusions.
- Add the required body-level `Trigger check` block without changing the skill's intended translation workflow.
- Complete `agents/openai.yaml` with the validator-required interface fields.
- Add the skill to `skills.json`, `scripts/publishable-skills.json`, `scripts/postinstall.js` fallback/legacy handling as appropriate, `AGENTS.md`'s publishable-skill and routing tables, and the README skill index narrative.
- Review and test the bundled job/render scripts for syntax, deterministic chunking/merge behavior, and selectable HTML/Markdown output. Fix only issues required for the documented contract.
- Run the repository validator and relevant Python smoke tests; leave no generated forbidden directories in the final working tree.

## Acceptance criteria

1. `npm run validate` passes with the new skill included.
2. The skill name is exactly `fifine-translation-multiple-kanban` in its directory, frontmatter, `skills.json`, and publishable list.
3. `SKILL.md` has a compliant route-oriented description and a first-section `Trigger check` block.
4. `agents/openai.yaml` contains both `interface.display_name` and `interface.short_description`.
5. A sample JobID can be created, validated, merged, and rendered to selectable HTML and Markdown using only the bundled scripts.
6. Documentation describes the new skill and its routing without exposing machine-specific paths.
7. Changes are committed to Git after the Trellis spec-update/check steps.

## Non-goals

- Adding external translation providers or network dependencies.
- Changing the public translation policy beyond metadata, validation, and correctness fixes discovered during testing.
