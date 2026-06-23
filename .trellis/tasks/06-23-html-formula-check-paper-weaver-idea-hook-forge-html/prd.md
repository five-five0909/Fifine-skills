# html-formula-check：HTML 公式清单提取 + AI 逐条审查修复

## 状态
- 创建时间：2026-06-23
- 负责人：fifine
- 类型：NEW_FEATURE
- 优先级：高

## 背景与动机
pdf-paper-weaver（KaTeX）和 idea-hook-forge（MathJax）生成的 final_report.html
有时公式渲染失败，原因多样（HTML 实体残留、括号不平衡、公式为空等），目前没有任何
收尾检查步骤，只能浏览器肉眼发现。

**设计原则：Python 只做机械提取，AI 做语义判断和修复。**
类比 TDD：Python 输出公式清单（测试列表），AI 逐条过、发现问题就修，修完打勾。

## 核心流程

```
run_pipeline.py 跑完生成 HTML
    ↓
check_formula.py --html final_report.html --engine katex|mathjax
    ↓
输出 formula_manifest.json（公式编号/内容/来源/状态字段）
    ↓
AI 读取 manifest，逐条审查每条公式
    ↓
对有问题的条目：AI 直接修改 HTML（或 source values.json）
    ↓
全部过完 → manifest 中 status 全部更新 → 打印审查完成摘要
```

## 目标与成功标准
- [ ] 两个 skill 各自 `scripts/check_formula.py` 新建，职责仅为**提取+编号+生成 manifest**
- [ ] `run_pipeline.py` 末尾硬编码调用 `check_formula.py`，不可绕过
- [ ] 生成 `formula_manifest.json` 与 `final_report.html` 同目录
- [ ] manifest 字段完整（见下），足够 AI 无需看 HTML 就能定位和判断每条公式
- [ ] SKILL.md 中补充 AI 审查行为说明（AI 看到 manifest 后的操作步骤）

## formula_manifest.json 字段设计

```json
{
  "html_path": "绝对路径",
  "engine": "katex | mathjax",
  "generated_at": "ISO时间",
  "total": 3,
  "formulas": [
    {
      "id": 0,
      "source": "formula_thread / section名",
      "type": "display | inline",
      "raw": "原始 LaTeX 内容",
      "context_before": "公式前50字符 HTML 上下文",
      "context_after": "公式后50字符 HTML 上下文",
      "status": "pending",
      "note": ""
    }
  ]
}
```

`status` 取值：`pending` / `ok` / `fixed` / `flagged`

## 技术范围

### 涉及文件
```
pdf-paper-weaver/scripts/check_formula.py     ← 新建
pdf-paper-weaver/scripts/run_pipeline.py      ← 末尾追加调用（import 内调用）
pdf-paper-weaver/SKILL.md                     ← 补充 AI 审查步骤说明

idea-hook-forge/scripts/check_formula.py      ← 新建（与 weaver 同逻辑，engine 不同）
idea-hook-forge/scripts/run_pipeline.py       ← 末尾追加调用
idea-hook-forge/SKILL.md                      ← 补充 AI 审查步骤说明
```

### 两种引擎公式定位规则
| Skill | 引擎 | display 公式正则 |
|-------|------|----------------|
| pdf-paper-weaver | katex | `<div class="math-block">\$\$(.*?)\$\$</div>` (re.S) |
| idea-hook-forge | mathjax | `\\\[(.*?)\\\]` in `<div class="formula-math">` (re.S) |

### check_formula.py 接口
```bash
python check_formula.py --html <路径> --engine katex|mathjax [--output <路径>]
```
- 仅提取，不修改 HTML
- 输出 formula_manifest.json
- 打印摘要：提取了多少条，manifest 路径

### run_pipeline.py 集成方式
```python
# 末尾追加，渲染 HTML 之后
import sys, importlib.util
_spec = importlib.util.spec_from_file_location(
    "check_formula", Path(__file__).parent / "check_formula.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_mod.run_check(html_path, engine="katex")  # 或 "mathjax"
```
（用 importlib 而非 import，避免两个 skill 的 check_formula 互相冲突）

### 不在范围内
- Python 不做任何公式质量判断（判断交给 AI）
- 不做 LaTeX 语法验证
- 不自动修改 HTML

## SKILL.md 需补充的 AI 审查行为

在"输出目录确认"之后，补充"公式审查步骤"节：

```markdown
## 公式审查步骤（收尾阶段）

HTML 生成完毕后，脚本自动输出 `formula_manifest.json`。
AI 必须执行以下逐条审查流程：

1. 读取 `formula_manifest.json`
2. 对每条 `status: pending` 的公式：
   - 检查 `raw` 字段内容是否合法 LaTeX
   - 常见问题：HTML 实体（`&lt;` `&gt;`）、括号不平衡、公式为空、混有 HTML 标签
   - 无问题 → 将 `status` 改为 `ok`
   - 有问题但可修复 → 修改 HTML 中对应公式，将 `status` 改为 `fixed`，`note` 填写修改说明
   - 有问题无法自动判断 → 将 `status` 改为 `flagged`，`note` 填写疑问
3. 全部审查完毕后，更新 manifest 文件
4. 打印审查摘要：ok / fixed / flagged 各多少条
```

## 任务拆分
1. 写 `check_formula.py`（逻辑共用，engine 参数区分）
2. 集成到 `pdf-paper-weaver/scripts/run_pipeline.py`
3. 集成到 `idea-hook-forge/scripts/run_pipeline.py`
4. 更新两个 SKILL.md，补充 AI 审查步骤说明

## 验收清单
- [ ] `python check_formula.py --html xxx.html --engine katex` 输出 manifest
- [ ] `python check_formula.py --html xxx.html --engine mathjax` 输出 manifest
- [ ] 运行 weaver 的 run_pipeline.py 后自动生成 manifest
- [ ] 运行 forge 的 run_pipeline.py 后自动生成 manifest
- [ ] manifest 字段齐全，raw 字段内容正确提取
- [ ] SKILL.md 中有 AI 审查步骤说明
