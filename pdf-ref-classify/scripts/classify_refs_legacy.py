#!/usr/bin/env python3
"""
classify_refs.py — PISFM 参考文献 A-F 板块自动分类脚本

用法：
  python .trellis/spec/scripts/classify_refs.py [--dir <refs_dir>] [--dry-run]

默认目录：plans/PISFM_Enhance/参考文献/
对应 spec：.trellis/spec/reference-classification.md
"""

import os
import shutil
import argparse
from pathlib import Path

# ── 板块定义 ──────────────────────────────────────────────────────────────────
PANELS = {
    "A-Mamba-SSM": {
        "description": "Mamba / SSM 架构主线",
        "keywords": [
            "Mamba", "Linear-Time Sequence", "Selective State",
            "Transformers are SSMs", "Structured State Space", "Vision Mamba",
            "S2Mamba", "Spatial-spectral State", "Hyena Hierarchy",
            "Simplified State Space", "S5",
        ],
        "authors_years": [
            ("Gu", "2024"), ("Dao", "2024"), ("Zhu", "2024"),
            ("Wang", "2024", "S2Mamba"), ("Gu", "2022"),
            ("Poli", "2023"), ("Smith", "2023"),
        ],
    },
    "B-Physics-Prior-ML": {
        "description": "物理先验 ML",
        "keywords": [
            "Physics-informed neural networks", "Physics-informed machine learning",
            "Deep learning and process understanding", "DeepXDE",
            "Soil Science-Informed Machine Learning",
            "Integrating Scientific Knowledge",
            "Scientific Machine Learning Through Physics",
            "physics-informed machine learning.*weather",
            "Soil organic carbon prediction by hyperspectral remote sensing.*Gomez",
            "Using deep learning for digital soil mapping",
        ],
        "authors_years": [
            ("Raissi", "2019"), ("Karniadakis", "2021"), ("Minasny", "2024"),
            ("Reichstein", "2019"), ("Willard", "2022"), ("Lu", "2020"),
            ("Gomez", "2008"), ("Cuomo", "2022"), ("Kashinath", "2021"),
            ("Padarian", "2019", "digital soil mapping"),
        ],
    },
    "C-Transfer-Learning": {
        "description": "迁移学习与数据增强",
        "keywords": [
            "C-Mixup", "Improving Generalization in Regression",
            "Transfer Learning for Soil Spectroscopy",
            "Using soil library hyperspectral reflectance",
            "Enhancing soil organic carbon prediction of LUCAS",
            "Predicting Soil Properties Using Spectral Subsets of LUCAS",
            "Soil Moisture, Organic Carbon, and Nitrogen Content Prediction",
            "SpectralEarth", "Hyperspectral Foundation Models at Scale",
            "A Hybrid Framework for Soil Property Estimation",
            "General Purpose Spectral Foundational Model",
            "Cross-Domain Few-Shot Learning.*Mixup",
        ],
        "authors_years": [
            ("Yao", "2022"), ("Liu", "2018", "Transfer Learning"),
            ("Wang", "2022", "soil library"), ("Saberioon", "2024"),
            ("Hateffard", "2025"), ("Datta", "2022"),
            ("Braham", "2025"), ("Ayuba", "2025"),
            ("Laprade", "2025"), ("Paeedeh", "2026"),
        ],
    },
    "D-Soil-Spectral-DL": {
        "description": "土壤光谱深度学习",
        "keywords": [
            "Simultaneous prediction of soil properties from VNIR-SWIR",
            "Convolutional neural network for simultaneous prediction of several soil",
            "SpectralFormer", "Rethinking Hyperspectral Image Classification with Transformers",
            "Soil properties.*prediction and feature extraction from the LUCAS",
            "SSL-SoilNet",
            "Predicting soil properties from the Australian soil visible-near infrared",
            "influence of training sample size on the accuracy of deep learning",
            "Regional soil organic carbon prediction model based on a discrete wavelet",
            "Using deep learning to predict soil properties from regional spectral",
            "Estimation of Soil Organic Carbon Using Vis-NIR Spectral Data.*Bai",
            "Transfer learning to localise a continental soil",
            "Innovative Approach.*Swin Transformer",
        ],
        "authors_years": [
            ("Tsakiridis", "2020"), ("Ng", "2019", "Convolutional"),
            ("Hong", "2021"), ("Zhong", "2021"),
            ("Kakhani", "2024"), ("Viscarra Rossel", "2012"),
            ("Ng", "2020", "training sample"), ("Meng", "2020"),
            ("Padarian", "2019", "regional spectral"),
            ("Bai", "2022"), ("Padarian", "2019", "localise"),
            ("Jin", "2023"),
        ],
    },
    "E-Soil-Science-Basics": {
        "description": "土壤科学基础",
        "keywords": [
            "Soil carbon 4 per mille",
            "Unprotected carbon dominates decadal soil carbon",
            "SoilGrids 2.0",
            "Visible and Near Infrared Spectroscopy in Soil Science",
            "In-field soil spectroscopy in Vis-NIR range.*review",
            "High-Resolution Forest Soil Organic Carbon Dataset for China",
            "small sample size problems in time-series soil organic carbon",
            "Vis-NIR Spectroscopy for Soil Organic Carbon Assessment.*Meta-Analysis",
        ],
        "authors_years": [
            ("Minasny", "2017"), ("Liu", "2025", "Unprotected"),
            ("Poggio", "2021"), ("Stenberg", "2010"),
            ("Piccini", "2024"), ("Chen", "2026"),
            ("Wang", "2025", "small sample"), ("Chinilin", "2023"),
        ],
    },
    "F-Traditional-Baseline": {
        "description": "传统基线方法论文",
        "keywords": [
            "PLS-regression.*basic tool of chemometrics",
            "Random Forests_Breiman",
            "Support-Vector Networks",
            "Using data mining to model and interpret soil diffuse reflectance",
        ],
        "authors_years": [
            ("Wold", "2001"), ("Breiman", "2001"),
            ("Cortes", "1995"), ("Viscarra Rossel", "2010"),
        ],
    },
}


