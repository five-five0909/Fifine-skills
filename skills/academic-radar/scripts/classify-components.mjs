// scripts/classify-components.mjs
// 规则驱动的 A-T + U 组件分类器

// ============================================================
// 分类规则：关键词 → 标签映射
// ============================================================
const CLASSIFICATION_RULES = [
  // A — 输入编码类
  {
    tags: ['A'],
    formulaTags: [],
    keywords: ['patch embedding', 'tokenization', 'positional encoding', 'scan order',
      'spectral encoding', 'input projection', 'token embedding', 'image tokenizer',
      'patch partition', 'overlapping patch']
  },
  // B — 局部特征类
  {
    tags: ['B'],
    formulaTags: [],
    keywords: ['large kernel', 'depthwise convolution', 'multi-scale convolution',
      'local window', 'convolutional stem', 'convnext', 'repvgg',
      'dilated convolution', 'deformable convolution']
  },
  // C — 全局交互类
  {
    tags: ['C'],
    formulaTags: ['U2'],
    keywords: ['cross-attention', 'axial attention', 'anchor attention',
      'global attention', 'non-local', 'global context', 'self-attention']
  },
  // D — 长程建模类
  {
    tags: ['D'],
    formulaTags: ['U1', 'U3'],
    keywords: ['mamba', 'mamba-2', 'state space model', 'ssm', 's4', 's5',
      'selective state space', 'selective scan', 'structured state space',
      'hyena', 'retnet', 'rwkv', 'xlstm', 'long-range', 'long range',
      'deltanet', 'linear rnn', 'state space duality', 'semiseparable']
  },
  // E — 记忆更新类
  {
    tags: ['E'],
    formulaTags: ['U1', 'U5'],
    keywords: ['selective update', 'delta rule', 'forgetting mechanism',
      'hidden state update', 'state transition', 'memory write',
      'gated recurrent', 'memory gate']
  },
  // F — 选择/注意力类
  {
    tags: ['F'],
    formulaTags: ['U5'],
    keywords: ['channel attention', 'spatial attention', 'spectral attention',
      'se-net', 'squeeze excitation', 'cbam', 'band attention',
      'feature selection', 'feature recalibration', 'adaptive feature']
  },
  // G — 特征融合类
  {
    tags: ['G'],
    formulaTags: [],
    keywords: ['feature fusion', 'spatial-spectral fusion', 'multi-scale fusion',
      'gate fusion', 'cross-attention fusion', 'feature merging',
      'hybrid architecture', 'dual stream', 'dual branch']
  },
  // H — 训练稳定类
  {
    tags: ['H'],
    formulaTags: ['U7'],
    keywords: ['layer norm', 'rms norm', 'batch norm', 'residual connection',
      'auxiliary loss', 'gradient clipping', 'initialization',
      'regularization', 'dropout', 'weight decay']
  },
  // I — 计算加速类
  {
    tags: ['I'],
    formulaTags: ['U4'],
    keywords: ['flash attention', 'parallel scan', 'fft', 'structured matrix',
      'low-rank', 'quantization', 'pruning', 'knowledge distillation',
      'efficient', 'lightweight', 'hardware-aware', 'cuda kernel']
  },
  // J — 任务/知识约束类
  {
    tags: ['J'],
    formulaTags: ['U6'],
    keywords: ['physics-informed', 'pinn', 'pde', 'scorpan', 'soil science',
      'knowledge constraint', 'physical constraint', 'scientific machine learning',
      'physics-guided', 'prior knowledge', 'domain knowledge', 'knowledge-guided']
  },
  // K — 数据与基准类
  {
    tags: ['K'],
    formulaTags: [],
    keywords: ['dataset', 'benchmark', 'annotation', 'evaluation protocol',
      'data collection', 'ground truth label', 'training split']
  },
  // L — 评价指标类
  {
    tags: ['L'],
    formulaTags: [],
    keywords: ['accuracy', 'f1 score', 'miou', 'rmse', 'r2 score', 'mae',
      'ece', 'calibration error', 'uncertainty quantification', 'rpd']
  },
  // M — 优化算法类
  {
    tags: ['M'],
    formulaTags: ['U7'],
    keywords: ['optimizer', 'learning rate schedule', 'loss weighting',
      'loss landscape', 'adamw', 'lion optimizer', 'cosine annealing',
      'warmup', 'gradient accumulation']
  },
  // N — 学习范式类
  {
    tags: ['N'],
    formulaTags: [],
    keywords: ['self-supervised', 'semi-supervised', 'transfer learning',
      'multi-task learning', 'pretraining', 'fine-tuning',
      'contrastive learning', 'masked autoencoder', 'foundation model',
      'few-shot', 'zero-shot', 'meta-learning']
  },
  // O — 可解释性类
  {
    tags: ['O'],
    formulaTags: [],
    keywords: ['explainability', 'interpretability', 'shap', 'attention map',
      'band importance', 'feature attribution', 'visualization',
      'occlusion test', 'grad-cam', 'saliency']
  },
  // P — 可信学习类
  {
    tags: ['P'],
    formulaTags: [],
    keywords: ['robustness', 'uncertainty estimation', 'ood detection',
      'out-of-distribution', 'calibration', 'generalization',
      'distribution shift', 'adversarial', 'reliability']
  },
  // Q — 部署系统类
  {
    tags: ['Q'],
    formulaTags: [],
    keywords: ['model compression', 'edge deployment', 'tflite', 'onnx',
      'npu', 'int8', 'quantization-aware', 'hardware deployment',
      'inference acceleration', 'tensorrt']
  },
  // R — 理论分析类
  {
    tags: ['R'],
    formulaTags: [],
    keywords: ['complexity analysis', 'convergence proof', 'expressivity',
      'generalization bound', 'theoretical analysis', 'stability analysis',
      'approximation theory']
  },
  // S — 综述地图类
  {
    tags: ['S'],
    formulaTags: [],
    keywords: ['survey', 'taxonomy', 'review', 'roadmap', 'overview',
      'literature review', 'systematic review', 'meta-analysis']
  },
  // T — 应用任务类
  {
    tags: ['T'],
    formulaTags: [],
    keywords: ['soil organic carbon', 'soil organic matter', 'soc prediction',
      'remote sensing', 'hyperspectral', 'change detection',
      'semantic segmentation', 'object detection', 'weather prediction',
      'climate model', 'medical image', 'earth observation',
      'digital soil mapping', 'land cover']
  },
  // U 标签额外补充规则
  // U1 — 状态更新公式
  {
    tags: [],
    formulaTags: ['U1'],
    keywords: ['hidden state', 'recurrent update', 'h_t', 'state transition formula',
      'selective update rule', 'delta update']
  },
  // U2 — 注意力公式
  {
    tags: [],
    formulaTags: ['U2'],
    keywords: ['linear attention', 'kernel attention', 'performer', 'softmax approximation',
      'attention approximation', 'efficient attention mechanism']
  },
  // U3 — 矩阵参数化
  {
    tags: [],
    formulaTags: ['U3'],
    keywords: ['dplr', 'toeplitz matrix', 'semiseparable matrix',
      'hippo', 'diagonalization', 'structured matrix parameterization']
  },
  // U4 — 卷积/滤波
  {
    tags: [],
    formulaTags: ['U4'],
    keywords: ['long convolution', 'implicit filter', 'frequency filter',
      'fft convolution', 'spectral convolution', 'continuous convolution']
  },
  // U5 — 门控公式
  {
    tags: [],
    formulaTags: ['U5'],
    keywords: ['glu', 'swish gate', 'sigmoid gate', 'gated linear unit',
      'multiplicative gate', 'input gate', 'output gate']
  },
  // U6 — 损失函数
  {
    tags: [],
    formulaTags: ['U6'],
    keywords: ['pde loss', 'physics loss', 'residual loss', 'constraint loss',
      'auxiliary loss term', 'combined loss', 'multi-objective loss',
      'focal loss', 'contrastive loss']
  },
  // U7 — 归一化/优化
  {
    tags: [],
    formulaTags: ['U7'],
    keywords: ['rmsnorm', 'layernorm', 'pre-norm', 'post-norm',
      'gradient norm', 'weight norm', 'spectral normalization']
  },
  // U8 — 采样/权重
  {
    tags: [],
    formulaTags: ['U8'],
    keywords: ['focal loss', 'hard negative mining', 'importance sampling',
      'collocation points', 'oversampling', 'class imbalance',
      'curriculum learning', 'self-paced learning']
  }
];

