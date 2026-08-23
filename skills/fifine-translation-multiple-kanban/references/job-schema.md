# Job schema

## Contents

1. Normalized source input
2. Job directory layout
3. Chunk schema
4. Translation chunk schema
5. Merged output schema
6. Commands

## 1. Normalized source input

Create UTF-8 JSON like this before `translation_job.py create`:

```json
{
  "title": "Optional source title",
  "source_name": "paper.pdf",
  "source_language": "auto",
  "target_languages": ["zh-CN"],
  "blocks": [
    {
      "id": "b000001",
      "type": "heading",
      "text": "Introduction",
      "order": 1,
      "page": 1,
      "source_file": "paper.pdf"
    },
    {
      "id": "b000002",
      "type": "paragraph",
      "text": "First paragraph...",
      "order": 2,
      "page": 1,
      "source_file": "paper.pdf"
    }
  ]
}
```

Required fields:

- `blocks`: non-empty list

Recommended fields:

- `title`
- `source_name`
- `source_language`
- `target_languages`

Each block requires:

- `id`: stable unique ID
- `type`: logical block type
- `text`: source text
- `order`: integer source order

Additional metadata is preserved.

## 2. Job directory layout

```text
translation_jobs/
└── tr-YYYYMMDD-HHMMSS-xxxxxxxx/
    ├── manifest.json
    ├── glossary.json
    ├── source.json
    ├── chunks/
    │   ├── chunk-0001.json
    │   └── chunk-0002.json
    ├── translations/
    │   ├── chunk-0001.json
    │   └── chunk-0002.json
    └── final/
        └── translation.json
```

## 3. Chunk schema

Generated automatically:

```json
{
  "job_id": "tr-20260823-234500-a1b2c3d4",
  "chunk_id": "chunk-0001",
  "source_language": "auto",
  "target_languages": ["zh-CN"],
  "context_before": "...",
  "context_after": "...",
  "segments": [
    {
      "segment_id": "b000002::s001",
      "parent_id": "b000002",
      "type": "paragraph",
      "source": "...",
      "order": 2,
      "segment_order": 1,
      "segment_count": 1,
      "page": 1,
      "source_file": "paper.pdf"
    }
  ]
}
```

Translate only `segments[].source`. Context fields are reference-only and must not be duplicated into the translation output.

## 4. Translation chunk schema

Save one file per chunk in `translations/` with the same filename as the source chunk:

```json
{
  "job_id": "tr-20260823-234500-a1b2c3d4",
  "chunk_id": "chunk-0001",
  "translations": [
    {
      "segment_id": "b000002::s001",
      "translated": {
        "zh-CN": "对应的中文翻译。"
      }
    }
  ]
}
```

For multiple target languages:

```json
"translated": {
  "zh-CN": "中文翻译。",
  "ja-JP": "日本語訳。"
}
```

Every segment must contain every target language listed in the manifest.

## 5. Merged output schema

`merge` produces:

```json
{
  "job_id": "tr-20260823-234500-a1b2c3d4",
  "title": "Optional source title",
  "source_name": "paper.pdf",
  "source_language": "auto",
  "target_languages": ["zh-CN"],
  "blocks": [
    {
      "id": "b000002",
      "type": "paragraph",
      "order": 2,
      "source": "First paragraph...",
      "translations": {
        "zh-CN": "第一段……"
      },
      "page": 1,
      "source_file": "paper.pdf"
    }
  ]
}
```

Split segments are reassembled into their original parent block before rendering.

## 6. Commands

Create a job from normalized JSON:

```bash
python scripts/translation_job.py create normalized.json \
  --out-root translation_jobs \
  --target zh-CN \
  --target ja-JP
```

When no `--target` is provided and the source manifest has no target list, the
bundled script defaults to `zh-CN`, matching the skill's Chinese-request
default. Pass one or more `--target` flags to override it.

Override chunk sizing:

```bash
python scripts/translation_job.py create normalized.json \
  --out-root translation_jobs \
  --target zh-CN \
  --chunk-target 10000 \
  --chunk-max 14000
```

Check completeness:

```bash
python scripts/translation_job.py status translation_jobs/<job-id>
```

Merge:

```bash
python scripts/translation_job.py merge translation_jobs/<job-id>
```

Render:

```bash
python scripts/render_outputs.py \
  translation_jobs/<job-id>/final/translation.json \
  --out-dir translation_jobs/<job-id>/final \
  --format both \
  --basename translated_document
```
