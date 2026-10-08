---
name: stem-illustration
description: STEM 领域 AI 图像生成 Skill。面向科研、教育、工程场景，生成信号通路、实验流程、机制图、细胞结构、概念信息图、学术海报、架构图等示意图。
---

# stem-illustration

面向 STEM（科学、技术、工程、数学）领域的 AI 图像生成 Skill，专注生成**科研示意图、教学插图、技术架构图**等概念性图像，覆盖生物医学、化学、物理、工程、数学 6 大学科。

## 何时使用

- 用户要生成科研示意图、机制图、流程图、流程海报、教学插图、学术图、技术架构图
- 用户提供主题/论文/概念/数据，期望出一张图（不限于"科研"，包括科普、教学、产品技术图）
- 学科关键词触发：信号通路、pathway、mechanism、细胞结构、anatomy、实验流程、workflow、质粒、plasmid、机器学习、neural network、力学、电路、化学结构、数学概念、信息图、海报、截面、爆炸图

## 不适用

- 真实实验数据图（散点/柱状/线图，学术诚信）→ 拒绝并提示使用 GraphPad/Origin/Python matplotlib
- 照片级写实（人像/风景/产品摄影）→ 用通用生图 skill
- 创意插画/卡通角色 → 用通用生图 skill

## 生图配置

复用 [scripts/generate_image.py](scripts/generate_image.py)，自动兼容 OpenAI 同步 API 和 apimart.ai 异步 API。

`.env` 字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `IMG_BASE_URL` | 是 | API 根地址 |
| `IMG_MODEL` | 是 | 图片模型 |
| `IMG_API_KEY` | 是 | API key |

模板：[.env.example](.env.example)（含 STEM 推荐参数说明）。

## 推荐尺寸

| 用途 | 比例 | 分辨率 |
|---|---|---|
| 期刊单栏图 | 4:3 | 2K |
| 期刊双栏图 | 16:9 | 2K |
| 垂直机制图（信号通路/树） | 3:4 | 2K |
| 学术海报（A0/A1） | 2:3 | 2K |
| PPT/幻灯片插图 | 16:9 | 2K |
| 正方形示意图 | 1:1 | 2K |
| 长流程横幅 | 21:9 | 2K |

## 核心流程（Brief / Prompt 模式，10 步）

1. **收集最小输入**：学科、图表类型、目标受众、关键术语清单、尺寸/比例、语言
2. **匹配场景模板**（24 个，见 [references/templates/](references/templates)）
3. **选择变体**：`academic` / `textbook` / `infographic` / `3d-render`
4. **套用学科提示**（模板的 `category_tips`）
5. **应用 STEM Prompt 铁律**（见下）
6. **组装 9 段 Prompt**（见下）
7. **应用 Campaign Style Lock**（多图任务）
8. **自检**（见 QA 清单）
9. **输出视觉简报**（中文，含 Prompt + 调用方式）
10. **若用户明确要求生图** → 调用 `scripts/generate_image.py`

## 最小输入

至少包含：

- **学科**：生命科学/医学/化学/物理/工程/数学
- **图表类型**：模板 ID（如 `signaling-pathway`、`experimental-workflow`）
- **目标受众**：K-12 / 高中 / 大学 / 研究生 / 同行研究者 / 公众科普
- **关键术语清单**：蛋白质名、化合物、公式等需准确呈现的术语
- **尺寸/比例**：见上表
- **语言**：中文 / 英文 / 双语

## 通用 Prompt 结构（9 段）

1. **Type**：图表类型（scientific mechanism diagram / data infographic / system architecture / ...）
2. **Subject**：主题（具体内容）
3. **Layout**：布局（top-to-bottom / left-to-right / 2x2 grid / radial / ...）
4. **Style**：风格（flat vector / textbook illustration / 3D render / infographic / ...）
5. **Color scheme**：用 hex 码（`#2563eb`、`#10b981` 等）
6. **Labels**：字体（中文 SimHei/Microsoft YaHei；英文 Arial/Helvetica；蛋白质名用标准基因符号；解剖术语拉丁名斜体）
7. **Quality**：4K / publication-ready / journal style
8. **Constraints**：禁止虚构、禁止错误方向、必须包含的关键元素
9. **Background**：white / dark / gradient / transparent

