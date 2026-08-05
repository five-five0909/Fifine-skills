# 组件分类体系（A-T + U）

用于对论文进行多标签分类。每篇论文可同时拥有多个标签。

---

## A-J：模型组件分类

### A — 输入编码类
记录 Patch Embedding、Token 化、位置编码、扫描方式、光谱编码、图结构编码。

**典型关键词**：patch embedding, tokenization, positional encoding, scan order, spectral encoding, graph embedding, input projection

**迁移价值**：高光谱 token 化方式，决定序列长度与信息保留。

---

### B — 局部特征类
记录 CNN、大核卷积、多尺度卷积、局部窗口注意力、局部纹理提取。

**典型关键词**：convolution, large kernel, depthwise, multi-scale, local window, texture, convolutional stem

**迁移价值**：大核卷积可替换 3×3 卷积提升感受野，适合高光谱空间特征。

---

### C — 全局交互类
记录 Attention、Cross-Attention、线性注意力、轴向注意力、锚点注意力。

**典型关键词**：attention, cross-attention, axial attention, anchor attention, global interaction, self-attention

**迁移价值**：跨波段交互建模。

---

### D — 长程建模类
记录 SSM、S4、S5、Mamba、Mamba-2、Hyena、RetNet、RWKV、xLSTM、Graph Mamba。

**典型关键词**：mamba, ssm, state space, s4, s5, hyena, retnet, rwkv, xlstm, long-range, sequence model, selective scan

**迁移价值**：土壤光谱序列建模、长程依赖捕获。

---

### E — 记忆更新类
记录 Gate、Selective Update、Delta Update、衰减、写入、遗忘、读取机制。

**典型关键词**：gating, selective update, delta rule, forgetting, memory write, hidden state update, state transition

**迁移价值**：序列信息过滤，避免无关光谱带干扰。

---

### F — 选择/注意力类
记录通道注意力、空间注意力、时间注意力、光谱注意力、状态门控。

**典型关键词**：channel attention, spatial attention, spectral attention, se-net, squeeze excitation, band attention, feature selection

**迁移价值**：光谱波段重要性建模。

---

### G — 特征融合类
记录 Add、Concat、Gate Fusion、Cross-Attention Fusion、Multi-scale Fusion、Spatial-Spectral Fusion、Knowledge Fusion。

**典型关键词**：fusion, concatenation, multi-scale fusion, spatial spectral fusion, feature merging, hybrid, gate fusion

**迁移价值**：空间-光谱双流融合，是高光谱建模核心。

---

### H — 训练稳定类
记录 Residual、Norm、Initialization、Regularization、Auxiliary Loss、Gradient Clipping。

**典型关键词**：residual, layer norm, rms norm, batch norm, initialization, regularization, auxiliary loss, gradient clipping, dropout

**迁移价值**：小样本训练稳定性。

---

### I — 计算加速类
记录 Flash、Scan、FFT、结构化矩阵、低秩、KV Cache 压缩、量化、剪枝、蒸馏。

**典型关键词**：flash attention, parallel scan, fft, structured matrix, low-rank, quantization, pruning, distillation, efficient, lightweight

**迁移价值**：边缘部署、低显存场景（RTX 5060 Blackwell）。

---

### J — 任务/知识约束类
记录 PINN、SoilML、PDE residual、SCORPAN、光谱先验、土壤知识约束、物理约束。

**典型关键词**：physics-informed, pinn, pde, scorpan, soil science, knowledge constraint, prior knowledge, physical constraint, scientific ml

**迁移价值**：直接用于 SoilML/PINN 方向。

---

## K-T：论文类型分类

### K — 数据与基准类
数据集、benchmark、标注方式、划分协议。

**典型关键词**：dataset, benchmark, annotation, evaluation protocol, data collection, ground truth

---

### L — 评价指标类
Accuracy、F1、mIoU、RMSE、R²、MAE、ECE、不确定性量化指标。

