#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_references.py
===================
从 OCR 复原的逐页 Markdown 中，逐字精确提取《Science Research Writing》Unit 1-5 的
  (a) Useful Words and Phrases 词汇库 (HTML 表格 -> Markdown 表格)
  (b) Language and Writing Skills 规则讲解 (原文保留, 去页眉噪声)
  (c) Example Corpus 范例论文句 (书中从真实论文摘的例句, 作生成基线)
按 IMRaD 章节类型归并, 输出到 ../references/<section>.md

设计原则: 逐字保真, 不做任何 LLM 改写; 逐页标注 [PDF pXX] 来源.
"""
import os
import re
import glob
import html as htmlmod

# ---------------------------------------------------------------------------
# 配置: 章节 -> (OCR 片段 key 列表, 该片段在原 PDF 的起始页, IMRaD 章节名, Unit 标题)
# ---------------------------------------------------------------------------
OCR = r"e:\code_space\agent-space\ai-temp\ocr_work\ocr"

SECTIONS = {
    "introduction": {
        "unit": "UNIT 1 — How to Write the Introduction",
        "start_pdf_page": 74,           # u1_uwp 起始页
        "fragments": [("u1_uwp", 74), ("u1_lws", 82)],
    },
    "method": {
        "unit": "UNIT 2 — How to Write about Methods",
        "start_pdf_page": 128,
        "fragments": [("u2_uwp", 128), ("u2_lws", 142)],
    },
    "results": {
        "unit": "UNIT 3 — How to Write about Results",
        "start_pdf_page": 184,
        "fragments": [("u3_uwp", 184), ("u3_lws", 198)],
    },
    "discussion": {
        "unit": "UNIT 4 — How to Write the Discussion",
        "start_pdf_page": 250,
        "fragments": [("u4_uwp", 250), ("u4_lws", 258)],
    },
    "conclusion": {
        "unit": "UNIT 5 — How to Write the Conclusion",
        "start_pdf_page": 287,
        "fragments": [("u5_uwp", 287), ("u5_lws", 288)],
    },
}

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def read_pages(key):
    """读取某片段所有 doc_<n>.md, 按页码序返回 [(pdf_page, text), ...]"""
    d = os.path.join(OCR, key, "pages")
    files = glob.glob(os.path.join(d, "doc_*.md"))
    files.sort(key=lambda x: int(re.findall(r"\d+", os.path.basename(x))[0]))
    out = []
    for idx, f in enumerate(files):
        # 该 doc 对应的原 PDF 页码 = 片段起始页 + 页序
        with open(f, encoding="utf-8") as fh:
            out.append((start_of(key) + idx, fh.read()))
    return out


def start_of(key):
    for sec in SECTIONS.values():
        for k, sp in sec["fragments"]:
            if k == key:
                return sp
    return 0


def strip_page_noise(line):
    """去除页眉页脚噪声: b3779, "9x6", 重复书名, 装饰空白符"""
    s = line
    s = re.sub(r"b\d{3,5}", "", s)                     # b3779 等页码标记
    s = re.sub(r"[\u201c\u201d]?9x6[\u201c\u201d]?", "", s)  # "9x6"
    s = re.sub(r"Science Research Writing[Â»\s]*w?", "", s)
    s = re.sub(r"Science Research Writing\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def clean_inline(text):
    """行内去噪 (去 HTML 实体/多余空白), 不破坏内容"""
    t = htmlmod.unescape(text)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def html_table_to_md(table_html):
    """把单个 <table>...</table> 转成 Markdown 表格, 单元格内逗号分隔的多个短语拆分保留。
    返回 (md_table, cell_phrases)"""
    # 提取所有行
    rows = re.findall(r"<tr>(.*?)</tr>", table_html, re.S)
    md_rows = []
    all_phrases = []
    for r in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        clean_cells = []
        for c in cells:
            ctext = clean_inline(c)
            clean_cells.append(ctext)
            # 单元格内可能逗号分隔多个短语
            for ph in re.split(r"\s*,\s*", ctext):
                ph = ph.strip()
                if ph:
                    all_phrases.append(ph)
        md_rows.append("| " + " | ".join(clean_cells) + " |")
    if not md_rows:
        return "", []
    # 加表头分隔行 (假设首行为表头)
    header = md_rows[0]
    ncol = header.count("|") - 1
    sep = "|" + "---|" * ncol
    md = "\n".join([md_rows[0], sep] + md_rows[1:])
    return md, all_phrases


def split_phrase_list(phrases):
    """把单元格聚合的短语列表去重输出, 用于 vocab_count 统计与校验"""
    out = []
    seen = set()
    for p in phrases:
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out


# 宽松动词探测: 覆盖常见学术动词 + 动词性后缀 (-ed/-es/-ing)
_VERB_RE = re.compile(
    r"\b(is|are|was|were|be|been|being|has|have|had|do|does|did|can|could|may|might|"
    r"must|should|will|would|shall|suggest|suggests|indicate|indicates|show|shows|"
    r"showed|demonstrate|demonstrates|demonstrated|present|presents|presented|report|"
    r"reports|reported|observe|observes|observed|reveal|reveals|revealed|propose|"
    r"proposes|proposed|argue|argues|argued|conclude|concludes|concluded|appear|"
    r"appears|appeared|seem|seems|remain|remains|increase|increases|increased|decrease|"
    r"decreases|decreased|develop|develops|developed|measure|measures|measured|analyse|"
    r"analyses|analysed|analyze|analyzes|analyzed|compare|compares|compared|provide|"
    r"provides|provided|obtain|obtains|obtained|achieve|achieves|achieved|require|"
    r"requires|required|allow|allows|allowed|enable|enables|enabled|lead|leads|led|"
    r"result|results|resulted|occur|occurs|occurred|exist|exists|existed|contain|"
    r"contains|contained|represent|represents|represented|extend|extends|extended|"
    r"generate|generates|generated|modify|modifies|modified|apply|applies|applied|"
    r"affect|affects|affected|rise|rises|rose|hypothesize|hypothesizes|hypothesized|"
    r"confirm|confirms|confirmed|expand|expands|expanded|describe|describes|described)\b"
    r"|[A-Za-z]+ed\b|[A-Za-z]+es\b|[A-Za-z]+ing\b",
    re.I,
)


def is_example_sentence(line):
    """判断一行是否为范例论文句 (Example Corpus):
       - 以 '- ' 或 '--' 开头的列表项
       - body 长度 >= 25 且词数 >= 6 (排除短词条)
       - 含动词性词 (宽松探测, 允许 (VRFB) is... 这类括号开头)
       - 排除表格残留 (含 '|') 与纯编号列表"""
    s = line.strip()
    if not (s.startswith("- ") or s.startswith("--")):
        return False
    body = re.sub(r"^[-]+\s*", "", s).strip()
    if len(body) < 25:                      # 太短不是完整例句
        return False
    if "|" in body:                         # 表格单元格残留
        return False
    words = body.split()
    if len(words) < 6:
        return False
    if not _VERB_RE.search(body):           # 必须含动词性词
        return False
    return True


# ---------------------------------------------------------------------------
# 主处理: 单片段 -> 结构化内容
# ---------------------------------------------------------------------------

def process_fragment(key, pdf_page, text):
    """处理单页, 返回 dict:
       {'vocab_md':..., 'vocab_phrases':[...], 'rules_md':..., 'examples':[(sentence, page)]}
       为保证保真, rules_md 保留全部非表格/非例句列表的原文(去噪)。
       表格归属: uwp 片段的表格 = 学术词汇库(vocab); lws 片段的表格 = 写作规则/练习(rules)。"""
    is_uwp = key.endswith("_uwp")
    # 1. 提取表格: uwp -> vocab, lws -> rules(作为讲解表格保留)
    vocab_phrases = []
    vocab_blocks = []
    rules_tables = []
    for m in re.finditer(r"<table.*?</table>", text, re.S):
        tbl = m.group(0)
        md, phrases = html_table_to_md(tbl)
        if is_uwp:
            vocab_phrases.extend(phrases)
            if md:
                vocab_blocks.append(md)
        else:
            if md:
                rules_tables.append(md)

    # 2. 去掉表格, 剩余文本按行处理 -> 规则讲解 + 例 sentences
    non_table = re.sub(r"<table.*?</table>", "", text, flags=re.S)
    non_table = re.sub(r"<!--.*?-->", "", non_table, flags=re.S)
    # 去除行内残留的孤立 <td>/<tr> 标签
    non_table = re.sub(r"</?(td|tr|table)[^>]*>", "", non_table)

    rule_lines = []
    examples = []
    for raw in non_table.split("\n"):
        line = strip_page_noise(raw)
        if not line:
            rule_lines.append("")
            continue
        if is_example_sentence(line):
            body = re.sub(r"^[-]+\s*", "", line).strip()
            examples.append((body, pdf_page))
            continue  # 例句不进入 rules_md, 单独归集
        rule_lines.append(line)

    rules_md = "\n".join(rule_lines).strip()
    # 折叠多余空行
    rules_md = re.sub(r"\n{3,}", "\n\n", rules_md)
    # lws 片段的表格作为讲解表格追加进 rules
    if rules_tables:
        rules_md = (rules_md + "\n\n" + "\n\n".join(rules_tables)).strip()
    return {
        "vocab_md": "\n\n".join(vocab_blocks),
        "vocab_phrases": vocab_phrases,
        "rules_md": rules_md,
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# 归并生成单章 reference
# ---------------------------------------------------------------------------

def build_section(sec_name, cfg, out_dir):
    collected_vocab = []      # [(md_block, phrases)]
    collected_rules = []      # [(pdf_page, md)]
    collected_examples = []   # [(sentence, pdf_page)]

    for key, _ in cfg["fragments"]:
        pages = read_pages(key)
        for pdf_page, txt in pages:
            r = process_fragment(key, pdf_page, txt)
            if r["vocab_md"]:
                collected_vocab.append((r["vocab_md"], r["vocab_phrases"]))
            if r["rules_md"]:
                collected_rules.append((pdf_page, r["rules_md"]))
            collected_examples.extend(r["examples"])

    # ---- 组装 Markdown ----
    lines = []
    lines.append(f"# {sec_name.capitalize()} — Academic Writing Reference")
    lines.append("")
    lines.append(f"> Source: {cfg['unit']} (Glasman-Deal, *Science Research Writing*). "
                 f"Content extracted verbatim from OCR; page tags `[PDF pXX]` denote the original PDF page.")
    lines.append("")
    lines.append("## 1. Useful Words and Phrases (Vocabulary Bank)")
    lines.append("")
    phrases_all = []
    for md, ph in collected_vocab:
        lines.append(md)
        lines.append("")
        phrases_all.extend(ph)
    phrases_unique = split_phrase_list(phrases_all)

    # ---- Language and Writing Skills ----
    lines.append("## 2. Language and Writing Skills (Rules & Guidance)")
    lines.append("")
    for pdf_page, md in collected_rules:
        lines.append(f"<details><summary>PDF page {pdf_page}</summary>\n")
        lines.append(md)
        lines.append("\n</details>\n")

    # ---- Example Corpus ----
    lines.append("## 3. Example Corpus (Sentences from Published Research Articles)")
    lines.append("")
    lines.append(f"Total example sentences extracted: **{len(collected_examples)}**. "
                 "Use these as the stylistic baseline for tone, tense, sentence length and paragraph rhythm.")
    lines.append("")
    for sent, pg in collected_examples:
        lines.append(f"- {sent}  *[PDF p{pg}]*")
    lines.append("")

    out_path = os.path.join(out_dir, f"{sec_name}.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return {
        "section": sec_name,
        "vocab_count": len(phrases_unique),
        "example_count": len(collected_examples),
        "rule_chars": sum(len(m) for _, m in collected_rules),
        "out_path": out_path,
    }


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
    os.makedirs(out_dir, exist_ok=True)
    summary = []
    for sec, cfg in SECTIONS.items():
        info = build_section(sec, cfg, out_dir)
        summary.append(info)
        print(f"[OK] {sec}: vocab={info['vocab_count']} examples={info['example_count']} -> {info['out_path']}")
    # 汇总
    print("\n=== build summary ===")
    for s in summary:
        print(f"  {s['section']:12s} vocab={s['vocab_count']:4d}  examples={s['example_count']:4d}")


if __name__ == "__main__":
    main()