/**
 * 对单篇论文进行分类
 * @param {Object} paper - 论文 JSON 对象（含 title 和 abstract）
 * @returns {Object} 补全了 primary_tags、formula_tags、matched_keywords 的论文对象
 */
function classifyPaper(paper) {
  const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase();

  const primaryTagsSet = new Set(paper.primary_tags || []);
  const formulaTagsSet = new Set(paper.formula_tags || []);
  const matchedKeywords = new Set(paper.matched_keywords || []);

  for (const rule of CLASSIFICATION_RULES) {
    for (const kw of rule.keywords) {
      if (text.includes(kw.toLowerCase())) {
        matchedKeywords.add(kw);
        rule.tags.forEach(t => primaryTagsSet.add(t));
        rule.formulaTags.forEach(t => formulaTagsSet.add(t));
      }
    }
  }

  return {
    ...paper,
    primary_tags: [...primaryTagsSet].sort(),
    formula_tags: [...formulaTagsSet].sort(),
    matched_keywords: [...matchedKeywords]
  };
}

/**
 * 批量分类论文
 * @param {Object[]} papers
 * @returns {Object[]}
 */
export function classifyPapers(papers) {
  return papers.map(classifyPaper);
}

// CLI 模式：支持从 stdin 读取 JSON
if (process.argv[1] === new URL(import.meta.url).pathname) {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    try {
      const papers = JSON.parse(input);
      const result = classifyPapers(Array.isArray(papers) ? papers : [papers]);
      process.stdout.write(JSON.stringify(result, null, 2));
    } catch (e) {
      console.error('分类失败:', e.message);
      process.exit(1);
    }
  });
}
