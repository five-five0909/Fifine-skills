// scripts/rank-papers.mjs
// H1 / H2 / H3 优先级排序器

// H1 核心标签（命中越多越高优先级）
const H1_PRIMARY_TAGS = new Set(['D', 'E', 'J', 'T', 'I']);
const H1_FORMULA_TAGS = new Set(['U1', 'U3', 'U6']);

// H2 次级标签
const H2_TAGS = new Set(['A', 'B', 'C', 'F', 'G', 'N', 'O', 'P', 'Q']);

// H1 Hook 类型（含这些 Hook 的论文更重要）
const HIGH_VALUE_HOOKS = new Set(['方法 Hook', '实验 Hook', '问题 Hook']);

/**
 * 计算论文距今天数
 */
function daysSincePublished(paper) {
  const dateStr = paper.published_date || paper.publication_date || '';
  if (!dateStr) return 999;
  const pub = new Date(dateStr);
  const now = new Date();
  const diff = (now - pub) / (1000 * 60 * 60 * 24);
  return Math.max(0, diff);
}

/**
 * 计算 H1 得分（0-10）
 */
function scoreH1(paper) {
  let score = 0;
  const tags = paper.primary_tags || [];
  const formulaTags = paper.formula_tags || [];
  const hooks = paper.hook_types || [];
  const keywords = paper.matched_keywords || [];

  // 1. 核心标签命中
  const coreTagHits = tags.filter(t => H1_PRIMARY_TAGS.has(t)).length;
  score += Math.min(coreTagHits * 1.5, 4); // 最多 4 分

  // 2. 公式标签命中
  const formulaHits = formulaTags.filter(t => H1_FORMULA_TAGS.has(t)).length;
  score += Math.min(formulaHits, 2); // 最多 2 分

  // 3. 关键词匹配数
  score += Math.min(keywords.length * 0.3, 1.5); // 最多 1.5 分

  // 4. 高价值 Hook
  const highHookHits = hooks.filter(h => HIGH_VALUE_HOOKS.has(h)).length;
  score += Math.min(highHookHits * 0.5, 1.5); // 最多 1.5 分

  // 5. 时效性加分
  const days = daysSincePublished(paper);
  if (days <= 7) score += 1;
  else if (days <= 14) score += 0.5;

  // 6. 开放 PDF 加分
  if (paper.pdf_status === 'open_pdf') score += 0.5;

  // 7. 代码链接加分
  if (paper.code_url) score += 0.5;

  return score;
}

/**
 * 计算 H2 得分
 */
function scoreH2(paper) {
  const tags = paper.primary_tags || [];
  const hooks = paper.hook_types || [];

  let score = 0;
  const secondaryHits = tags.filter(t => H2_TAGS.has(t)).length;
  score += secondaryHits;
  score += hooks.length * 0.3;
  return score;
}

/**
 * 对单篇论文打优先级
 */
function rankPaper(paper) {
  const h1Score = scoreH1(paper);
  const h2Score = scoreH2(paper);
  const tags = paper.primary_tags || [];

  let priority, reason;

  // H1 判据：H1 得分 >= 4 且 核心标签 >= 1 且 关键词 >= 2
  const coreTagHits = tags.filter(t => H1_PRIMARY_TAGS.has(t)).length;
  const keywordCount = (paper.matched_keywords || []).length;

  if (h1Score >= 4 && coreTagHits >= 1 && keywordCount >= 2) {
    priority = 'H1';
    reason = `核心标签 ${tags.filter(t => H1_PRIMARY_TAGS.has(t)).join('/')} 命中，关键词匹配 ${keywordCount} 个，H1 得分 ${h1Score.toFixed(1)}`;
  } else if (h2Score >= 2 || h1Score >= 2) {
    // H2 判据：次级标签命中 or H1 得分偏低但有价值
    priority = 'H2';
    reason = `次级标签或方法迁移价值，H1 得分 ${h1Score.toFixed(1)}，H2 得分 ${h2Score.toFixed(1)}`;
  } else if (tags.length > 0) {
    // H3：有标签但得分低
    priority = 'H3';
    reason = `标签命中 [${tags.join(',')}]，优先级较低`;
  } else {
    priority = 'H3';
    reason = '无相关标签命中，普通参考';
  }

  return { ...paper, priority, reason };
}

/**
 * 批量排序，返回按优先级分组后的结果
 */
export function rankPapers(papers) {
  const ranked = papers.map(rankPaper);

  // 在各优先级内部按 H1 得分降序排列
  ranked.sort((a, b) => {
    const priorityOrder = { H1: 0, H2: 1, H3: 2 };
    const pa = priorityOrder[a.priority] ?? 3;
    const pb = priorityOrder[b.priority] ?? 3;
    if (pa !== pb) return pa - pb;
    return scoreH1(b) - scoreH1(a);
  });

  return ranked;
}

/**
 * 获取分组统计
 */
export function getSummary(ranked) {
  const h1 = ranked.filter(p => p.priority === 'H1');
  const h2 = ranked.filter(p => p.priority === 'H2');
  const h3 = ranked.filter(p => p.priority === 'H3');
  return { total: ranked.length, h1Count: h1.length, h2Count: h2.length, h3Count: h3.length, h1, h2, h3 };
}

// CLI 模式
if (process.argv[1] === new URL(import.meta.url).pathname) {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    try {
      const papers = JSON.parse(input);
      const result = rankPapers(Array.isArray(papers) ? papers : [papers]);
      process.stdout.write(JSON.stringify(result, null, 2));
    } catch (e) {
      console.error('排序失败:', e.message);
      process.exit(1);
    }
  });
}
