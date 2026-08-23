---
name: fifine-translation-multiple-kanban
description: Use this skill when the user wants substantial content translated from images, PDFs, documents, text, or mixed batches while preserving structure, or needs multi-language output, chunking, resumable JobID tracking, or selectable HTML/Markdown artifacts. Trigger: /fifine-translation-multiple-kanban, multiple translation, batch translation, document translation, 多语言翻译, 批量翻译, 论文翻译. Produces faithful aligned translations and optional HTML/Markdown files. Not for OCR-only extraction, literature search, or media transcription.
---

# Multiple Translation

Translate heterogeneous user input reliably, preserve its structure, and scale from one short paragraph to large multi-file jobs. Use JobID-based chunking when the input is large or resumability is useful. Generate selectable HTML, Markdown, or both when requested.

## Trigger check

Use this skill for substantial or structured translation requests, including files, images, PDFs, mixed batches, multiple target languages, or resumable/chunked jobs. If the user only wants OCR/text extraction, literature search, or audio/video transcription without translation, stop — use the task-specific skill instead.

## Workflow

1. Inspect the input and the user's requested target language(s), style, and output format.
2. Preserve the source structure while normalizing readable content into ordered blocks.
3. Decide whether to translate directly or create a chunked translation job.
4. Translate every block faithfully and consistently.
5. Merge chunk results by JobID when chunking is used.
6. Run a final alignment and terminology check.
7. Return the requested translated text and/or generated HTML/Markdown files.

Read `references/input-handling.md` when the input is an image, PDF, document, batch, or mixed media. Read `references/job-schema.md` before creating or merging a JobID-based translation job. Read `references/translation-rules.md` for fidelity and domain-specific translation rules. Read `references/example.md` when demonstrating the workflow or imitation mode.

## Language selection

- Use the user-specified target language(s) exactly.
- Support one or multiple target languages in the same job.
- If the user does not specify a target language, translate into the language the user is currently using. For a Chinese request, default to Simplified Chinese (`zh-CN`).
- Auto-detect the source language by block when necessary. Do not force a single source language on a genuinely multilingual document.
- Preserve official names, abbreviations, identifiers, formulas, citations, URLs, code, and units unless the user explicitly asks to localize them.

## Structure preservation

Normalize the source into ordered blocks such as:

- title
- heading
- paragraph
- list-item
- table
- caption
- quote
- code
- footnote
- other

Preserve the original order and boundaries whenever they are visible or semantically recoverable.

- Treat visual line wrapping as layout, not a paragraph boundary.
- Keep a paragraph that continues across images or pages as one logical block when the continuation is clear.
- Preserve list nesting, table row/column order, citations, equation notation, and numbering.
- Never invent cropped, hidden, or unreadable content. Mark uncertainty explicitly, for example `[原文不清]` for a Chinese-target job.
- Do not silently fix a likely typo in the source. Preserve source text and, when useful, add a brief note while translating the intended meaning only when unambiguous.

## Direct versus JobID mode

Use **direct mode** only when all of the following are true:

- the normalized source is at most 16,000 source characters;
- the input is small enough to inspect reliably in one pass;
- there are at most 4 images or at most 6 document pages in the current unit of work;
- the request does not require resumable batch processing.

Use **JobID mode** when any of the following is true:

- normalized source exceeds 16,000 characters;
- more than 4 images or more than 6 pages must be processed;
- multiple files are provided and should be treated as one batch;
- the user asks for splitting, merging, resumability, batch translation, or a JobID;
- the input is large enough that a single-pass translation risks omission or structural drift.

Default JobID chunk policy:

- target chunk size: 12,000 source characters;
- hard chunk limit: 16,000 source characters;
- prefer block boundaries;
- split an oversized paragraph only at sentence boundaries;
- if one sentence itself exceeds the hard limit, split at the safest punctuation or whitespace boundary and keep the parts under the same parent block;
- for pre-normalization ingestion, inspect at most 4 images or 6 document pages per pass, then append their normalized blocks in source order before translation;
- do not duplicate overlap/context text in final output.

