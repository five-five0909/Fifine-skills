#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_stats.py
=================
从 build_references.py 生成的 5 个 reference Markdown 中, 基于「Example Corpus (范例论文句)」
计算每章量化基线指标, 输出 references/stats.json。

指标用途 (用户明确):
  - 展示: 让用户/AI 了解该章真实论文句的风格基线
  - 校验基线: verify_fidelity 可复核
  - 生成硬约束: SKILL.md 生成模式要求生成稿的句长/时态分布接近本基线

注意: 时态分布为纯文本启发式近似 (无 POS 标注), 字段名与说明均标注 approx, 不夸大精度。
"""
import os
import re
import json

REF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
SECTIONS = ["introduction", "method", "results", "discussion", "conclusion"]

# ---------------------------------------------------------------------------
# 解析 helper
# ---------------------------------------------------------------------------

def extract_examples(md):
    """从 reference 的 '## 3. Example Corpus' 段提取例句列表 [(sentence, pdf_page)]"""
    m = re.search(r"## 3\. Example Corpus.*?(?=\n## |\Z)", md, re.S)
    if not m:
        return []
    block = m.group(0)
    out = []
    for line in block.split("\n"):
        s = line.strip()
        if not s.startswith("- "):
            continue
        # 去掉末尾的 *[PDF pXX]*
        sent = re.sub(r"\*\[PDF p\d+\]\*$", "", s[2:]).strip()
        sent = re.sub(r"\s+", " ", sent)
        if sent:
            out.append(sent)
    return out


def extract_vocab_count(md):
    """从 '## 1. Useful Words and Phrases' 段统计词汇短语总数 (按行解析表格, 逗号拆分去重, 与 build/verify 口径一致)"""
    i = md.find("## 1. Useful Words and Phrases")
    if i < 0:
        return 0
    j = md.find("## 2. Language", i + 10)
    if j < 0:
        j = len(md)
    block = md[i:j]
    phrases = set()
    for line in block.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|$", s):
            continue
        for c in s.strip("|").split("|"):
            for ph in re.split(r"\s*,\s*", c):
                ph = ph.strip().lower()
                if ph and ph not in ("column a", "column b"):
                    phrases.add(ph)
    return len(phrases)


# ---------------------------------------------------------------------------
# 时态近似探测 (纯启发式, 标注 approx)
# ---------------------------------------------------------------------------

PAST_SIMPLE = re.compile(r"\b(\w+ed|\w+ew|found|showed|demonstrated|reported|observed|revealed|"
                         r"proposed|argued|concluded|increased|decreased|developed|measured|"
                         r"analysed|analyzed|compared|provided|obtained|achieved|required|"
                         r"allowed|enabled|led|resulted|occurred|existed|contained|represented|"
                         r"extended|generated|modified|applied|affected|rose|hypothesized|"
                         r"confirmed|expanded|described|began|built|made|took|gave|saw|came|"
                         r"wrote|drew|froze|chose|flew|broke|spoke|wore|bore|tore|sought|"
                         r"brought|thought|fought|caught|taught|bent|spent|sent|kept|slept|"
                         r"left|met|set|let|put|cut|hit|fit|shut|split|spread|burst)\b", re.I)

PRESENT_SIMPLE = re.compile(r"\b(is|are|was|were|shows?|demonstrates?|presents?|reports?|"
                            r"indicates?|suggests?|appears?|seems?|remains?|provides?|"
                            r"contains?|represents?|extends?|leads?|results?|exists?|occurs?|"
                            r"requires?|allows?|enables?|affects?|rises?|generates?|describes?)\b", re.I)

PRESENT_PERFECT = re.compile(r"\b(has|have|had)\s+(\w+ed|been|shown|demonstrated|reported|"
                             r"observed|revealed|proposed|argued|concluded|increased|decreased|"
                             r"developed|measured|analysed|analyzed|compared|provided|obtained|"
                             r"achieved|required|allowed|enabled|led|resulted|occurred|extended|"
                             r"generated|modified|applied|affected|confirmed|expanded|described)\b", re.I)


def classify_tense(sent):
    """返回 'past' / 'present' / 'perfect' / 'mixed' / 'unknown' (approx)"""
    has_past = bool(PAST_SIMPLE.search(sent))
    has_pres = bool(PRESENT_SIMPLE.search(sent))
    has_perf = bool(PRESENT_PERFECT.search(sent))
    # 校正: has/have + 过去分词 优先 perfect
    if has_perf:
        if has_past and not has_pres:
            return "mixed"
        return "perfect"
    if has_past and has_pres:
        return "mixed"
    if has_past:
        return "past"
    if has_pres:
        return "present"
    return "unknown"


def compute_tense_dist(sentences):
    buckets = {"past": 0, "present": 0, "perfect": 0, "mixed": 0, "unknown": 0}
    for s in sentences:
        buckets[classify_tense(s)] += 1
    n = len(sentences)
    dist = {k: (round(v / n, 3) if n else 0.0) for k, v in buckets.items()}
    return {"counts": buckets, "proportions_approx": dist, "method_note":
            "Approximate heuristic over surface verb forms (no POS tagging). "
            "'past'=Past Simple markers, 'present'=Present Simple markers, "
            "'perfect'=has/have+participle, 'mixed'=both past&present markers."}


def paragraph_pattern(sentences, md):
    """近似段落节奏: 按 Example Corpus 中例句在原文里的空行/块分组, 统计每组句数。
    由于 build 已将例句平铺为列表, 这里用 reference 中例句之间的空行近似还原块结构。"""
    m = re.search(r"## 3\. Example Corpus.*?(?=\n## |\Z)", md, re.S)
    if not m:
        return {}
    block = m.group(0)
    # 按空行分段, 统计每段含多少例句
    groups = [g for g in re.split(r"\n\s*\n", block) if "- " in g]
    sizes = [g.count("\n- ") + (1 if g.strip().startswith("- ") else 0) for g in groups]
    sizes = [s for s in sizes if s > 0]
    if not sizes:
        return {}
    from collections import Counter
    cnt = Counter(sizes)
    return {
        "group_count": len(sizes),
        "sentences_per_group": dict(sorted(cnt.items())),
        "avg_sentences_per_group": round(sum(sizes) / len(sizes), 2),
        "note": "Approximate: groups inferred from blank-line separation in the extracted corpus.",
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    stats = {}
    for sec in SECTIONS:
        path = os.path.join(REF_DIR, f"{sec}.md")
        md = open(path, encoding="utf-8").read()
        examples = extract_examples(md)
        vocab = extract_vocab_count(md)
        word_counts = [len(s.split()) for s in examples]
        avg_words = round(sum(word_counts) / len(word_counts), 1) if word_counts else 0
        stats[sec] = {
            "vocab_count": vocab,
            "example_sentence_count": len(examples),
            "avg_words_per_example_sentence": avg_words,
            "min_words": min(word_counts) if word_counts else 0,
            "max_words": max(word_counts) if word_counts else 0,
            "tense_distribution_approx": compute_tense_dist(examples),
            "paragraph_rhythm_approx": paragraph_pattern(examples, md),
        }
        print(f"[OK] {sec}: vocab={vocab} examples={len(examples)} "
              f"avg_words={avg_words} tense={stats[sec]['tense_distribution_approx']['proportions_approx']}")

    out = {
        "_meta": {
            "description": "Per-section stylistic baseline derived from Example Corpus "
                           "(sentences excerpted from published research articles in the source book).",
            "purpose": ["display", "fidelity_check", "generation_hard_constraint"],
            "usage": "SKILL.md generation mode MUST read this file and require generated drafts to "
                     "approximate avg_words_per_example_sentence and tense_distribution_approx.",
            "caveats": ["tense_distribution is APPROXIMATE (surface heuristic, no POS).",
                        "paragraph_rhythm is APPROXIMATE (inferred from blank-line grouping).",
                        "Baselines reflect the source book's excerpted examples, not a universal rule."],
        },
        "sections": stats,
    }
    out_path = os.path.join(REF_DIR, "stats.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(f"\n[OK] wrote {out_path}")


if __name__ == "__main__":
    main()
