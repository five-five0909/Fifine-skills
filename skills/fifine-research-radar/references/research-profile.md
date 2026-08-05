# 研究画像（Research Profile）

本文件定义每日论文雷达的个人研究方向，用于论文过滤、优先级排序和 Hook 提取。

---

## 核心研究方向

### 1. Mamba / SSM / S4 系列
- Mamba、Mamba-2、S4、S5、Hyena、RetNet、xLSTM、DeltaNet、RWKV
- 选择性状态空间机制（selective state space）
- 长程序列建模、高效递推扫描、结构化矩阵参数化

### 2. Vision Mamba / 视觉状态空间
- Vision Mamba、VMamba、Vim、Visual State Space Model
- 遥感图像 Mamba 应用
- Mamba 在图像分类、语义分割、变化检测中的应用

### 3. 高光谱空间-光谱建模
- 高光谱图像分类（Hyperspectral Image Classification, HIC）
- 空间-光谱联合建模（Spatial-Spectral Modeling）
- 波段注意力、光谱门控、频谱扫描
- 高光谱降维、波段选择、特征融合

### 4. 土壤有机碳 / 土壤有机质预测
- 土壤有机碳（SOC）、土壤有机质（OM）预测
- Vis-NIR/高光谱土壤光谱
- 数字土壤制图（DSM）
- SCORPAN 框架、土壤科学先验知识约束

### 5. SoilML / 科学机器学习
- 科学机器学习（Scientific ML / SciML）
- 知识引导机器学习（Knowledge-Guided ML）
- 土壤知识约束（SoilML）

### 6. 物理信息神经网络（PINN）
- Physics-Informed Neural Networks（PINN）
- PDE residual loss、物理约束损失函数
- 物理引导学习（Physics-Guided Learning）

### 7. 高效注意力 / 模型组件创新
- 线性注意力、稀疏注意力、锚点注意力
- 大核卷积（Large Kernel Convolution）
- 门控模块（GLU、Gated Fusion）
- 特征融合创新（Multi-scale Fusion、Spatial-Spectral Fusion）
- 高效视觉 Backbone

### 8. 遥感智能感知
- 遥感图像语义分割、目标检测、变化检测
- 轻量化遥感模型
- 边缘部署、低显存推理（适配 RTX 5060 Blackwell sm_120）

---

## 迁移目标

每日雷达发现的新组件/公式/Hook 应评估能否迁移到：

| 目标任务 | 评估维度 |
|---------|---------|
| 高光谱 SOC/OM 预测 | 光谱序列建模、土壤先验约束、小样本泛化 |
| 遥感智能感知 | 高效特征提取、多尺度融合、实时部署 |
| 高光谱图像分类/回归 | 空间-光谱联合建模、波段选择 |
| 小样本科学机器学习 | Few-shot、Transfer Learning、预训练迁移 |
| 高效 Mamba/SSM 模型 | 计算效率、内存效率、精度权衡 |
| 边缘部署低显存推理 | 量化、蒸馏、剪枝、NPU/GPU 优化 |

---

## 优先级定义

| 级别 | 含义 |
|------|------|
| **H1** | 可直接影响当前论文或实验，需要精读 |
| **H2** | 有潜力，进入 idea 池，暂存待用 |
| **H3** | 普通参考，只保留标题链接和标签 |

---

## 关键词（用于快速过滤）

```
mamba, ssm, state space, selective scan, s4, s5, mamba-2
vision mamba, vmamba, vim, visual state space
hyperspectral, spectral, band selection, vis-nir
soil organic carbon, soc, soil organic matter, digital soil mapping, scorpan
pinn, physics-informed, pde residual, scientific machine learning
linear attention, efficient attention, large kernel, gated fusion
remote sensing, change detection, semantic segmentation
```
