---
name: lab-report-writing
description: Use when writing a Chinese physics, optics, or electronics lab report from local experiment materials, generating a XeLaTeX source file, extracting data from images, inserting figures, answering thinking questions, and compiling a GB/T 7713.1 style PDF.
---

# Lab Report Writing

Use this skill for full experiment reports.

## Required Inputs

- Experiment name.
- Work directory. All reading and writing for the report must stay inside this directory.

## Workflow

1. Explore only the work directory and list relevant files.
2. Locate the experiment manual or handout: `.pdf`, `.md`, `.docx`, `.txt`, or similar files with names like `讲义`, `实验`, `指导`, `手册`, `说明`.
3. Collect image resources from common folders: `image`, `images`, `pictures`, `图片`, `figures`, `data`, `photo`.
4. Read the manual fully before writing. If the manual cannot be read directly, convert or ask before continuing.
5. Inspect images that contain data, apparatus, optical paths, waveforms, signatures, or phenomena.
6. Classify images:
   - Data screenshots without signature: extract to LaTeX tables, do not insert as images.
   - Signed raw data records: extract tables and also attach original image in appendix.
   - Apparatus/path/result figures: insert as numbered figures.
7. Create a XeLaTeX report in the work directory.
8. Compile twice with `xelatex -interaction=nonstopmode`.
9. If compile fails, read the `.log`, fix `! ` errors, and retry up to 3 rounds.

## Required Sections

Include these unless the manual clearly requires a better structure:

- 实验目的
- 实验原理
- 实验仪器
- 实验步骤
- 实验数据与处理
- 实验结果与分析
- 误差分析
- 实验结论
- 思考题, only if the handout contains thinking/discussion questions
- 原始数据记录 appendix, only if signed raw data images exist

## Typesetting Rules

- Use XeLaTeX, `ctex`, Times New Roman for English/numbers, 1.5 line spacing.
- Use three-line tables with `booktabs`.
- Number figures/tables by section, such as `图2-3` and `表2-3`.
- Check wide tables proactively. Use shorter headers, `makecell`, `adjustbox`, `resizebox`, landscape pages, or split tables as needed.
- Insert figures with relative paths from the `.tex` file.
- Add references only if the handout explicitly includes or requires them.
