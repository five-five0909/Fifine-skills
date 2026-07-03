// scripts/extract-hooks.mjs
// 规则驱动的 8 类 Hook 提取器

// Hook 类型常量
const HOOK_TYPES = {
  PROBLEM: '问题 Hook',
  METHOD: '方法 Hook',
  VARIABLE: '变量 Hook',
  EXPERIMENT: '实验 Hook',
  EXPLANATION: '解释 Hook',
  COUNTER: '反例 Hook',
  FAILURE: '失败 Hook',
  WRITING: '写作 Hook'
};

// 写作位置常量
const WRITING_POS = {
  INTRO: 'Introduction',
  RELATED: 'Related Work',
  METHOD: 'Method',
  EXPERIMENT: 'Experiments',
  ABLATION: 'Ablation Study',
  DISCUSSION: 'Discussion',
  LIMITATION: 'Limitation',
  FUTURE: 'Future Work'
};

/**
 * 判断标题/摘要是否含指定关键词（不区分大小写）
 */
function contains(text, ...keywords) {
  const lower = text.toLowerCase();
  return keywords.some(kw => lower.includes(kw.toLowerCase()));
}

/**
 * 对单篇论文提取 Hook
 */
function extractHooks(paper) {
  const text = `${paper.title || ''} ${paper.abstract || ''}`;
  const tags = paper.primary_tags || [];
  const formulaTags = paper.formula_tags || [];
  const allTags = [...tags, ...formulaTags];

  const hookTypes = new Set();
  const writingPositions = new Set();
  let hookSummary = '';
  let possibleIdea = '';
  let possibleExperiment = '';
  let riskNote = '';

  // --- 规则 1：长程建模 / Mamba / SSM → 方法 Hook + 解释 Hook + 实验 Hook
  if (tags.some(t => ['D', 'E', 'I'].includes(t)) ||
      contains(text, 'mamba', 'ssm', 'state space', 'selective scan', 's4', 's5',
               'retnet', 'rwkv', 'xlstm', 'hyena', 'deltanet')) {
    hookTypes.add(HOOK_TYPES.METHOD);
    hookTypes.add(HOOK_TYPES.EXPLANATION);
    hookTypes.add(HOOK_TYPES.EXPERIMENT);
    writingPositions.add(WRITING_POS.METHOD);
    writingPositions.add(WRITING_POS.RELATED);
    writingPositions.add(WRITING_POS.EXPERIMENT);
    hookSummary += '提出新的状态空间/长程建模组件，可迁移到高光谱序列建模或土壤光谱预测。';
    possibleIdea += '将该组件替换现有 Transformer 编码器，对比 Mamba vs Attention 在光谱序列上的效果。';
    possibleExperiment += '消融实验：替换 SSM 扫描方式（单向/双向/全向），对比 RMSE 和 R²。';
  }

  // --- 规则 2：物理约束 / PINN / SoilML → 方法 Hook + 写作 Hook + 解释 Hook
  if (tags.some(t => ['J', 'M'].includes(t)) ||
      formulaTags.includes('U6') ||
      contains(text, 'physics-informed', 'pinn', 'pde', 'scorpan',
               'soil science', 'knowledge constraint', 'physics-guided')) {
    hookTypes.add(HOOK_TYPES.METHOD);
    hookTypes.add(HOOK_TYPES.WRITING);
    hookTypes.add(HOOK_TYPES.EXPLANATION);
    writingPositions.add(WRITING_POS.METHOD);
    writingPositions.add(WRITING_POS.RELATED);
    writingPositions.add(WRITING_POS.DISCUSSION);
    hookSummary += (hookSummary ? ' ' : '') + '引入物理/知识约束损失，可迁移到 SoilML/PINN 方向。';
    possibleIdea += (possibleIdea ? ' ' : '') + '在土壤 SOC 预测中引入 SCORPAN 因素作为约束项，与纯数据驱动方法对比。';
    possibleExperiment += (possibleExperiment ? ' ' : '') + '实验：物理约束权重 λ 的敏感性分析。';
  }

  // --- 规则 3：可解释性 / 可信学习 → 实验 Hook + 解释 Hook + 失败 Hook
  if (tags.some(t => ['O', 'P'].includes(t)) ||
      contains(text, 'explainability', 'interpretability', 'uncertainty',
               'robustness', 'ood', 'calibration', 'shap', 'attention map')) {
    hookTypes.add(HOOK_TYPES.EXPERIMENT);
    hookTypes.add(HOOK_TYPES.EXPLANATION);
    hookTypes.add(HOOK_TYPES.FAILURE);
    writingPositions.add(WRITING_POS.EXPERIMENT);
    writingPositions.add(WRITING_POS.DISCUSSION);
    writingPositions.add(WRITING_POS.LIMITATION);
    possibleExperiment += (possibleExperiment ? ' ' : '') + '可视化波段重要性热图，分析模型预测的光谱依据。';
    riskNote += '注意：该论文的可信性指标需要在分布外数据集上验证。';
  }

  // --- 规则 4：高光谱 / 光谱建模 → 方法 Hook + 实验 Hook
  if (tags.some(t => ['A', 'F', 'G'].includes(t)) ||
      contains(text, 'hyperspectral', 'spectral', 'band selection', 'vis-nir',
               'spatial-spectral', 'spectral attention')) {
    hookTypes.add(HOOK_TYPES.METHOD);
    hookTypes.add(HOOK_TYPES.EXPERIMENT);
    writingPositions.add(WRITING_POS.METHOD);
    writingPositions.add(WRITING_POS.EXPERIMENT);
    possibleIdea += (possibleIdea ? ' ' : '') + '将光谱注意力机制应用于 Vis-NIR 土壤光谱，提升 SOC 波段权重学习。';
  }

  // --- 规则 5：综述 → 写作 Hook
  if (tags.includes('S') ||
      contains(text, 'survey', 'review', 'taxonomy', 'roadmap', 'overview')) {
    hookTypes.add(HOOK_TYPES.WRITING);
    writingPositions.add(WRITING_POS.RELATED);
    writingPositions.add(WRITING_POS.INTRO);
    hookSummary += (hookSummary ? ' ' : '') + '综述类论文，可作为 Related Work 组织框架和分类依据。';
  }

  // --- 规则 6：Foundation model / 预训练 → 反例 Hook
  if (tags.includes('N') ||
      contains(text, 'foundation model', 'pretrained', 'zero-shot',
               'universal', 'large-scale pretraining', 'vision language')) {
    hookTypes.add(HOOK_TYPES.COUNTER);
    writingPositions.add(WRITING_POS.EXPERIMENT);
    writingPositions.add(WRITING_POS.LIMITATION);
    riskNote += (riskNote ? ' ' : '') + '注意：该论文可能成为强 Baseline，需要在对比实验中纳入。';
    possibleExperiment += (possibleExperiment ? ' ' : '') + '防御实验：将该预训练模型作为竞争基线，对比资源消耗与精度。';
  }

  // --- 规则 7：变量/超参数/自适应 → 变量 Hook
  if (contains(text, 'learnable', 'adaptive', 'dynamic', 'data-driven parameter',
               'hyperparameter search', 'neural architecture search')) {
    hookTypes.add(HOOK_TYPES.VARIABLE);
    writingPositions.add(WRITING_POS.METHOD);
    writingPositions.add(WRITING_POS.ABLATION);
    possibleIdea += (possibleIdea ? ' ' : '') + '将固定超参数（如扫描窗口大小）替换为可学习变量。';
  }

  // --- 规则 8：效率 / 计算加速 → 实验 Hook + 变量 Hook
  if (tags.includes('I') || tags.includes('Q') ||
      contains(text, 'efficient', 'lightweight', 'fast', 'low-latency',
               'edge deployment', 'model compression', 'inference speed')) {
    hookTypes.add(HOOK_TYPES.EXPERIMENT);
    writingPositions.add(WRITING_POS.EXPERIMENT);
    possibleExperiment += (possibleExperiment ? ' ' : '') + '效率对比：FLOPs、参数量、推理时间（RTX 5060 上测量）。';
  }

  // --- 规则 9：问题 Hook（通用，几乎所有相关论文都有）
  if (hookTypes.size > 0) {
    hookTypes.add(HOOK_TYPES.PROBLEM);
    hookTypes.add(HOOK_TYPES.WRITING);
    writingPositions.add(WRITING_POS.INTRO);
    writingPositions.add(WRITING_POS.RELATED);
  }

  return {
    ...paper,
    hook_types: [...hookTypes],
    hook_summary: hookSummary || '暂无 Hook 摘要（关键词匹配度低）',
    possible_idea: possibleIdea || '',
    possible_experiment: possibleExperiment || '',
    writing_position: [...writingPositions],
    risk_note: riskNote || ''
  };
}

/**
 * 批量提取 Hook
 */
export function extractHooksFromPapers(papers) {
  return papers.map(extractHooks);
}

// CLI 模式
if (process.argv[1] === new URL(import.meta.url).pathname) {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    try {
      const papers = JSON.parse(input);
      const result = extractHooksFromPapers(Array.isArray(papers) ? papers : [papers]);
      process.stdout.write(JSON.stringify(result, null, 2));
    } catch (e) {
      console.error('Hook提取失败:', e.message);
      process.exit(1);
    }
  });
}
