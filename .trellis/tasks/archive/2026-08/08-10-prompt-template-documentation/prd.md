# Update prompt template documentation

## Goal

Make the repository README accurately describe the prompt-template collection that is present under `prompts/`, so users can discover the available templates without mistaking them for installable skills.

## Background

- The issue requests a documentation-only repair.
- `README.md` currently names only `BASE AGENTS.md` and `Claude Fable 5.md`.
- The working tree also contains twenty role-oriented Markdown prompt templates grouped around product, design, software, and platform responsibilities.
- `package.json` already treats `prompts/` as a packaged documentation/resource directory.

## Requirements

1. Update only `README.md` as the repository-facing catalog for prompt templates.
2. Preserve the distinction between prompt templates and installable skills.
3. Keep the two existing general prompt entries and add a compact, categorized catalog for the role-oriented templates.
4. Use repository-relative Markdown links whose targets match filenames exactly.
5. Do not modify scripts, package metadata, skill content, prompt-template bodies, or unrelated dirty files.

## Acceptance Criteria

- Every Markdown file currently present directly under `prompts/` is represented in the README prompt-template section.
- Every new README link resolves to an existing local file.
- `npm run validate` passes.
- A documentation consistency check confirms that the README catalog and `prompts/*.md` have the same set of filenames.
- `git diff --check` reports no whitespace errors for the task change.

## Out of Scope

- Editing or adding prompt-template content.
- Publishing prompt templates as skills.
- Changing package distribution behavior.
- Cleaning up existing Multica runtime files or other agents' working-tree changes.

## Open Questions

None. Repository evidence defines the catalog scope, and the triggering comment explicitly authorizes the documentation update.
