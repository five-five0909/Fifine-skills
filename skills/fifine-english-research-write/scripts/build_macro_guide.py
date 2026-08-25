# -*- coding: utf-8 -*-
"""build_macro_guide.py
将 mind-map (xmind) 的 content.json 递归转换为结构化 Markdown -> references/macro-guide.md。
保留全部节点文本与层级 (宏观写作框架)；空标题节点跳过。
复现命令: python build_macro_guide.py
"""
import zipfile, json, os, re

XMIND = r"e:\code_space\agent-space\ai-temp\mind_ideas\英语科技写作\英语科技写作.xmind"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "references", "macro-guide.md")


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


def clean(text):
    text = (text or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def walk(node, depth, out):
    title = clean(node.get("title", ""))
    if title:
        if depth == 0:
            out.append(f"# {title}\n")
        elif depth == 1:
            out.append(f"## {title}\n")
        elif depth == 2:
            out.append(f"### {title}\n")
        else:
            indent = "  " * (depth - 3)
            out.append(f"{indent}- {title}")
    for ch in get_children(node):
        walk(ch, depth + 1, out)


def main():
    z = zipfile.ZipFile(XMIND)
    data = json.loads(z.read("content.json").decode("utf-8"))
    root = data[0]["rootTopic"] if isinstance(data[0], dict) and "rootTopic" in data[0] else data[0]
    out = []
    walk(root, 0, out)
    md = "\n".join(out)
    md = re.sub(r"^\s*-\s*$", "", md, flags=re.M)
    md = re.sub(r"\n{3,}", "\n\n", md)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] wrote {OUT} ({len(md)} chars, {md.count(chr(10))} lines)")


if __name__ == "__main__":
    main()
