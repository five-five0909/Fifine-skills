// scripts/export-radar-html.mjs
// 生成 Notion 风格的每日论文雷达 HTML 报告

/**
 * 生成标签 pill HTML
 */
function renderTagPills(primaryTags, formulaTags, hookTypes) {
  const pills = [];

  // A-T 标签（蓝色系）
  for (const tag of (primaryTags || [])) {
    pills.push(`<span class="pill pill-tag">${tag}</span>`);
  }

  // U 标签（紫色系）
  for (const tag of (formulaTags || [])) {
    pills.push(`<span class="pill pill-formula">${tag}</span>`);
  }

  // Hook 标签（绿色系，只显示前2个）
  for (const hook of (hookTypes || []).slice(0, 2)) {
    const short = hook.replace(' Hook', '');
    pills.push(`<span class="pill pill-hook">${short}</span>`);
  }

  return pills.join('');
}

/**
 * 生成 PDF 状态徽章
 */
function renderPdfBadge(paper) {
  if (paper.pdf_status === 'open_pdf' && paper.pdf_url) {
    return `<a href="${escHtml(paper.pdf_url)}" class="badge badge-open" target="_blank" rel="noopener">PDF ↗</a>`;
  }
  if (paper.code_url) {
    return `<a href="${escHtml(paper.code_url)}" class="badge badge-code" target="_blank" rel="noopener">Code ↗</a>`;
  }
  if (paper.pdf_status === 'needs_institution') {
    return `<span class="badge badge-paywall">需机构</span>`;
  }
  return '';
}

/**
 * HTML 转义
 */
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * 格式化作者（最多显示 3 个）
 */
function formatAuthors(authors) {
  if (!authors || authors.length === 0) return '—';
  const list = authors.slice(0, 3).map(a => a.split(' ').pop()); // 取姓
  if (authors.length > 3) list.push('et al.');
  return escHtml(list.join(', '));
}

/**
 * 生成 H1 论文表格行
 */
function renderH1Row(paper, index) {
  const titleLink = paper.url
    ? `<a href="${escHtml(paper.url)}" target="_blank" rel="noopener" class="paper-title-link">${escHtml(paper.title)}</a>`
    : escHtml(paper.title);

  const priorityBadge = `<span class="priority-badge priority-h1">H1</span>`;
  const sourceBadge = `<span class="source-badge">${escHtml(paper.source || '?')}</span>`;

  return `
    <tr>
      <td>${priorityBadge}</td>
      <td class="title-cell">
        ${titleLink}
        <div class="paper-meta">${formatAuthors(paper.authors)} · ${paper.year || '?'} · ${sourceBadge} ${renderPdfBadge(paper)}</div>
      </td>
      <td>${renderTagPills(paper.primary_tags, paper.formula_tags, [])}</td>
      <td>${renderTagPills([], [], paper.hook_types)}</td>
      <td class="reason-cell">${escHtml(paper.hook_summary || paper.reason || '—')}</td>
      <td class="idea-cell">${escHtml(paper.possible_idea || '—')}</td>
    </tr>`;
}

/**
 * 生成 H2 论文表格行
 */
function renderH2Row(paper) {
  const titleLink = paper.url
    ? `<a href="${escHtml(paper.url)}" target="_blank" rel="noopener" class="paper-title-link">${escHtml(paper.title)}</a>`
    : escHtml(paper.title);

  return `
    <tr>
      <td class="title-cell">
        ${titleLink}
        <div class="paper-meta">${formatAuthors(paper.authors)} · ${paper.year || '?'} ${renderPdfBadge(paper)}</div>
      </td>
      <td>${renderTagPills(paper.primary_tags, paper.formula_tags, paper.hook_types)}</td>
      <td class="idea-cell">${escHtml(paper.possible_idea || '—')}</td>
      <td>${escHtml(paper.reason || '—')}</td>
    </tr>`;
}

/**
 * 生成今日新增组件表
 */
