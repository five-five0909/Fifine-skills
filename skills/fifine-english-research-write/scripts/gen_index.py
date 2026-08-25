#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_index.py
============
根据 stats.json 与各章 reference 的 (a)词汇库规模 (b)写作技巧章节标题 自动生成
references/index.md (章节路由 + 技巧清单 + 范例句基线摘要)。

动态生成可避免手写数字与 stats 脱节。
"""
import os
import re
import json

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(SKILL, "references")
SECTIONS = ["introduction", "method", "results", "discussion", "conclusion"]
SECTION_TITLE = {
    "introduction": "Introduction",
    "method": "Methods",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
}

# 每章覆盖的写作技巧 (从 LWS 段标题归纳, 用于路由清单)
SKILLS_COVERED = {
    "introduction": ["Verb tense choices (Past/Present/Present Perfect)",
                     "Linking sentences & information", "Passive/Active choices", "Paragraphing"],
    "method": ["Describing materials/methods", "Verb tense (Past Simple dominant)",
               "Passive voice for procedures", "Sequencing & linking steps"],
    "results": ["Reporting results (Past tense)", "Quantitative/comparative language",
                "Signalling cause & result", "Linking data to known facts"],
    "discussion": ["Moving from results to meaning", "Modal verbs for hedging",
                   "Comparing with other studies", "Verb tense in Discussion"],
    "conclusion": ["Verb tense in Conclusion", "Recalling the generic model",
                   "Evaluative language", "Summarising achievements & implications"],
}

# 宏观框架 macro-guide.md 章节映射 (xmind 节点顺序)
MACRO_SECTION = {
    "introduction": "## 1. 如何写好引言【introduction】",
    "method": "## 2.  怎么写方法【method】",
    "results": "## 3. 怎么写结果【Result】",
    "discussion": "## 4. 怎么写讨论【Discussion】",
    "conclusion": "## 5. 怎么写结论",
}
MACRO_EXTRA = {
    "abstract": "## 6. 怎么写摘要",
    "title": "## 7. 撰写标题",
    "checklist": "## 8. 清单和提示",
}


def extract_lws_headings(md):
    """提取 LWS 段内的 #### / ## 子标题作为技巧清单"""
    headings = []
    m = re.search(r"## 2\. Language and Writing Skills.*", md, re.S)
    if not m:
        return headings
    block = md[m.start():]
    for line in block.split("\n"):
        s = line.strip()
        if re.match(r"^#{2,4}\s+\d", s) or re.match(r"^(VERB TENSE|LINKING|PASSIVE|PARAGRAPH|MODAL|HEDG|COMPAR|SEQUENC)", s, re.I):
            headings.append(re.sub(r"^#{1,4}\s*", "", s).strip())
    return headings[:12]


def main():
    stats = json.load(open(os.path.join(REF, "stats.json"), encoding="utf-8"))
    secs = stats["sections"]

    L = []
    L.append("# Reference Index — English Research Writing\n")
    L.append("Routes the agent to the correct per-section reference. "
             "Read `index.md` first when the target section is unclear; otherwise open the specific `<section>.md`.\n")

    # 路由表
    L.append("## Routing Table")
    L.append("")
    L.append("| Need | Reference file | Notes |")
    L.append("|---|---|---|")
    for s in SECTIONS:
        st = secs[s]
        L.append(f"| {SECTION_TITLE[s]} (IMRaD) | `{s}.md` + `macro-guide.md` `{MACRO_SECTION[s]}` | "
                 f"micro vocab={st['vocab_count']}, examples={st['example_sentence_count']} |")
    L.append(f"| Abstract (摘要) | `macro-guide.md` `{MACRO_EXTRA['abstract']}` | book lacks this; mind-map covers it |")
    L.append(f"| Title (标题) | `macro-guide.md` `{MACRO_EXTRA['title']}` | journal-title analysis |")
    L.append(f"| General checklist / tips | `macro-guide.md` `{MACRO_EXTRA['checklist']}` | cross-section |")
    L.append(f"| Planning / structure / sentence-function | `macro-guide.md` (matching `## N.`) | macro layer |")
    L.append("")
    L.append("> Two-layer model: `macro-guide.md` = WHAT to say & WHY (structure, function, principles); "
             "`<section>.md` = HOW to phrase it (vocab, tense, example patterns). Apply both per section.")
    L.append("")

    # 各章技巧清单 + 基线
    L.append("## Per-Section Writing Skills & Stylistic Baseline")
    L.append("")
    for s in SECTIONS:
        st = secs[s]
        md = open(os.path.join(REF, f"{s}.md"), encoding="utf-8").read()
        headings = extract_lws_headings(md)
        td = st["tense_distribution_approx"]["proportions_approx"]
        L.append(f"### {SECTION_TITLE[s]}  (`{s}.md` + `macro-guide.md` `{MACRO_SECTION[s]}`)")
        L.append(f"- **UWP vocabulary bank**: {st['vocab_count']} phrases")
        L.append(f"- **Example corpus**: {st['example_sentence_count']} sentences "
                 f"(avg **{st['avg_words_per_example_sentence']}** words/sentence; "
                 f"range {st['min_words']}–{st['max_words']})")
        L.append(f"- **Tense distribution (approx)**: past={td['past']}, present={td['present']}, "
                 f"perfect={td['perfect']}, mixed={td['mixed']}")
        L.append(f"- **Macro framework**: see `macro-guide.md` → `{MACRO_SECTION[s]}` "
                 f"(structure, sentence-function map, template, global principles)")
        L.append("- **Writing skills covered (micro)**:")
        for h in (headings or SKILLS_COVERED[s]):
            L.append(f"  - {h}")
        L.append("")

    L.append("## Macro Framework (`macro-guide.md`)")
    L.append("")
    L.append("Distilled from the Chinese mind-map **英语科技写作** (295 nodes). It is the *big-picture* layer: "
             "section structure, sentence-function mapping, templates, and global principles. The book-based "
             "`<section>.md` files supply the *detailed* vocabulary & example patterns that realise it.")
    L.append("")
    L.append("| Macro topic | `macro-guide.md` section |")
    L.append("|---|---|")
    for s in SECTIONS:
        L.append(f"| {SECTION_TITLE[s]} | `{MACRO_SECTION[s]}` |")
    L.append(f"| Abstract | `{MACRO_EXTRA['abstract']}` |")
    L.append(f"| Title | `{MACRO_EXTRA['title']}` |")
    L.append(f"| Checklist & tips | `{MACRO_EXTRA['checklist']}` |")
    L.append("")
    L.append("## How to Use as Generation Constraint")
    L.append("When generating a section draft, read the matching `<section>.md` AND `stats.json` AND the "
             "matching `macro-guide.md` `## N.` section. Keep the draft close to that section's "
             "`avg_words_per_example_sentence` and `tense_distribution_approx`, AND follow the macro "
             "structure/sentence-function map. (Tense distribution is approximate — surface heuristic, no POS.)")
    L.append("")
    L.append("> Fidelity verified by `verify_fidelity.py` (vocab coverage ≥99%, example sentences exact, "
             "HTML phrase coverage ≥98%). See `verify_report.md`.")

    out = os.path.join(REF, "index.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"[OK] wrote {out} ({len(L)} lines)")


if __name__ == "__main__":
    main()
