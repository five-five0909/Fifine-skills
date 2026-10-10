---
name: latex-writing
description: "Use when: 需要用 LaTeX 写作、排版文档（含中文支持、公式、三线表、插图、章节格式）。涵盖常用宏包用法、表格防溢出、图表编号、XeLaTeX 编译与常见错误修复。关键词：LaTeX 排版、中文 LaTeX、XeLaTeX、三线表、数学公式、插图、编译报错。"
argument-hint: "描述需要完成的 LaTeX 排版任务"
---

# LaTeX 写作技能指南

## 编译器选择

中文文档**必须使用 XeLaTeX**（而非 pdflatex），运行两遍确保交叉引用正确：

```bash
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

---

## 常用宏包速查

| 功能 | 宏包 | 关键命令 |
|------|------|----------|
| 中文支持 | `ctex`（`[UTF8, zihao=-4]`） | 自动处理字体、缩进、字号 |
| 英文字体 | `fontspec` | `\setmainfont{Times New Roman}` |
| 页边距 | `geometry` | `[top=2.5cm, bottom=2.5cm, left=2.8cm, right=2.8cm]` |
| 行距 | `setspace` | `\setstretch{1.5}` |
| 图片 | `graphicx` + `float` | `\includegraphics[width=...]{}` + `[H]` 强制定位 |
| 三线表 | `booktabs` | `\toprule \midrule \bottomrule` |
| 数学 | `amsmath` + `amssymb` | `equation`、`align`、`multline` |
| 表头换行 | `makecell` | `\makecell{第一行\\第二行}` |
| 表格自适应宽度 | `adjustbox` | `\begin{adjustbox}{max width=\textwidth}` |
| 横向页面 | `pdflscape` | `\begin{landscape}...\end{landscape}` |
| 图表标题 | `caption` | `\captionsetup{font=small, labelsep=space}` |
| 页眉页脚 | `fancyhdr` | `\fancyhead[C]{...} \fancyfoot[C]{\thepage}` |
| 超链接/书签 | `hyperref` | `[colorlinks=true, linkcolor=black]` |
| 章节格式 | `titlesec` | `\titleformat{\section}[block]{...}` |

---

## 中文排版

```latex
\documentclass[12pt, a4paper]{article}
\usepackage[UTF8, zihao=-4]{ctex}   % 中文支持，正文小四
\usepackage{fontspec}
\setmainfont{Times New Roman}        % 英文/数字 Times New Roman
```

- `ctex` 会自动设置中文字体（宋体正文、黑体标题）和首行缩进 2 字符
- 字号命令：`\zihao{3}`（三号 16pt）、`\zihao{4}`（四号 14pt）、`\zihao{-4}`（小四 12pt）、`\zihao{5}`（五号 10.5pt）
- 中文字体切换：`\heiti`（黑体）、`\songti`（宋体）、`\kaishu`（楷书）

---

## 数学公式

### 行内公式
```latex
质量 $m$，速度 $v$，动能为 $E_k = \frac{1}{2}mv^2$
```

### 带编号行间公式
```latex
\begin{equation}
  E = mc^2  \label{eq:einstein}
\end{equation}
```
引用：`式\eqref{eq:einstein}`

### 多行对齐公式（推荐用于推导）
```latex
\begin{align}
  F &= ma \\
    &= m \frac{\mathrm{d}v}{\mathrm{d}t}
\end{align}
```

### 长公式换行（防止溢出版心）
```latex
\begin{multline}
  \bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i \\
           = \frac{x_1 + x_2 + \cdots + x_n}{n}
\end{multline}
```

### 常用符号速查
| 符号 | 命令 | 符号 | 命令 |
|------|------|------|------|
| $\alpha\beta\gamma$ | `\alpha \beta \gamma` | $\partial$ | `\partial` |
| $\nabla$ | `\nabla` | $\infty$ | `\infty` |
| $\times$ | `\times` | $\cdot$ | `\cdot` |
| $\vec{A}$ | `\vec{A}` | $\hat{e}$ | `\hat{e}` |
| $\overrightarrow{AB}$ | `\overrightarrow{AB}` | $\mathrm{d}$ | `\mathrm{d}` |

---

## 插图

```latex
\usepackage{graphicx}
\usepackage{float}
\graphicspath{{./images/}}   % 图片目录（相对路径）

\begin{figure}[H]            % [H] 强制就地放置，需 float 包
  \centering
  \includegraphics[width=0.8\textwidth]{filename.png}
  \caption{图片标题}
  \label{fig:label}
\end{figure}
```

**图片编号分章**（如"图2-3"）：
```latex
\renewcommand{\thefigure}{\arabic{section}-\arabic{figure}}
\counterwithin{figure}{section}
```

图题在图**下方**，正文引用：`如图~\ref{fig:label}所示`

---

## 表格（三线表）

```latex
\usepackage{booktabs}

