# Implementation Plan

1. Add `scripts/scan_transcript.py` as a stdlib-only CLI adapter and test it.
2. Extend transcript discovery and MCP behavior for Codex-only default selection.
3. Rebuild code indexes when their persisted manifest is stale; add regressions.
4. Update bootstrap paths and all affected skill/README commands.
5. Run Node tests, smoke test, Python CLI help/fixture tests, and package validation.