## STEM Prompt 铁律（10 条，**强制**）

1. **颜色用 hex 码**：`#10b981` 激活、`#ef4444` 抑制、`#3b82f6` 膜蛋白、`#2563eb` 数据主色
2. **方向显式声明**：`top-to-bottom vertical cascade`、`left-to-right horizontal flow`、`clockwise` / `counter-clockwise`
3. **字体明确指定**：中文 SimHei/Microsoft YaHei 粗体；英文 Arial/Helvetica
4. **术语标准化**：用 `MAPK/ERK` 不用"细胞信号"；用 `B-form DNA` 不用"DNA"；解剖术语拉丁名斜体括注
5. **分辨率和比例**：期刊图 4K，PPT 2K；单栏 4:3，双栏 16:9，垂直机制图 3:4
6. **否定清单**：禁止虚构数据/认证/相互作用/通路分支；禁止箭头方向错误
7. **标注规范**：激活实线、抑制虚线（T 型）；磷酸化用红圈 P；显著性 `*/**/***` 对应 p<0.05/0.01/0.001
8. **中英混排**：`线粒体 (Mitochondria)`，中文为主时英文括注；中英字号协调
9. **多子图编号**：A/B/C/D 加粗置于子图左上角
10. **期刊合规**：禁止用 AI 生成真实实验数据图（scatter/bar/line），仅限概念示意图

## 两阶段工作流（复杂任务）

### Architect 阶段（LLM 分析）

输出 **[VISUAL SCHEMA]**：

```
LAYOUT: 2x2 grid of 4 panels
PANEL A: [Top-left] Experimental workflow (5 steps)
PANEL B: [Top-right] Representative Western blot image
PANEL C: [Bottom-left] Quantification bar chart
PANEL D: [Bottom-right] Mechanism diagram
COLOR: Blue #2563eb primary, gray #6b7280 secondary
PANEL LABELS: A/B/C/D bold top-left
SHARED: Scale bar, statistical markers */**
```

### Renderer 阶段（LLM 转 Prompt）

将 Schema 翻译为 9 段 Prompt，套用铁律，生成最终生图 Prompt。

## ⚠️ 能力边界（重要：何时不要用本 Skill）

AI 生图模型（gpt-image-2、DALL-E、Midjourney、Stable Diffusion 等）是**模式匹配器**，不是几何引擎。它们能渲染"看起来对"的图，但**无法保证**：

- 平行线真正平行、直角真正是 90°
- 三角形真正全等（边长精确相等）
- 几何关系与公式严格对应
- 公式/文字无拼写错误

### ✅ AI 生图**适合**（推荐用本 Skill）

- 概念示意图、流程图、信息图
- 信号通路、细胞结构（标注准确即可，几何不必精确）
- 机械结构剖视图（视觉清晰即可）
- 海报、封面、教学插图
- 风格化、装饰性、教学性图表

### ❌ AI 生图**不适合**（必须用代码生成或人工绘制）

- **数学严格证明图**（如勾股定理、欧几里得几何证明、向量/矩阵图）
- **坐标图、函数图像**（坐标系、抛物线、正弦曲线等）
- **精确构造图**（如圆的内接多边形、角平分线、相似三角形证明）
- **电路图、化学结构式（精确键长/角度）**——除非是教学示意图
- **数据图（柱状图/折线图/热图）**——必须用 matplotlib/plotly 等代码工具

### 🛠️ 严格几何/数学图的正确做法

使用 [scripts/generate_geometry.py](scripts/generate_geometry.py)（基于 matplotlib），或：
- **matplotlib** + `matplotlib.patches`：精确绘制多边形、角度标记、面积填充
- **TikZ / pgfplots**（LaTeX）：学术论文级数学图
- **GeoGebra**：交互式几何
- **Asymptote**：精确几何编程
- **desmos.com / Wolfram Alpha**：函数图像

**判断原则**：如果图需要"几何正确性"才能传达信息（数学证明、精确数据图、坐标变换）→ 必须用代码生成。如果图只需要"视觉传达"概念（流程、机制、结构）→ 可以用 AI 生图。

## 场景模板系统

24 个模板位于 [references/templates/](references/templates)，按场景编号：