\begin{table}[H]
  \caption{表格标题}          % 表题在表上方
  \label{tab:label}
  \centering
  \begin{tabular}{ccc}
    \toprule
    列一 & 列二 & 列三 \\
    \midrule
    数据 & 数据 & 数据 \\
    \bottomrule
  \end{tabular}
\end{table}
```

**表格编号分章**（如"表2-3"）：
```latex
\renewcommand{\thetable}{\arabic{section}-\arabic{table}}
\counterwithin{table}{section}
```

### 表格防溢出（必须主动评估）

A4 纸正文宽约 **15.4 cm**。满足以下任一条件时视为高风险：列数 ≥ 6、表头 ≥ 8 汉字、含长公式+单位、行内字符估算 ≥ 80。

按优先级选用：

| 方案 | 适用场景 | 示例 |
|------|----------|------|
| **a. 缩短表头** | 表头冗长，可用符号代替 | `$\bar{x}$/mm` |
| **b. 表头换行** | 表头中等长度 | `\makecell{测量\\次数}` |
| **c. 整体缩放** | 列数较多，内容难缩短 | `\resizebox{\textwidth}{!}{\begin{tabular}{...}...\end{tabular}}` |
| **d. adjustbox** | 超出页宽才缩，否则原尺寸 | `\begin{adjustbox}{max width=\textwidth}...\end{adjustbox}` |
| **e. 横向页面** | 列数极多（≥ 9）或缩放后字号过小 | `\begin{landscape}...\end{landscape}` |
| **f. 拆分子表** | 行列均多，缩放不可读 | 拆为表 X-1a 和 X-1b |

> `\resizebox` 只能包裹 `tabular` 环境，不能直接包裹 `table` 浮动体。

---

## 章节标题格式（titlesec）

```latex
\usepackage{titlesec}
% 一级标题：黑体四号，居中
\titleformat{\section}[block]
  {\centering\heiti\zihao{4}}{\thesection}{1em}{}
\titlespacing*{\section}{0pt}{24pt}{18pt}
% 二级标题：黑体小四
\titleformat{\subsection}[hang]
  {\heiti\zihao{-4}}{\thesubsection}{1em}{}
\titlespacing*{\subsection}{0pt}{18pt}{6pt}
```

> 不要用 `\ctexset{section={...}}` 语法——部分 TeX Live 版本不支持，改用 `titlesec`。

---

## 页眉页脚

```latex
\usepackage{fancyhdr}
\setlength{\headheight}{15pt}  % 必须在 \usepackage{fancyhdr} 之后
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\small 文档标题}
\fancyfoot[C]{\small\thepage}
```

---

## 交叉引用与超链接

```latex
\usepackage[colorlinks=true, linkcolor=black, citecolor=black,
            urlcolor=blue, bookmarks=true, bookmarksnumbered=true]{hyperref}
```

- 图：`\label{fig:xxx}` → 引用 `图~\ref{fig:xxx}`
- 表：`\label{tab:xxx}` → 引用 `表~\ref{tab:xxx}`
- 公式：`\label{eq:xxx}` → 引用 `式~\eqref{eq:xxx}`
- `hyperref` 必须放在导言区**最后**加载（`fancyhdr` 等之后）

---

## 常见编译错误与修复

| 错误信息 | 原因 | 修复方法 |
|----------|------|----------|
| `\headheight is too small` | fancyhdr 默认高度不足 | 加 `\setlength{\headheight}{15pt}` |
| `The key 'ctex/section' is unknown` | ctexset 语法不兼容当前版本 | 改用 `titlesec` 包 |
| `unicode-math` 或 `leading` 缺失 | 宏包未安装 | 删除该宏包，用 `\setstretch{}` 替代行距 |
| `xdvipdfmx: Unable to open .pdf` | PDF 被其他程序占用 | 关闭 PDF 查看器后重新编译 |
| `Overfull \hbox` | 内容溢出版心 | 针对 `tabular` 用上表方案处理；行间公式用 `multline`/`align` |
| `! Undefined control sequence` | 宏包未引入或命令拼写错误 | 检查导言区宏包，对照文档核查命令 |

**调试流程**：编译失败后读取 `.log` 文件，找所有 `! ` 开头的行，修复后再次运行两遍 `xelatex`。

---

## 参考文献

```latex
% 方式一：手动（适合少量引用）
\begin{thebibliography}{99}
  \bibitem{ref1} 作者. 题名[J]. 期刊名, 年, 卷(期): 起--止页.
\end{thebibliography}

% 方式二：natbib（适合较多引用）
\usepackage[numbers, sort&compress]{natbib}
\bibliographystyle{unsrtnat}
\bibliography{refs}   % refs.bib 文件
```

正文引用：`\cite{ref1}`（上标数字需配合 `\citep` 或 `\citenum`）
