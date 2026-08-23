# Fabricated example

This example is invented only to demonstrate the skill. It is not a real paper or source document.

## Example A: image-based academic translation

User request:

> 把这 7 张论文截图翻译成中文，严格按原文分段并标句序号，HTML 和 MD 都要。

Expected behavior:

1. Because there are 7 images, use JobID mode.
2. Inspect images 1–4, then 5–7, appending normalized blocks in source order.
3. Join paragraphs that clearly continue across screenshot boundaries.
4. Normalize the complete source into blocks.
5. Create a JobID and chunk at approximately 12,000 source characters.
6. Translate each chunk with continuous sentence numbering across the document.
7. Merge by segment IDs.
8. Generate selectable HTML and Markdown.

Example job summary:

```text
JobID: tr-20260823-234500-a1b2c3d4
Inputs: 7 images
Source blocks: 18
Source characters: 24,680
Translation chunks: 3
Target: zh-CN
Outputs: HTML + Markdown
```

The HTML provides `全部`, `仅原文`, `仅中文`, `全选全文`, and `复制全文` controls.

## Example B: mixed file translation

User request:

> 把 report.pdf、notes.md 和我下面贴的这段话一起翻译成中日双语，保持标题、段落和表格结构。

Expected policy:

- one batch JobID;
- `target_languages = ["zh-CN", "ja-JP"]`;
- each block records `source_file`;
- PDF pages are inspected in windows of at most 6 pages when needed;
- Markdown structure is preserved;
- pasted text becomes an additional source block;
- final HTML can switch between source, Chinese, Japanese, or all.

## Example C: optional imitation

Source pattern:

1. background and importance;
2. common method;
3. limitation;
4. unresolved gap;
5. present work.

User asks:

> 翻译完以后，再仿照这个结构写一个关于土壤光谱重建的小引言。

Create the literal translation first. Then create a separate `仿写示例` that follows the five-move structure but does not copy distinctive wording, data, citations, or claims. If factual support is unavailable, keep the imitation clearly illustrative rather than inventing real-looking evidence.
