// scripts/export-radar-md.mjs
// 生成 Obsidian / Notion 兼容的 Markdown 每日雷达报告

/**
 * 转义 Markdown 表格内的特殊字符
 */
function escMd(str) {
  if (!str) return '—';
  return String(str)
    .replace(/\|/g, '\\|')
    .replace(/\n/g, ' ')
    .replace(/\r/g, '')
    .trim();
}

/**
 * 截断长文本
 */
function truncate(str, maxLen = 80) {
  if (!str) return '—';
  return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

/**
 * 格式化作者
 */
function formatAuthors(authors) {
  if (!authors || authors.length === 0) return '—';
  const list = authors.slice(0, 3).map(a => a.split(' ').pop());
  if (authors.length > 3) list.push('et al.');
  return list.join(', ');
}

/**
 * 渲染标签为 Markdown 内联格式
 */
function renderTagsMd(primaryTags, formulaTags) {
  const tags = [
    ...(primaryTags || []).map(t => `\`${t}\``),
    ...(formulaTags || []).map(t => `\`${t}\``),
  ];
  return tags.join(' ') || '—';
}

/**
 * 渲染 Hook 为简短文本
 */
function renderHooksMd(hookTypes) {
  if (!hookTypes || hookTypes.length === 0) return '—';
  return hookTypes.map(h => h.replace(' Hook', '')).join(' / ');
}

/**
 * 生成 H1 表格
 */
function renderH1Table(h1Papers) {
  if (h1Papers.length === 0) return '_今日无 H1 精读候选_\n';

  const header = '| 论文 | 来源 | 日期 | 标签 | Hook | 为什么重要 | 下一步 |\n|---|---|---|---|---|---|---|';
  const rows = h1Papers.map(p => {
    const titleLink = p.url ? `[${escMd(truncate(p.title, 50))}](${p.url})` : escMd(truncate(p.title, 50));
    const date = p.published_date ? p.published_date.substring(0, 10) : (p.year || '?');
    const tags = renderTagsMd(p.primary_tags, p.formula_tags);
    const hooks = renderHooksMd(p.hook_types);
    const why = escMd(truncate(p.hook_summary || p.reason, 60));
    const next = p.pdf_status === 'open_pdf'
      ? `[PDF](${p.pdf_url || p.url})` + (p.code_url ? ` / [Code](${p.code_url})` : '')
      : (p.code_url ? `[Code](${p.code_url})` : '手动下载');

    return `| ${titleLink} | ${escMd(p.source)} | ${date} | ${tags} | ${hooks} | ${why} | ${next} |`;
  });

  return [header, ...rows].join('\n') + '\n';
}

/**
 * 生成 H2 表格
 */
function renderH2Table(h2Papers) {
  if (h2Papers.length === 0) return '_今日无 H2 候选_\n';

  const header = '| 论文 | 标签 | Hook | 可迁移 Idea | 暂存理由 |\n|---|---|---|---|---|';
  const rows = h2Papers.map(p => {
    const titleLink = p.url ? `[${escMd(truncate(p.title, 45))}](${p.url})` : escMd(truncate(p.title, 45));
    const tags = renderTagsMd(p.primary_tags, p.formula_tags);
    const hooks = renderHooksMd(p.hook_types);
    const idea = escMd(truncate(p.possible_idea, 60));
    const reason = escMd(truncate(p.reason, 50));
    return `| ${titleLink} | ${tags} | ${hooks} | ${idea} | ${reason} |`;
  });

  return [header, ...rows].join('\n') + '\n';
}

/**
 * 生成 H3 列表
 */
function renderH3List(h3Papers) {
  if (h3Papers.length === 0) return '_今日无 H3 参考_\n';

  return h3Papers.map(p => {
    const link = p.url ? `[${escMd(truncate(p.title, 60))}](${p.url})` : escMd(truncate(p.title, 60));
    const tags = (p.primary_tags || []).map(t => `\`${t}\``).join(' ');
    return `- ${link} ${tags} _${p.source || ''} · ${p.year || ''}_`;
  }).join('\n') + '\n';
}

/**
 * 生成今日新增组件表
 */
function renderComponentTableMd(h1Papers, h2Papers) {
  const allPapers = [...h1Papers, ...h2Papers].filter(p =>
    p.primary_tags && p.primary_tags.some(t => /^[A-J]$/.test(t))
  );

  if (allPapers.length === 0) return '_今日无新增组件记录_\n';

  const header = '| 标签 | 来源论文 | 优先级 | 可迁移方向 |\n|---|---|---|---|';
  const rows = allPapers.slice(0, 10).map(p => {
    const componentTags = (p.primary_tags || []).filter(t => /^[A-J]$/.test(t)).map(t => `\`${t}\``).join(' ');
    const formulaTags = (p.formula_tags || []).map(t => `\`${t}\``).join(' ');
    const titleLink = p.url ? `[${escMd(truncate(p.title, 40))}](${p.url})` : escMd(truncate(p.title, 40));
    const positions = escMd((p.writing_position || []).slice(0, 2).join(' / '));
    return `| ${componentTags} ${formulaTags} | ${titleLink} | **${p.priority}** | ${positions} |`;
  });

  return [header, ...rows].join('\n') + '\n';
}

/**
 * 生成今日建议动作
 */
function renderActionsMd(h1Papers, h2Papers) {
  const actions = [];

  if (h1Papers.length > 0) {
    actions.push(`- **精读**：${h1Papers.slice(0, 3).map(p => `《${truncate(p.title, 30)}》`).join('、')}`);
  }

  const openPdfs = h1Papers.filter(p => p.pdf_status === 'open_pdf' && p.pdf_url);
  if (openPdfs.length > 0) {
    actions.push(`- **下载开放 PDF**：${openPdfs.slice(0, 3).map(p => p.pdf_url || p.url).join(' / ')}`);
  }

  const methodHooks = [...h1Papers, ...h2Papers].filter(p => (p.hook_types || []).includes('方法 Hook'));
  if (methodHooks.length > 0) {
    actions.push(`- **方法迁移**：关注 ${[...new Set(methodHooks.map(p => p.query_pack).filter(Boolean))].slice(0, 3).join('、')} 方向`);
  }

  const counterHooks = [...h1Papers, ...h2Papers].filter(p => (p.hook_types || []).includes('反例 Hook'));
  if (counterHooks.length > 0) {
    actions.push(`- **防御基线**：${counterHooks.slice(0, 2).map(p => truncate(p.title, 30)).join('、')} 需要纳入对比`);
  }

  if (h2Papers.length > 0) {
    actions.push(`- **Idea 池**：${h2Papers.length} 篇 H2 论文，建议本周读摘要`);
  }

  if (actions.length === 0) actions.push('- 今日无特别建议动作');

  return actions.join('\n') + '\n';
}

/**
 * 生成完整 Markdown 报告
 */
export function generateMarkdownReport(reportData) {
  const { date, packs = [], total_candidates = 0, total_deduped = 0, h1 = [], h2 = [], h3 = [] } = reportData;

  const topDirections = [...new Set([...h1, ...h2].flatMap(p => p.primary_tags || []))].slice(0, 5).join(', ') || '暂无';
  const openPdfCount = [...h1, ...h2].filter(p => p.pdf_status === 'open_pdf').length;

  return `# 每日论文组件雷达｜${date}

## 今日总览

| 指标 | 数值 |
|---|---|
| 检索方向 | ${escMd(packs.join(' / '))} |
| 候选论文 | ${total_candidates} 篇 |
| 去重后 | ${total_deduped} 篇 |
| **H1 精读候选** | **${h1.length} 篇** |
| **H2 Idea 池** | **${h2.length} 篇** |
| H3 普通参考 | ${h3.length} 篇 |
| 开放 PDF 可下载 | ${openPdfCount} 篇 |
| 今日最强方向 | ${escMd(topDirections)} |

---

## H1 精读候选

${renderH1Table(h1)}

---

## H2 Idea 池

${renderH2Table(h2)}

---

## H3 普通参考

${renderH3List(h3)}

---

## 今日新增组件

${renderComponentTableMd(h1, h2)}

---

## 今日建议动作

${renderActionsMd(h1, h2)}

---

_由 Academic Component Hook Radar 自动生成 · ${date}_
`;
}

// CLI 模式
if (process.argv[1] === new URL(import.meta.url).pathname) {
  import('node:fs').then(({ readFileSync, writeFileSync, mkdirSync }) => {
    const args = process.argv.slice(2);
    const inputFile = args[0] || null;
    const outputFile = args[1] || null;

    if (inputFile) {
      const data = JSON.parse(readFileSync(inputFile, 'utf8'));
      const md = generateMarkdownReport(data);
      if (outputFile) {
        mkdirSync(outputFile.replace(/[^/\\]*$/, ''), { recursive: true });
        writeFileSync(outputFile, md, 'utf8');
        console.log(`Markdown 报告已写入: ${outputFile}`);
      } else {
        process.stdout.write(md);
      }
    } else {
      const chunks = [];
      process.stdin.setEncoding('utf8');
      process.stdin.on('data', c => chunks.push(c));
      process.stdin.on('end', () => {
        const data = JSON.parse(chunks.join(''));
        const md = generateMarkdownReport(data);
        if (outputFile) {
          mkdirSync(outputFile.replace(/[^/\\]*$/, ''), { recursive: true });
          writeFileSync(outputFile, md, 'utf8');
          console.log(`Markdown 报告已写入: ${outputFile}`);
        } else {
          process.stdout.write(md);
        }
      });
    }
  });
}