These limits are defaults, not claims about a model's context window. Reduce them for dense tables, poor scans, complex equations, or unusually terminology-heavy material. Increase them only when the user explicitly requests it and the environment can safely handle the larger unit.

## JobID processing

For a chunked job:

1. Normalize source blocks into UTF-8 JSON using the schema in `references/job-schema.md`.
2. Run `scripts/translation_job.py create ...` to generate a JobID, manifest, chunk files, and empty glossary.
3. Translate every chunk. For each chunk:
   - translate only `segments`;
   - use `context_before`, `context_after`, and the job glossary for consistency;
   - save a matching file in the job's `translations/` directory using the schema in `references/job-schema.md`.
4. Run `scripts/translation_job.py status <job-dir>` and resolve missing chunks or target languages.
5. Run `scripts/translation_job.py merge <job-dir>`.
6. Review the merged result for term consistency, missing text, duplicated overlap, and paragraph order.
7. Render final artifacts with `scripts/render_outputs.py` when HTML or Markdown is requested.

Never merge chunks by simple string concatenation when a JobID exists. Merge by stable block/segment IDs and validate completeness first.

## Translation behavior

Translate for meaning while preserving source scope and information.

- Do not summarize, omit, expand, or add claims unless the user asks for adaptation instead of translation.
- Preserve paragraph count when the source clearly defines paragraphs.
- Preserve sentence order. Sentence numbering is optional unless requested or useful for alignment.
- If the user requests sentence numbering, number continuously within each source document unless they request per-paragraph numbering.
- Keep technical terminology consistent across chunks. Maintain/update `glossary.json` for recurring proper names, acronyms, technical terms, product names, and fixed translations.
- Preserve citations with the content they support.
- Preserve equations and symbols exactly unless notation localization is explicitly requested.
- Keep code unchanged by default. Translate prose around code; translate code comments only when explicitly requested or clearly useful.
- For tables, translate cell content without changing row/column meaning. Preserve numeric cells exactly.

## Output selection

Support:

- `text`: translated text in chat;
- `html`: selectable HTML;
- `md`: Markdown;
- `both`: HTML + Markdown;
- `text + files`: chat translation plus file artifacts.

If the user says `全选`, `都要`, `HTML + MD`, `html、md`, or equivalent, generate both HTML and Markdown. If the user asks for a file but does not specify HTML or Markdown, generate both by default.

### HTML requirements

Generate real selectable text, never canvas-rendered text.

The HTML must:

- preserve source block order;
- support one or multiple target languages;
- show source and translation together by default;
- provide view buttons for `全部`, `仅原文`, and each target language;
- provide `全选全文` and `复制全文` controls;
- use embedded CSS/JS only, with no external CDN requirement;
- remain readable without JavaScript;
- include print-friendly styling.

### Markdown requirements

The Markdown must:

- preserve the same logical block order as HTML;
- keep source and each translation clearly labeled;
- preserve headings, paragraphs, lists, tables, citations, and code fences where possible;
- remain usable in Obsidian, Typora, GitHub, and plain Markdown viewers.

## Optional imitation mode

Preserve the previous skill's imitation capability, but keep it optional.

When the user explicitly asks to `仿照`, `仿写`, `imitate`, or create a parallel example:

1. Identify the source's structural/rhetorical pattern.
2. Create new content for the user's requested topic using that pattern rather than copying wording or claims.
3. Label it clearly as `仿写示例` or equivalent.
4. Keep imitation content separate from the literal translation.
5. Translate the imitation too only when requested.
6. Never present fabricated example facts, citations, or measurements as real research.

## Final validation

Before delivery, verify:

- all source blocks are present and in order;
- every required target language has a translation for every translatable block;
- no chunk is missing or duplicated;
- paragraph, list, table, and citation alignment is preserved;
- terminology is consistent across chunks;
- numbers, units, formulas, code, URLs, and identifiers are unchanged unless explicitly localized;
- unreadable source content is marked rather than guessed;
- generated HTML contains selectable text and the requested view/copy controls;
- generated file links correspond to files that actually exist.
