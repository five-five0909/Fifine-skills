---
name: ref-classify
description: >
  PISFM 参考文献 A-F 板块自动分类工具。扫描指定目录下的 PDF，
  依次用三种技巧匹配板块（关键词 → 作者年份 → PDF 首页内容），
  对置信度不足的文件发起交互确认，最终移动到 A-F 子目录并输出分类报告。
  触发词：分类文献、整理参考文献、ref-classify、帮我分一下PDF、文献归档。
---

# ref-classify

> 三种匹配技巧依次兜底，置信度不足时问用户，不猜测、不静默移错。

## 触发与输入

用户提供以下任一输入：
- **文件夹路径** → 扫描该目录下所有 `.pdf` 文件（含子目录中的未分类文件）
- 无路径 → 使用默认路径 `plans/PISFM_Enhance/参考文献/`

触发后**立即开始** Step 0，不先问一堆问题。

---

## 板块定义（A-F）

| 子目录 | 主题 | 核心识别信号 |
|--------|------|------------|
| `A-Mamba-SSM/` | Mamba / SSM 架构 | Mamba、Selective State、S4、S5、Hyena、Vision Mamba、S2Mamba |
| `B-Physics-Prior-ML/` | 物理先验 ML | Physics-informed、PINN、DeepXDE、process understanding、Beer-Lambert |
| `C-Transfer-Learning/` | 迁移学习 & 数据增强 | Transfer Learning、C-Mixup、Foundation Model、SpectralEarth、Cross-Domain |
| `D-Soil-Spectral-DL/` | 土壤光谱深度学习 | 1D-CNN soil、LUCAS spectral、Swin Transformer soil、SSL-SoilNet、SpectralFormer |
| `E-Soil-Science-Basics/` | 土壤科学基础 | SOC、SoilGrids、4 per mille、vis-NIR review、soil carbon mapping |
| `F-Traditional-Baseline/` | 传统基线方法 | PLS-regression、Random Forests Breiman、Support-Vector Networks、data mining soil |

---

## Step 0 · 扫描目录

调用脚本列出所有待分类 PDF（根目录下的，不含已在子目录中的）：

```bash
python <repo_root>/skills/ref-classify/scripts/scan_pdfs.py "<目标路径>"
```

输出：文件名列表 + 每个文件的 `already_classified`（是否已在 A-F 子目录中）状态。

若所有 PDF 均已分类，输出 "All files already classified. Nothing to do." 并结束。

---

## Step 1 · 三级匹配（按优先级依次执行）

对每个 PDF 文件名，依次用以下三种技巧尝试匹配板块，**首次命中即停止**：

### 技巧一：文件名关键词正则匹配

对文件名做全小写处理后，按板块关键词列表进行 `re.search` 匹配。

**命中条件**：任一关键词在文件名中匹配成功。  
**置信度**：高（直接输出，无需确认）。

关键词表（精简核心词，避免误匹配）：

| 板块 | 关键词（正则，不区分大小写） |
|------|--------------------------|
| A | `mamba`, `selective state`, `structured state space`, `vision mamba`, `s2mamba`, `hyena hierarchy`, `simplified state space` |
| B | `physics-informed neural`, `physics-informed machine`, `deep learning and process understanding`, `deepxde`, `soil science-informed machine` |
| C | `c-mixup`, `transfer learning for soil spectroscop`, `using soil library hyperspectral`, `spectral(earth\|former.*train)`, `cross-domain few-shot`, `hybrid framework for soil property`, `general purpose spectral found` |
| D | `simultaneous prediction.*vnir`, `convolutional neural network.*soil properties.*ng`, `spectralformer`, `ssl-soilnet`, `predicting soil properties.*australian`, `influence of training sample size`, `regional soil organic carbon.*wavelet`, `using deep learning to predict soil properties.*regional`, `estimation of soil organic carbon.*bai`, `transfer learning to localise.*continental`, `innovative approach.*swin transformer` |
| E | `soil carbon 4 per mille`, `unprotected carbon dominates`, `soilgrids 2\.0`, `visible and near infrared spectroscopy in soil science`, `in-field soil spectroscopy.*review`, `high-resolution forest soil organic carbon.*china`, `small sample size.*time-series soil`, `vis-nir spectroscopy.*meta-analysis` |
| F | `pls-regression.*chemometrics`, `random forests_breiman`, `support-vector networks`, `using data mining.*soil diffuse` |

> **边界案例**：若关键词在多个板块均能匹配（如 "soil spectroscopy transfer" 同时触发 C 和 D），**优先取排序更靠前的板块（A > B > C > D > E > F）**，并在报告中标注"多板块命中，已按优先级选择"。

---

### 技巧二：作者 + 年份联合匹配

若技巧一未命中，从文件名中提取年份（`\d{4}`）和第一作者姓氏（`_`之后、空格或`-`之前的词），查表匹配：