| # | 模板 ID | 场景 |
|---|---|---|
| 01 | signaling-pathway | 信号通路/分子机制图 |
| 02 | experimental-workflow | 实验流程/技术路线图 |
| 03 | cell-structure | 细胞/解剖结构图 |
| 04 | data-infographic | 数据可视化信息图 |
| 05 | academic-poster | 双语学术海报 |
| 06 | concept-infographic | 概念教育信息图 |
| 07 | timeline | 科学史时间线 |
| 08 | comparison-matrix | 对比矩阵 |
| 09 | cross-section | 截面/剖视图 |
| 10 | hub-spoke | 中心辐射图 |
| 11 | hierarchical-tree | 层级树/分类树 |
| 12 | cyclic-flow | 循环流程图 |
| 13 | multi-panel-figure | 多子图组合（Figure 1A-F） |
| 14 | plasmid-map | 质粒图/分子结构图 |
| 15 | machine-mechanism | 机械/工程示意图 |
| 16 | physics-schematic | 物理原理示意图 |
| 17 | chemistry-structure | 化学结构/反应机理 |
| 18 | math-concept | 数学概念可视化 |
| 19 | graphical-abstract | 论文图文摘要 |
| 20 | lab-safety | 实验室安全/操作规范 |
| 21 | educational-poster | 教学海报（K-12/高校） |
| 22 | step-by-step | 步骤说明图 |
| 23 | architecture-diagram | 系统/算法架构图 |
| 24 | bilingual-diagram | 中英双语通用图 |

每模板字段：`id` / `name` / `keywords` / `trigger_phrases` / `prompt_template` / `defaults` / `variants` / `category_tips` / `examples` / `accuracy_tips` / `supports_image_reference`。

## 学科适配

| 学科 | 推荐模板 | 关键提示 |
|---|---|---|
| 生命科学 | 01/03/12/14 | 对照 KEGG/UniProt；磷酸化标记；双层膜结构 |
| 医学 | 03/05/09/19 | 解剖术语拉丁名；MOA 级联；临床标识 |
| 化学 | 14/17 | 反应条件标在箭头上；CPK 配色；IUPAC 命名 |
| 物理 | 09/15/16 | 矢量箭头带单位；右手定则；P-V 图 |
| 工程 | 13/15/23 | 爆炸视图带零件号；ISO 标准；公差标注 |
| 数学/CS | 11/18/23 | LaTeX 排版；算法流程；网络拓扑 |

## Campaign Style Lock（多图任务，**强制**）

整套论文 Figure、系列教学卡、教材插图集必须锁定：

- **固定色板**：2-3 主色 + 1 强调色，全部 hex
- **统一字体**：中文一种 + 英文一种
- **统一箭头/线条**：线宽、颜色、端点一致
- **统一背景**：纯白 `#FFFFFF` 或浅灰 `#F8FAFC`
- **统一标注框**：圆角矩形、半透明白底
- **禁止漂移**：不因新图而改变主色、字体、线宽

## 多子图组合规则

- 标签 A/B/C/D 加粗置于子图左上角
- 子图间风格统一（字体/线宽/配色）
- 共享坐标轴和比例尺
- 统计标记一致（*/**/***对应 p<0.05/0.01/0.001）
- 化合物编号、分子量标记跨子图一致

## 期刊合规与学术诚信（**强制**）

### 允许（概念示意图）

- 信号通路、机制图、流程图、架构图
- 细胞/解剖/化学结构示意
- 教学插图、概念信息图、海报
- 理论模型示意、工作原理图

### 禁止（学术不端）

- **用 AI 生成真实实验数据的统计图**：散点图、柱状图、线图、箱线图
- 虚构蛋白质相互作用、通路分支
- 虚构 Western blot 条带、PCR 凝胶图、显微镜图像（应提供真实图像）
- 虚构认证、评分、销量、评价（电商同理）
- 虚构化学反应机理、电子转移方向

→ 如用户要求，**拒绝并提示使用 GraphPad/Origin/Python matplotlib/seaborn**。

## 直接生图规则

用户明确要求"生图/出图/render/生成"时：

1. 用 `scripts/generate_image.py` 调用 API
2. 命令示例：
   ```bash
   # 从 Prompt 文件生图
   python scripts/generate_image.py --prompt-file ./prompt.txt --size 3:4 --resolution 2k

   # 从 stdin/字符串生图
   python scripts/generate_image.py --prompt "..." --size 16:9 --resolution 2k

   # 参考图生图（图生图）
   python scripts/generate_image.py --prompt "..." --image ./reference.png --size 1:1
   ```