function renderComponentTable(h1Papers, h2Papers) {
  const allPapers = [...h1Papers, ...h2Papers].filter(p =>
    p.primary_tags && p.primary_tags.some(t => ['A','B','C','D','E','F','G','H','I','J'].includes(t))
  );

  if (allPapers.length === 0) return '<p class="empty-note">今日无新增组件记录</p>';

  const rows = allPapers.slice(0, 10).map(p => {
    const componentTags = (p.primary_tags || []).filter(t => /^[A-J]$/.test(t));
    const titleLink = p.url
      ? `<a href="${escHtml(p.url)}" target="_blank" rel="noopener">${escHtml(p.title.substring(0, 60))}${p.title.length > 60 ? '...' : ''}</a>`
      : `${escHtml(p.title.substring(0, 60))}${p.title.length > 60 ? '...' : ''}`;

    return `<tr>
      <td>${renderTagPills(componentTags, p.formula_tags, [])}</td>
      <td class="title-cell">${titleLink}</td>
      <td><span class="priority-badge priority-${p.priority.toLowerCase()}">${p.priority}</span></td>
      <td class="idea-cell">${escHtml((p.writing_position || []).join(' / ') || '—')}</td>
    </tr>`;
  }).join('');

  return `<table class="data-table">
    <thead><tr><th>标签</th><th>来源论文</th><th>优先级</th><th>可用位置</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

/**
 * 生成今日建议动作列表
 */
function renderActions(h1Papers, h2Papers) {
  const actions = [];

  if (h1Papers.length > 0) {
    actions.push(`<li><strong>精读</strong>：${h1Papers.slice(0, 3).map(p => `《${escHtml(p.title.length > 40 ? p.title.substring(0, 40) + '...' : p.title)}》`).join('、')}</li>`);
  }

  const openPdfs = h1Papers.filter(p => p.pdf_status === 'open_pdf' && p.pdf_url);
  if (openPdfs.length > 0) {
    actions.push(`<li><strong>下载开放 PDF</strong>：${openPdfs.slice(0, 3).length} 篇可直接下载</li>`);
  }

  const methodHooks = [...h1Papers, ...h2Papers].filter(p => (p.hook_types || []).includes('方法 Hook'));
  if (methodHooks.length > 0) {
    const packNames = [...new Set(methodHooks.map(p => p.query_pack).filter(Boolean))];
    actions.push(`<li><strong>方法迁移候选</strong>：关注 ${packNames.slice(0, 3).join('、')} 方向的新组件</li>`);
  }

  const counterHooks = [...h1Papers, ...h2Papers].filter(p => (p.hook_types || []).includes('反例 Hook'));
  if (counterHooks.length > 0) {
    actions.push(`<li><strong>注意竞争基线</strong>：${counterHooks.slice(0, 2).map(p => escHtml(p.title.substring(0, 30))).join('、')} 可能需要纳入对比</li>`);
  }

  const ideaPool = h2Papers.slice(0, 5);
  if (ideaPool.length > 0) {
    actions.push(`<li><strong>Idea 池新增</strong>：${ideaPool.length} 篇进入 H2，建议本周内阅读摘要</li>`);
  }

  if (actions.length === 0) {
    actions.push('<li>今日无特别建议动作</li>');
  }

  return `<ul class="action-list">${actions.join('')}</ul>`;
}

/**
 * 生成完整 HTML 报告
 */
export function generateHtmlReport(reportData) {
  const { date, packs = [], total_candidates = 0, total_deduped = 0, h1 = [], h2 = [], h3 = [] } = reportData;

  const topDirections = [...new Set([...h1, ...h2].flatMap(p => p.primary_tags || []))].slice(0, 5).join(', ') || '暂无';

  const css = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #FAFAF9; color: #1a1a1a; font-size: 14px; line-height: 1.6; }

    .layout { display: flex; min-height: 100vh; }

    /* 侧边导航 */
    .sidebar { width: 220px; position: fixed; top: 0; left: 0; height: 100vh; background: #F5F4F0; border-right: 1px solid #e5e5e5; padding: 24px 16px; overflow-y: auto; flex-shrink: 0; }
    .sidebar h2 { font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; font-weight: 600; }
    .sidebar a { display: block; padding: 5px 8px; color: #444; text-decoration: none; border-radius: 4px; font-size: 13px; margin-bottom: 2px; }
    .sidebar a:hover { background: #eee; color: #000; }
    .sidebar .nav-count { font-size: 11px; color: #999; margin-left: 4px; }

    /* 主内容 */
    .main { margin-left: 220px; padding: 40px 48px; max-width: 1200px; }

    /* 标题区 */
    .report-header { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 2px solid #e5e5e5; }
    .report-header h1 { font-size: 28px; font-weight: 700; color: #1a1a1a; margin-bottom: 8px; }
    .report-header .subtitle { color: #666; font-size: 14px; }

    /* 总览卡片 */
    .overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 40px; }
    .stat-card { background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: 16px; }
    .stat-card .num { font-size: 32px; font-weight: 700; color: #1a1a1a; }
    .stat-card .label { font-size: 12px; color: #888; margin-top: 4px; }
    .stat-card.h1 .num { color: #DC2626; }
    .stat-card.h2 .num { color: #D97706; }
    .stat-card.h3 .num { color: #6B7280; }

    /* 章节 */
    .section { margin-bottom: 48px; }
    .section-title { font-size: 20px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #e5e5e5; display: flex; align-items: center; gap: 8px; }
    .section-title .priority-indicator { width: 6px; height: 24px; border-radius: 3px; }
    .section-title .priority-indicator.h1 { background: #DC2626; }
    .section-title .priority-indicator.h2 { background: #D97706; }
    .section-title .priority-indicator.h3 { background: #6B7280; }

    /* 表格 */
    .data-table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; overflow: hidden; }
    .data-table th { background: #F5F4F0; padding: 10px 14px; text-align: left; font-size: 12px; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 0.03em; border-bottom: 1px solid #e5e5e5; }
    .data-table td { padding: 12px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
    .data-table tr:last-child td { border-bottom: none; }
    .data-table tr:hover td { background: #FAFAF9; }
    .title-cell { max-width: 320px; }
    .reason-cell, .idea-cell { max-width: 200px; font-size: 13px; color: #444; }

    /* 论文标题链接 */
    .paper-title-link { color: #1a1a1a; text-decoration: none; font-weight: 500; font-size: 13px; }
    .paper-title-link:hover { color: #2563EB; text-decoration: underline; }
    .paper-meta { font-size: 12px; color: #888; margin-top: 4px; }

    /* 优先级徽章 */
    .priority-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; }
    .priority-h1 { background: #FEE2E2; color: #DC2626; }
    .priority-h2 { background: #FEF3C7; color: #D97706; }
    .priority-h3 { background: #F3F4F6; color: #6B7280; }

    /* 来源徽章 */
    .source-badge { display: inline-block; padding: 1px 6px; background: #EFF6FF; color: #2563EB; border-radius: 3px; font-size: 11px; }

    /* 链接徽章 */
    .badge { display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 11px; text-decoration: none; margin-left: 4px; }
    .badge-open { background: #D1FAE5; color: #059669; }
    .badge-code { background: #EDE9FE; color: #7C3AED; }
    .badge-paywall { background: #FEE2E2; color: #DC2626; }

    /* 标签 pill */
    .pill { display: inline-block; padding: 2px 7px; border-radius: 12px; font-size: 11px; font-weight: 600; margin: 1px; white-space: nowrap; }
    .pill-tag { background: #DBEAFE; color: #1D4ED8; }
    .pill-formula { background: #EDE9FE; color: #6D28D9; }
    .pill-hook { background: #D1FAE5; color: #065F46; }

    /* H3 折叠 */
    details { background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: 12px 16px; }
    details summary { cursor: pointer; font-weight: 600; color: #444; list-style: none; }
    details summary::-webkit-details-marker { display: none; }
    .h3-list { margin-top: 12px; }
    .h3-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; display: flex; align-items: flex-start; gap: 8px; }
    .h3-item:last-child { border-bottom: none; }
    .h3-item a { color: #444; text-decoration: none; }
    .h3-item a:hover { color: #2563EB; }

    /* 建议动作 */
    .action-list { list-style: none; }
    .action-list li { padding: 10px 14px; background: #fff; border: 1px solid #e5e5e5; border-radius: 6px; margin-bottom: 8px; font-size: 14px; }

    .empty-note { color: #999; font-size: 13px; padding: 16px 0; font-style: italic; }

    @media (max-width: 768px) {
      .sidebar { display: none; }
      .main { margin-left: 0; padding: 20px 16px; }
      .overview-grid { grid-template-columns: repeat(2, 1fr); }
    }
  `;

  const nav = `
    <nav class="sidebar">
      <h2>今日导航</h2>
      <a href="#overview">总览</a>
      <a href="#h1">H1 精读候选 <span class="nav-count">(${h1.length})</span></a>
      <a href="#h2">H2 Idea 池 <span class="nav-count">(${h2.length})</span></a>
      <a href="#h3">H3 普通参考 <span class="nav-count">(${h3.length})</span></a>
      <a href="#components">今日新增组件</a>
      <a href="#actions">建议动作</a>
    </nav>`;

  const h1Table = h1.length > 0
    ? `<table class="data-table">
        <thead><tr><th>优先级</th><th>论文</th><th>组件标签</th><th>Hook</th><th>为什么重要</th><th>可迁移 Idea</th></tr></thead>
        <tbody>${h1.map((p, i) => renderH1Row(p, i)).join('')}</tbody>
      </table>`
    : '<p class="empty-note">今日无 H1 精读候选</p>';

  const h2Table = h2.length > 0
    ? `<table class="data-table">
        <thead><tr><th>论文</th><th>标签</th><th>可迁移 Idea</th><th>暂存理由</th></tr></thead>
        <tbody>${h2.map(p => renderH2Row(p)).join('')}</tbody>
      </table>`
    : '<p class="empty-note">今日无 H2 候选</p>';

  const h3Details = h3.length > 0
    ? `<details>
        <summary>展开 H3 普通参考（共 ${h3.length} 篇）</summary>
        <div class="h3-list">
          ${h3.map(p => `
            <div class="h3-item">
              ${renderTagPills(p.primary_tags, [], [])}
              ${p.url
                ? `<a href="${escHtml(p.url)}" target="_blank" rel="noopener">${escHtml(p.title)}</a>`
                : escHtml(p.title)}
              <span style="color:#999;font-size:11px;margin-left:auto;">${p.source || ''} · ${p.year || ''}</span>
            </div>
          `).join('')}
        </div>
      </details>`
    : '<p class="empty-note">今日无 H3 参考</p>';

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日论文组件雷达｜${escHtml(date)}</title>
  <style>${css}</style>
</head>
<body>
<div class="layout">
  ${nav}
  <main class="main">
    <div class="report-header">
      <h1>每日论文组件雷达</h1>
      <div class="subtitle">
        ${escHtml(date)} · 检索方向：${escHtml(packs.join(' / '))} ·
        候选 ${total_candidates} → 去重后 ${total_deduped} 篇
      </div>
    </div>

    <div id="overview">
      <div class="overview-grid">
        <div class="stat-card h1">
          <div class="num">${h1.length}</div>
          <div class="label">H1 精读候选</div>
        </div>
        <div class="stat-card h2">
          <div class="num">${h2.length}</div>
          <div class="label">H2 Idea 池</div>
        </div>
        <div class="stat-card h3">
          <div class="num">${h3.length}</div>
          <div class="label">H3 普通参考</div>
        </div>
        <div class="stat-card">
          <div class="num">${total_deduped}</div>
          <div class="label">今日去重总数</div>
        </div>
        <div class="stat-card">
          <div class="num">${[...h1,...h2].reduce((n,p) => n + (p.pdf_status === 'open_pdf' ? 1 : 0), 0)}</div>
          <div class="label">开放 PDF 可下载</div>
        </div>
        <div class="stat-card">
          <div class="num">${topDirections.split(',').length}</div>
          <div class="label">今日最强方向数</div>
        </div>
      </div>
      <div style="background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:12px 16px;margin-bottom:40px;font-size:13px;color:#555;">
        今日最强方向：<strong>${escHtml(topDirections)}</strong>
      </div>
    </div>

    <section class="section" id="h1">
      <h2 class="section-title">
        <span class="priority-indicator h1"></span>
        H1 精读候选
      </h2>
      ${h1Table}
    </section>

    <section class="section" id="h2">
      <h2 class="section-title">
        <span class="priority-indicator h2"></span>
        H2 Idea 池
      </h2>
      ${h2Table}
    </section>

    <section class="section" id="h3">
      <h2 class="section-title">
        <span class="priority-indicator h3"></span>
        H3 普通参考
      </h2>
      ${h3Details}
    </section>

    <section class="section" id="components">
      <h2 class="section-title">今日新增组件</h2>
      ${renderComponentTable(h1, h2)}
    </section>

    <section class="section" id="actions">
      <h2 class="section-title">今日建议动作</h2>
      ${renderActions(h1, h2)}
    </section>
  </main>
</div>
</body>
</html>`;
}

// CLI 模式：读 JSON stdin，写 HTML stdout 或文件
if (process.argv[1] === new URL(import.meta.url).pathname) {
  import('node:fs').then(({ readFileSync, writeFileSync, mkdirSync }) => {
    const args = process.argv.slice(2);
    const inputFile = args[0] || null;
    const outputFile = args[1] || null;

    let input = '';
    if (inputFile) {
      input = readFileSync(inputFile, 'utf8');
      const data = JSON.parse(input);
      const html = generateHtmlReport(data);
      if (outputFile) {
        mkdirSync(outputFile.replace(/[^/\\]*$/, ''), { recursive: true });
        writeFileSync(outputFile, html, 'utf8');
        console.log(`HTML 报告已写入: ${outputFile}`);
      } else {
        process.stdout.write(html);
      }
    } else {
      // 从 stdin 读
      process.stdin.setEncoding('utf8');
      const chunks = [];
      process.stdin.on('data', c => chunks.push(c));
      process.stdin.on('end', () => {
        const data = JSON.parse(chunks.join(''));
        const html = generateHtmlReport(data);
        if (outputFile) {
          mkdirSync(outputFile.replace(/[^/\\]*$/, ''), { recursive: true });
          writeFileSync(outputFile, html, 'utf8');
          console.log(`HTML 报告已写入: ${outputFile}`);
        } else {
          process.stdout.write(html);
        }
      });
    }
  });
}