def match_panel(filename: str) -> str | None:
    """根据文件名关键词匹配板块，返回板块目录名或 None。"""
    import re
    name_lower = filename.lower()
    for panel, info in PANELS.items():
        for kw in info["keywords"]:
            if re.search(kw.lower(), name_lower):
                return panel
    return None


def classify(refs_dir: Path, dry_run: bool = False):
    refs_dir = refs_dir.resolve()
    if not refs_dir.exists():
        print(f"[ERROR] 目录不存在：{refs_dir}")
        return

    # 创建子目录
    for panel in PANELS:
        target = refs_dir / panel
        if not target.exists():
            if not dry_run:
                target.mkdir()
            print(f"[MKDIR] {panel}/")

    matched, unmatched = [], []

    for pdf in sorted(refs_dir.glob("*.pdf")):
        panel = match_panel(pdf.name)
        if panel:
            dest = refs_dir / panel / pdf.name
            if not dry_run:
                shutil.move(str(pdf), str(dest))
            print(f"[{'DRY' if dry_run else 'MOVE'}] {pdf.name} → {panel}/")
            matched.append(pdf.name)
        else:
            print(f"[SKIP] 未匹配板块：{pdf.name}")
            unmatched.append(pdf.name)

    print(f"\n✅ 已分类 {len(matched)} 篇，未匹配 {len(unmatched)} 篇")
    if unmatched:
        print("未匹配文件：")
        for f in unmatched:
            print(f"  - {f}")


def main():
    parser = argparse.ArgumentParser(description="PISFM 参考文献 A-F 板块分类")
    parser.add_argument(
        "--dir",
        default="plans/PISFM_Enhance/参考文献",
        help="参考文献根目录（默认：plans/PISFM_Enhance/参考文献）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览，不实际移动文件",
    )
    args = parser.parse_args()
    classify(Path(args.dir), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
