---
name: ppt-typography-designer
description: Design professional PowerPoint typography systems using a local audited font library. Use when selecting PPT fonts, matching Chinese and English typography, designing slide title hierarchies, creating font pairing recommendations, or generating typography previews.
---

# PPT Typography Designer

适用于 PPT 字体搭配、设计方案、字体样张以及现有 PPT/PPTX 的字体层级调整。默认从 ModelScope 数据集 `fifine/fifine-font` 同步字体到本机缓存，不自动安装字体；也可指定本地字体库。

## 工作流

1. 安装 `requirements.txt`，用 `python scripts/font_index.py build` 同步默认数据集并更新索引。私有数据集通过环境变量 `MODELSCOPE_API_TOKEN` 提供令牌，切勿写入文件；`--root` 或 `PPT_TYPOGRAPHY_FONT_ROOT` 可覆盖默认数据源。远端尚无字体时明确报错，不得伪称同步成功。
2. 用 `python scripts/recommend_typography.py --brief "主题与受众"` 生成三套不同方案。验证字体文件、字符覆盖、字重、安装与许可状态；缺失不得冒充存在。
3. 按需读取 `references/eight-design-styles.md`（包含具体字体家族及方案）、`typography-principles.md` 和 `font-pairing-rules.md`；完整历史文件清单及 SHA256 在 `references/font-manifest.json`。历史清单不代表当前远端可用或授权，勿将整份索引读入上下文。
4. 用 `python scripts/generate_preview.py --output 展示.pdf --format pdf` 生成真实字体展示；可选 `--style 03`、`--format png` 或 `pptx`。PPTX 使用真实文本框，并不自动安装字体。
5. 对现有文稿调用 `python scripts/apply_typography.py --input 原稿.pptx --output 新稿.pptx --style 03`。保留原文件；检查操作报告中的未处理对象、授权和实际显示限制。旧式 PPT 需要 Windows PowerPoint。

## 质量标准

输出封面、页面标题、模块小标题、正文、核心数字、英文标题、图表标签和图注的字体、字重、大小和必要的间距与颜色，解释视觉关系、混排、应用场景、缺失和替代。正文投影尽量不小于 18 pt；参考字号和排版规范见 `references/typography-principles.md`。不得伪称字体已安装、授权可商用、变量轴已应用或生成的 PPT 与 PowerPoint 实际显示一致。
