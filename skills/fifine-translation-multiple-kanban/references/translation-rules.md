# Translation rules

## Contents

1. General fidelity
2. Scientific and technical text
3. Academic paragraph alignment
4. Business/general prose
5. UI and software strings
6. Terminology consistency
7. Uncertainty and source errors

## 1. General fidelity

Translate the source, not an imagined improved version of it.

Preserve:

- factual scope
- modality and uncertainty
- negation
- tense/aspect when meaningful
- numbering
- citations
- named entities
- quantities and units

Do not add explanations inside the translation unless the user requests annotated translation.

## 2. Scientific and technical text

Preserve formulas, symbols, chemical names, variable names, frequencies, dimensions, inequalities, percentages, and citations exactly.

On first occurrence, retain important abbreviations when useful, for example:

```text
local field potential (LFP)
局部场电位（LFP）
```

Keep recurring terminology fixed across all chunks unless the source itself changes meaning by context.

## 3. Academic paragraph alignment

When translating an academic passage or Introduction:

- preserve the original paragraph count;
- keep visual line wraps inside the same paragraph;
- preserve sentence order;
- if sentence numbering is requested, number continuously across the document;
- keep semicolons and colons inside the same sentence unless they genuinely terminate a sentence in the source language;
- keep citations attached to the claim they support.

## 4. Business/general prose

Prefer natural target-language phrasing while preserving tone and level of formality. Do not over-formalize casual text or make professional text colloquial without instruction.

## 5. UI and software strings

Preserve placeholders, variables, keys, paths, CLI flags, code identifiers, URLs, and markup.

Examples that normally remain unchanged:

- `{username}`
- `%s`
- `--output-dir`
- `/api/v1/users`
- `model_id`

Translate human-facing labels around them.

## 6. Terminology consistency

Maintain a job-level glossary for:

- people/organization/product names
- acronyms
- domain terms
- repeated labels
- user-specified preferred translations

A glossary entry may look like:

```json
{
  "source": "loss of consciousness",
  "target": {
    "zh-CN": "意识丧失"
  },
  "note": "Use LOC unchanged after first definition."
}
```

Prefer the glossary over ad-hoc alternatives unless context clearly requires a different sense.

## 7. Uncertainty and source errors

If source text cannot be read, mark it instead of guessing.

If the source appears to contain a typo:

- preserve the typo in source transcription;
- translate the intended meaning only when context makes it unambiguous;
- optionally add a short note outside the translated body.