3. 生图前向用户确认：**学科、模板 ID、变体、尺寸、风格**

## QA 自检清单（**强制**）

- [ ] 术语准确性（对照 KEGG/UniProt/IUPAC/ISO 等权威标准）
- [ ] 方向/箭头正确（激活实线、抑制虚线 T 型、磷酸化红圈 P）
- [ ] 比例和层级正确（细胞器大小、树的层级）
- [ ] 颜色符合色盲友好标准（避免纯红绿对比）
- [ ] 中文字笔画准确（放大 200% 核对）
- [ ] 未虚构实验数据/认证/相互作用
- [ ] 多子图编号一致（A/B/C/D）
- [ ] 已应用 STEM Prompt 铁律 10 条
- [ ] 已匹配正确场景模板
- [ ] 多图任务已应用 Campaign Style Lock
- [ ] 已选择合适尺寸和分辨率
- [ ] 已套用学科 `category_tips`

## 常见翻车点与防护

| 翻车 | 防护 |
|---|---|
| 蛋白质名错误 | 强制对照 KEGG/UniProt；用标准基因符号 |
| 箭头方向错误 | Prompt 显式声明 `top-to-bottom` / `left-to-right` |
| 解剖结构虚构 | 标注"不用于临床决策"；用通用示意 |
| 配色刺眼/不专业 | 强制 hex 码；色盲友好；主色不超过 3 个 |
| 中文字乱码/缺笔画 | 指定 SimHei/Microsoft YaHei；放大 200% 核对 |
| 数据图造假 | 强制使用真实数据工具；AI 仅限概念图 |
| 整套图风格漂移 | 强制 Campaign Style Lock |
| 虚构通路分支 | 严格依据参考论文/数据库；标注引用 |
| **化学/反应路径错误** | 反应路径必须从权威教材/文献（如 Clayden《Organic Chemistry》、March's Advanced Organic Chemistry）验证；写 prompt 时 LLM 不要凭直觉拼凑反应；用户需要标注引用来源 |
| **模型把甲主题渲染成乙主题** | Prompt 头部加 "PURE [学科] illustration ONLY. NO [其他学科]. NO [其他图种]."（如 `PURE CHEMISTRY ONLY. NO biology, NO cells.`）|
| **反应/通路跨学科混淆**（如 aspirin 关联到 cell biology） | 显式列出关键化合物全名（acetylsalicylic acid）和使用场景（抗血小板）；在 prompt 末尾重复强调"only molecular structures, no biological context" |
| **结构式/小字渲染模糊** | 异步模式用 `--resolution 4k`；prompt 要求 `bold high-contrast labels at 24pt+` |
| **🚨 AI 生图无法保证数学/几何精确性** | **几何证明图、坐标图、精确构造图必须用 [scripts/generate_geometry.py](scripts/generate_geometry.py) 或 matplotlib/TikZ/GeoGebra 等代码工具生成。AI 生图只能用于"看起来对即可"的概念图。这是 Skill 的最关键限制。** |

## 输出格式（中文）

向用户输出时使用以下结构：

```
**【视觉简报】**

**学科**：生命科学（细胞信号通路）
**模板**：signaling-pathway
**变体**：academic（Nature 期刊风格）
**尺寸/分辨率**：3:4 / 2K
**目标受众**：研究生

**核心元素**：
- 脂双层 + RTK 受体（跨膜）
- RAS-RAF-MEK-ERK 级联
- 核内转录因子激活
- 磷酸化用红圈 P 标记

**配色**：
- 激活 #10b981
- 抑制 #ef4444
- 膜蛋白 #3b82f6

**Prompt**（英文，可直接用于生图）：
[Scientific signaling pathway diagram, ... 完整 Prompt]

**调用方式**（如需生图）：
python scripts/generate_image.py --prompt-file ./prompt.txt --size 3:4 --resolution 2k
```

## 与 ecom-details-image 的关系

本 Skill 复用了 ecom-details-image 的生图脚本（统一 OpenAI/apimart 接口），在电商图场景之外扩展了 24 个 STEM 场景模板，并强制了学术诚信和科学准确性的更高要求。
