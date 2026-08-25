# -*- coding: utf-8 -*-
"""核对 xmind 全部节点文本是否都进入了 macro-guide.md"""
import zipfile, json, os, re

XMIND = r"e:\code_space\agent-space\ai-temp\mind_ideas\英语科技写作\英语科技写作.xmind"
MACRO = r"e:\code_space\agent-space\ai-temp\skills\references\macro-guide.md"


def get_children(node):
    children = node.get("children", {})
    items = []
    if isinstance(children, dict):
        for k, v in children.items():
            if isinstance(v, list):
                items.extend(v)
    elif isinstance(children, list):
        items = children
    return items


def walk(node, out):
    out.append(node.get("title", "") or "")
    for ch in get_children(node):
        walk(ch, out)


z = zipfile.ZipFile(XMIND)
data = json.loads(z.read("content.json").decode("utf-8"))
root = data[0]["rootTopic"] if isinstance(data[0], dict) and "rootTopic" in data[0] else data[0]

all_titles = []
walk(root, all_titles)

# xmind 源里的换行是字面 '\n' (两字符)，归一化为真实换行再比较
def norm(s):
    return s.replace("\\n", "\n").strip()

nonempty = [norm(t) for t in all_titles if (t or "").strip()]
empty = len(all_titles) - len(nonempty)
print(f"xmind 总节点: {len(all_titles)}")
print(f"  非空节点(有文本): {len(nonempty)}")
print(f"  空节点(无文本):   {empty}")

# 读出 macro-guide 的全部可见文本块 (按行)
macro = open(MACRO, encoding="utf-8").read()
macro_lines = [l.rstrip() for l in macro.split("\n")]
macro_text = [l for l in macro_lines if l.strip() and not l.strip().startswith("#")]

# 检查每个非空 xmind 节点文本是否作为子串出现在 macro-guide 中
missing = []
for t in nonempty:
    # 节点文本可能跨多行，比较首尾关键片段
    if t not in macro:
        missing.append(t)

print(f"\nmacro-guide.md 文本行数(非标题): {len(macro_text)}")
print(f"未能在 macro-guide 中找到的节点数: {len(missing)}")
if missing:
    print("\n缺失节点样例(前20):")
    for m in missing[:20]:
        print("  -", m[:90])
    # 估算缺失文本占比
    miss_chars = sum(len(m) for m in missing)
    total_chars = sum(len(m) for m in nonempty)
    print(f"\n缺失文本字符占比: {miss_chars}/{total_chars} = {miss_chars/total_chars:.1%}")
