# Update prompt template documentation

## Goal

Make the repository README accurately describe the prompt templates available in a clean checkout, so every documented target resolves without mistaking prompt references for installable skills.

## Background

- The issue requests a documentation-only repair.
- `README.md` currently names only `BASE AGENTS.md` and `Claude Fable 5.md`.
- The clean repository tracks two prompt templates. Twenty role-oriented Markdown files are separate, untracked parallel work and are not part of this task's delivery.
- `package.json` already treats `prompts/` as a packaged documentation/resource directory.

## Requirements

1. Update only `README.md` as the repository-facing catalog for prompt templates.
2. Preserve the distinction between prompt templates and installable skills.
3. Keep the two tracked general prompt entries and do not publish or take ownership of untracked parallel prompt work.
4. Use repository-relative Markdown links whose targets exist in the Git index.
5. Do not modify scripts, package metadata, skill content, prompt-template bodies, or unrelated dirty files.

## Acceptance Criteria

- Every prompt link in README resolves to a tracked target in a clean checkout.
- The README prompt catalog and tracked `prompts/*.md` files have the same two filenames.
- `npm run validate` passes.
- A tracked-target consistency check reports no missing or stale README prompt links.
- `git diff --check` reports no whitespace errors for the task change.

## Out of Scope

- Editing or adding prompt-template content.
- Publishing prompt templates as skills.
- Changing package distribution behavior.
- Cleaning up existing Multica runtime files or other agents' working-tree changes.

## Implementation Result

- `README.md` documents the two prompt templates tracked by Git.
- Twenty untracked role templates remain untouched in the working tree for their owner.
- Nine unrelated Trellis paths accidentally added by the original archive commit are removed from the task's net delivery while their working-tree files remain intact.

## Open Questions

None. Repository evidence defines the catalog scope, and the triggering comment explicitly authorizes the documentation update.