**典型关键词**：accuracy, f1, miou, rmse, r2, mae, ece, calibration, uncertainty quantification

---

### M — 优化算法类
Optimizer、Scheduler、Loss Weighting、Loss Landscape。

**典型关键词**：optimizer, scheduler, loss weighting, learning rate, adam, sgd, loss function, training strategy

---

### N — 学习范式类
自监督、半监督、迁移学习、多任务学习、预训练、微调。

**典型关键词**：self-supervised, semi-supervised, transfer learning, multi-task, pretraining, fine-tuning, contrastive learning, masked autoencoder

---

### O — 可解释性类
SHAP、Attention Map、波段重要性、遮挡测试、特征归因。

**典型关键词**：explainability, interpretability, shap, attention map, band importance, feature attribution, visualization, occlusion

---

### P — 可信学习类
鲁棒性、不确定性、分布外检测、校准、泛化。

**典型关键词**：robustness, uncertainty, ood detection, calibration, generalization, reliability, distribution shift

---

### Q — 部署系统类
量化、剪枝、蒸馏、边缘部署、NPU/GPU 优化。

**典型关键词**：quantization, pruning, knowledge distillation, edge deployment, npu, tflite, onnx, model compression

---

### R — 理论分析类
复杂度、收敛性、表达能力、泛化界、稳定性分析。

**典型关键词**：complexity analysis, convergence, expressivity, generalization bound, stability, theoretical analysis

---

### S — 综述地图类
综述、分类学、回顾、路线图。

**典型关键词**：survey, taxonomy, review, roadmap, overview, literature review

---

### T — 应用任务类
土壤有机碳、遥感、高光谱、天气/气候、医学图像、地球系统科学。

**典型关键词**：soil organic carbon, remote sensing, hyperspectral, weather prediction, climate, medical image, earth observation

---

## U：公式 / 算子 / Loss 横向标签

（可与 A-T 标签叠加，专门标注论文的公式创新）

### U1 — 状态更新公式
h_t 如何由 h_{t-1} 和 x_t 得到。

**示例论文**：SSM、Mamba、xLSTM、DeltaNet

**典型关键词**：state update, recurrent, h_t, hidden state transition, selective state

---

### U2 — 注意力公式
QK^T V 或其线性化、稀疏化、递推化。

**示例论文**：Linear Attention、RetNet、HiLo、Performer

**典型关键词**：attention formula, qkv, linear attention, kernel approximation, softmax attention

---

### U3 — 矩阵参数化公式
A、K、Toeplitz、低秩、DPLR、semiseparable matrix。

**示例论文**：S4、Mamba-2、Hyena

**典型关键词**：structured matrix, dplr, toeplitz, semiseparable, low-rank decomposition, parameterization

---

### U4 — 卷积/滤波公式
长卷积、FFT、implicit filter、frequency filter。

**示例论文**：Hyena、TCN、ModernTCN

**典型关键词**：long convolution, fft convolution, implicit filter, frequency domain, filter bank

---

### U5 — 门控公式
控制信息通过比例的门控机制。

**示例论文**：SENet、GLU、Mamba gate、Spectral gate

**典型关键词**：gating, sigmoid gate, glu, swish, activation gate, multiplicative gate

---

### U6 — 损失函数公式
数据损失 + 物理/土壤/先验约束损失。

**示例论文**：PINN、SoilML、Contrastive Loss

**典型关键词**：pde loss, physics loss, soil constraint loss, contrastive loss, auxiliary loss, combined loss

---

### U7 — 归一化/优化公式
LayerNorm、RMSNorm、AdamW、梯度稳定公式。

**典型关键词**：layer norm, rms norm, group norm, adamw, lion, gradient norm, weight decay

---

### U8 — 采样/权重公式
RAR、Focal Loss、Hard Mining、collocation point weighting。

**典型关键词**：focal loss, hard mining, sampling strategy, collocation points, importance weighting, oversampling
