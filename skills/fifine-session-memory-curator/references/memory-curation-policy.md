# Memory curation policy

## Proposal schema

```json
{
  "version": 1,
  "generated_at": "2026-09-20",
  "entries": [
    {
      "key": "communication.concise-first",
      "instruction": "Give the directly usable answer before optional background explanation.",
      "category": "preference",
      "scope": "global",
      "grounding": "explicit_user",
      "confidence": "high",
      "status": "active",
      "confirmed": true,
      "evidence": "The user explicitly asked for executable guidance before explanation.",
      "reason": "Stable cross-project response preference."
    }
  ]
}
```

`confirmed` is optional and defaults to `false`. Use it only when the user explicitly confirms an otherwise inferred or repeated observation.

## Promotion matrix

| Grounding | Default disposition |
|---|---|
| `explicit_user` | May become active when global and stable |
| `user_correction` | May become active; phrase as the corrected behavior |
| `verified_external` | May support a workflow or constraint, but do not present external facts as user preferences |
| `repeated_observation` | Candidate unless explicitly confirmed |
| `assistant_inference` | Candidate or rejected; never silently promote |

## Retention and correction

- Use stable semantic keys so a later proposal can update the same memory.
- Preserve the previous entry in ledger history when a grounded entry changes.
- A weak inferred candidate must never deactivate an existing active memory; retain it in `pending` for later confirmation.
- Mark obsolete rules `superseded` rather than erasing their existence.
- Mark disproven or unsafe rules `rejected` with a reason.
- Do not preserve raw credentials or sensitive transcript excerpts even in history.
- A user can explicitly ask to forget an item; use `status=deleted`. The helper removes its content from active entries, history, and pending proposals, retaining only a content-free deletion tombstone.

## Writing good instructions

Each active instruction should be:

- one behavioral rule;
- understandable without the original session;
- conditional when its applicability is conditional;
- phrased positively when a safe path exists;
- free of unsupported absolutes such as “always” and “never” unless the user actually set a hard boundary.

Bad:

> Always use tool X because it worked once.

Better:

> For remote V100 runs in the documented environment, prefer tool X; verify the runtime before applying this outside that environment.

The better version may still be project-scoped rather than global.

## Conflict policy

Use this precedence when curating:

1. current explicit user correction;
2. newer explicit user preference;
3. verified live constraints and authoritative documentation;
4. older active memory;
5. repeated observation;
6. assistant inference.

If a preference conflicts with objective facts, preserve it only as a preference where meaningful; do not rewrite the false factual claim as truth. If the conflict cannot be resolved safely, keep it as a candidate and ask the user.