| 作者姓氏 | 年份 | 板块 | 备注 |
|---------|------|------|------|
| Gu | 2024 | A | Mamba |
| Dao | 2024 | A | Mamba2 |
| Zhu | 2024 | A | Vision Mamba |
| Gu | 2022 | A | S4 |
| Poli | 2023 | A | Hyena |
| Smith | 2023 | A | S5 |
| Raissi | 2019 | B | PINNs |
| Karniadakis | 2021 | B | PIML |
| Reichstein | 2019 | B | Nature |
| Willard | 2022 | B | ACM Surv |
| Lu | 2020 | B | DeepXDE |
| Gomez | 2008 | B | — |
| Cuomo | 2022 | B | — |
| Kashinath | 2021 | B | — |
| Minasny | 2024 | B | Soil Science-Informed |
| Yao | 2022 | C | C-Mixup |
| Liu | 2018 | C | Transfer CNN soil |
| Saberioon | 2024 | C | LUCAS deep |
| Hateffard | 2025 | C | — |
| Datta | 2022 | C | — |
| Braham | 2025 | C | SpectralEarth |
| Ayuba | 2025 | C | — |
| Laprade | 2025 | C | — |
| Paeedeh | 2026 | C | — |
| Tsakiridis | 2020 | D | — |
| Hong | 2021 | D | SpectralFormer |
| Zhong | 2021 | D | LUCAS CNN |
| Kakhani | 2024 | D | SSL-SoilNet |
| Meng | 2020 | D | — |
| Jin | 2023 | D | Swin |
| Minasny | 2017 | E | 4 per mille |
| Poggio | 2021 | E | SoilGrids |
| Stenberg | 2010 | E | — |
| Piccini | 2024 | E | — |
| Chen | 2026 | E | Forest SOC |
| Chinilin | 2023 | E | — |
| Wold | 2001 | F | PLSR |
| Breiman | 2001 | F | RF |
| Cortes | 1995 | F | SVM |

> **冲突处理**：同一作者+年份出现在多个板块时（如 Padarian+2019 在 B/C/D 均有文献），**触发技巧三**而不是静默选择。

**置信度**：中（匹配成功且无冲突时直接输出，冲突时进入技巧三）。

---

### 技巧三：PDF 首页内容读取

若技巧一和技巧二均未命中，或技巧二发现冲突，用 `Read` 工具读取 PDF 首页（第 1 页），提取标题行和关键词，再做一次语义判断。

读取后：
- 标题中含有技巧一的核心词 → 直接分类
- 仍无法判断 → **向用户发起单条确认**（见 Step 2）

**置信度**：中~高（依读取内容而定）。

---

## Step 2 · 低置信度交互确认

对技巧三仍无法判断的文件，逐个展示给用户：

```
无法自动判断板块：
  文件：2022_Unknown_Paper_Author et al.pdf
  首页提取：[标题摘录]
  
请选择板块：A / B / C / D / E / F / 跳过
```

用户选择后记录，继续处理下一个。

所有确认完成后进入 Step 3。

---

## Step 3 · 创建子目录 & 移动文件

1. 确认 A-F 子目录存在，不存在则创建
2. 展示**移动预览**（dry-run 格式）：

```
将移动 47 个文件：
  A-Mamba-SSM/   ← 2024_Mamba...pdf, 2023_Hyena...pdf ...（7 篇）
  B-Physics-Prior-ML/ ← 2019_Physics-informed...pdf ...（10 篇）
  ...
  [需用户确认的 N 个文件跳过]
```

3. 询问用户是否确认执行（`AskUserQuestion`：确认移动 / 取消）
4. 用户确认后调用脚本执行：

```bash
python <repo_root>/skills/ref-classify/scripts/do_classify.py "<计划JSON路径>"
```

---

## Step 4 · 输出分类报告

执行完成后，输出 Markdown 表格：

| 板块 | 文件数 | 文件列表（简写） |
|------|--------|----------------|
| A-Mamba-SSM | N | ... |
| ... | | |
| **合计** | **N** | |

并在报告末尾列出：
- **未分类文件**（用户选择"跳过"的）
- **手册中有记录但 PDF 未入库的文献**（对照 `文献精读手册-Q1升级版.md` 检查缺口）

---

## 与 ref-rename 的联动

**ref-rename** 和 **ref-classify** 是同一工作流的两个阶段：

```
下载原始 PDF（任意文件名）
        ↓
   /ref-rename  →  YYYY_Title_Author.pdf（规范命名）
        ↓
  /ref-classify →  A-F 子目录（板块归档）
```

**检测到未规范命名文件时**（文件名不以 4 位年份开头），优先提示用户：

```
⚠️  检测到 N 个文件未按 YYYY_Title_Author 格式命名：
  - xxx.pdf
  - yyy.pdf

建议先运行 /ref-rename 完成重命名，再回来分类。
是否跳过这些文件，仅分类已命名的？（是 / 否，先去重命名）
```

---

## 边界情况

| 情况 | 处理 |
|------|------|
| PDF 密码保护，Read 失败 | 技巧三降级为仅凭文件名问用户 |
| 文件已在 A-F 子目录中 | 自动跳过，不重复移动 |
| 目标子目录已有同名文件 | 提示用户，不覆盖 |
| 文件名不含年份（非规范命名） | 触发上方联动提示，让用户决定是否先跑 ref-rename |

---

## 依赖

- Python 3.8+（无第三方依赖，标准库即可）
- 脚本位置：`skills/ref-classify/scripts/`
- 关联 spec：`.trellis/spec/reference-classification.md`

---

## 方法论来源

- 分类标准：`plans/PISFM_Enhance/文献精读手册-Q1升级版.md`（A-F 板块定义）
- 命名规范：`.trellis/spec/reference-classification.md`
