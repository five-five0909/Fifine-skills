# Input handling

## Contents

1. Pasted text
2. Images and screenshots
3. PDFs and document files
4. Multiple files and mixed inputs
5. Tables, code, and structured content
6. Pre-normalization batching

## 1. Pasted text

For short pasted text, preserve paragraph boundaries and translate directly unless JobID mode is requested.

For long pasted text, normalize paragraphs/list items/headings as blocks, then use JobID mode when the source exceeds the limits in `SKILL.md`.

## 2. Images and screenshots

Use the environment's native image understanding first. Do not invoke OCR merely because the input is an image if native visual reading is available and reliable.

Reconstruct content in reading order:

1. title/heading
2. main text blocks
3. captions/footnotes
4. tables or labels

Rules:

- Ignore decorative line wrapping.
- Join a paragraph continued across adjacent screenshots when the continuation is clear.
- Keep page/image provenance in block metadata when useful.
- Preserve visible superscripts, subscripts, citation marks, symbols, and equation notation.
- If text is illegible, record `[source unclear]` in normalized source or a target-language equivalent rather than guessing.

For more than 4 images, process them in source-order groups of at most 4 images per inspection pass, then append the resulting blocks to one normalized source before creating translation chunks.

## 3. PDFs and document files

Prefer the environment's document-reading tools when available. Preserve logical structure instead of flattening the document into one giant string.

Useful block types include:

- title
- heading
- paragraph
- list-item
- table
- caption
- footnote
- code

For PDFs with more than 6 pages, inspect page windows of at most 6 pages per pass when a full-document read would be unreliable. Record `page_start`/`page_end` or per-block `page` metadata and append blocks in exact source order.

For DOCX/PPTX/HTML/Markdown/text files, preserve existing headings, list levels, table structure, and code fences when the reader exposes them.

## 4. Multiple files and mixed inputs

Treat a mixed request as one batch when the user expects a combined deliverable.

Assign each block a `source_file` value and keep a deterministic `order` field. Use one JobID for the batch unless the user asks for separate jobs.

If the files require different target languages or radically different translation styles, prefer separate jobs so each manifest has one coherent policy.

## 5. Tables, code, and structured content

### Tables

Preserve row and column semantics. If a table is too large, split by complete rows, not arbitrary character offsets. Repeat the header as context only when needed; do not duplicate repeated headers in the merged output unless they were present in the source.

### Code

Keep code unchanged by default. Translate surrounding explanations. Preserve code fences and language tags. Translate comments only if explicitly requested.

### JSON/YAML/configuration

Do not translate keys, enum values, IDs, URLs, paths, or machine-readable values unless the user explicitly asks. Translate human-facing string values only when safe.

## 6. Pre-normalization batching

Large image/PDF inputs may need to be read in several passes before source JSON exists.

Use these default ingestion windows:

- images: up to 4 per pass;
- PDF/document pages: up to 6 per pass;
- dense tables/equations: reduce the window as needed.

After each pass, append normalized blocks in source order. Do not translate yet unless the job is intentionally streaming. Once normalization is complete, create the JobID and translation chunks from the combined source.
