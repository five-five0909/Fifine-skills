# Update prompt template documentation

## Goal

Make the repository README accurately describe the prompt templates available in a clean checkout, so every documented target resolves without mistaking prompt references for installable skills.

## Background

- The issue requests a documentation-only repair.
- Integration commit `f00318b` tracks 22 prompt templates: two general references and twenty role-oriented templates.
- `README.md` currently names only the two general templates, leaving twenty tracked targets undocumented.
- `package.json` already treats `prompts/` as a packaged documentation/resource directory.

## Requirements

1. Update only `README.md` as the repository-facing catalog for prompt templates.
2. Preserve the distinction between prompt templates and installable skills.
3. Catalog all 22 tracked templates in compact role-based categories without modifying their contents.
4. Use repository-relative Markdown links whose targets exist in the Git index.
5. Do not modify scripts, package metadata, skill content, prompt-template bodies, or unrelated dirty files.

## Acceptance Criteria

- Every prompt link in README resolves to a tracked target in a clean checkout.
- The README prompt catalog and tracked `prompts/*.md` files have the same 22 filenames.
- `npm run validate` passes.
- A tracked-target consistency check reports no missing or stale README prompt links.
- `git diff --check` reports no whitespace errors for the task change.

## Out of Scope

- Editing or adding prompt-template content.
- Publishing prompt templates as skills.
- Changing package distribution behavior.
- Cleaning up existing Multica runtime files or other agents' working-tree changes.

## Implementation Result

- `README.md` documents all 22 prompt templates tracked by Git, grouped into general, product, design, software, and platform categories.
- The twenty role template files introduced by `f00318b` remain byte-for-byte untouched by this documentation repair.
- Nine unrelated Trellis paths accidentally added by the original archive commit are removed from the task's net delivery while their working-tree files remain intact.

## Open Questions

None. Repository evidence defines the catalog scope, and the triggering comment explicitly authorizes the documentation update.
