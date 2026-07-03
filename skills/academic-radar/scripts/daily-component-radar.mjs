#!/usr/bin/env node
// scripts/daily-component-radar.mjs
// 论文雷达主入口
//
// 用法：
//   node scripts/daily-component-radar.mjs --mock
//   node scripts/daily-component-radar.mjs --days 7 --max 30 --name latest
//   node scripts/daily-component-radar.mjs --pack mamba-ssm --days 7
//   node scripts/daily-component-radar.mjs --keywords "DeltaNet,xLSTM" --days 14
//   node scripts/daily-component-radar.mjs --sources arxiv,openalex
//   node scripts/daily-component-radar.mjs --sources arxiv,semantic_scholar,openalex

import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ============================================================
// 解析 CLI 参数
// ============================================================
function parseArgs(argv) {
  const args = {
    days: 7,
    max: 30,
    pack: [],   // 支持多次 --pack，收集为数组
    keywords: null,
    name: 'latest',
    mock: false,
    output: join(ROOT, 'outputs', 'latest'),
    sources: ['arxiv', 'openalex']  // 默认不含 S2（频繁 429）
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--mock') args.mock = true;
    else if (arg === '--cdp') console.warn('[radar] --cdp 暂未实现，忽略。如需 Google Scholar/CNKI，请使用 cdp-proxy.mjs 手动操作。');
    else if (arg === '--days' && argv[i + 1]) { args.days = parseInt(argv[++i]); }
    else if (arg === '--max' && argv[i + 1]) { args.max = parseInt(argv[++i]); }
    else if (arg === '--pack' && argv[i + 1]) { args.pack.push(argv[++i]); }
    else if (arg === '--keywords' && argv[i + 1]) {
      // --keywords "DeltaNet,xLSTM,linear recurrence"
      args.keywords = argv[++i].split(',').map(s => s.trim()).filter(Boolean);
    }
    else if (arg === '--name' && argv[i + 1]) { args.name = argv[++i]; }
    else if (arg === '--output' && argv[i + 1]) { args.output = argv[++i]; }
    else if (arg === '--sources' && argv[i + 1]) {
      // --sources arxiv,openalex,semantic_scholar
      args.sources = argv[++i].split(',').map(s => s.trim()).filter(Boolean);
    }
  }

  return args;
}

function defaultPack() {
  return {
    name: 'default',
    description: '默认检索包',
    primary_tags: ['D', 'T'],
    formula_tags: [],
    keywords: ['Mamba', 'state space model', 'hyperspectral', 'soil organic carbon', 'physics-informed']
  };
}

// ============================================================
// 主流程
// ============================================================
async function main() {
  const args = parseArgs(process.argv);

  console.log('');
  console.log('╔══════════════════════════════════════════════════╗');
  console.log('║     Academic Paper Radar  v2.0                   ║');
  console.log('╚══════════════════════════════════════════════════╝');
  console.log('');

  // 动态导入模块（避免顶层 await 问题）
  const [
    { classifyPapers },
    { extractHooksFromPapers },
    { rankPapers, getSummary },
    { generateHtmlReport },
    { generateMarkdownReport }
  ] = await Promise.all([
    import('./classify-components.mjs'),
    import('./extract-hooks.mjs'),
    import('./rank-papers.mjs'),
    import('./export-radar-html.mjs'),
    import('./export-radar-md.mjs')
  ]);

  const today = new Date().toISOString().split('T')[0];
  const fileTag = args.mock ? 'demo' : args.name;

  // ---- Step 1: 获取候选论文 ----
  let rawPapers = [];
  let packsUsed = [];

  if (args.mock) {
    console.log('[radar] 使用 mock 数据（--mock 模式，不请求真实 API）');
    const { MOCK_PAPERS } = await import('./mock-papers.mjs');
    rawPapers = MOCK_PAPERS;
    packsUsed = ['mock-demo'];
  } else {
    const { searchForPack, deduplicatePapers, parseSimpleYaml } = await import('./search-adapter.mjs');

    let packs = [];

    if (args.keywords && args.keywords.length > 0) {
      // --keywords 模式：直接构造临时 pack
      packs = [{
        name: 'custom',
        description: `自定义关键词: ${args.keywords.join(', ')}`,
        primary_tags: [],
        formula_tags: [],
        keywords: args.keywords
      }];
    } else {
      // 加载 query packs
      const packsDir = join(ROOT, 'references', 'query-packs');
      let files = [];
      try {
        files = readdirSync(packsDir).filter(f => f.endsWith('.yaml'));
      } catch {
        console.warn('[radar] query-packs 目录不存在，使用内置默认 pack');
      }

      for (const file of files) {
        try {
          const content = readFileSync(join(packsDir, file), 'utf8');
          const pack = parseSimpleYaml(content);
          if (args.pack.length > 0 && !args.pack.includes(pack.name)) continue;
          packs.push(pack);
        } catch (e) {
          console.warn(`[radar] 跳过 ${file}: ${e.message}`);
        }
      }

      if (packs.length === 0) packs = [defaultPack()];
    }

    packsUsed = packs.map(p => p.name);

    console.log(`[radar] 检索方向：${packsUsed.join(', ')}`);
    console.log(`[radar] 时间范围：最近 ${args.days} 天，每包最多 ${args.max} 篇`);
    console.log(`[radar] 数据源：${args.sources.join(', ')}`);
    console.log('');

    // 顺序检索各 pack（避免并发触发反爬）
    for (const pack of packs) {
      console.log(`[radar] 检索 pack: ${pack.name}`);
      const results = await searchForPack(pack, {
        days: args.days,
        max: args.max,
        sources: args.sources
      });
      rawPapers.push(...results);
      console.log(`[radar] pack ${pack.name} 获得 ${results.length} 篇`);
    }

    rawPapers = deduplicatePapers(rawPapers);
    console.log(`[radar] 去重后共 ${rawPapers.length} 篇`);
  }

  const totalCandidates = rawPapers.length;

  // ---- Step 2: 分类 ----
  console.log('[radar] 开始 A-T+U 分类...');
  const classified = classifyPapers(rawPapers);

  // ---- Step 3: Hook 提取 ----
  console.log('[radar] 提取 8 类 Hook...');
  const withHooks = extractHooksFromPapers(classified);

  // ---- Step 4: 优先级排序 ----
  console.log('[radar] 生成 H1/H2/H3 优先级...');
  const ranked = rankPapers(withHooks);
  const summary = getSummary(ranked);

  console.log('');
  console.log(`┌─ 今日总览 ──────────────────────────┐`);
  console.log(`│  候选论文：${String(totalCandidates).padEnd(5)} 去重后：${String(ranked.length).padEnd(5)}          │`);
  console.log(`│  H1 精读候选：${String(summary.h1Count).padEnd(3)}  H2 Idea 池：${String(summary.h2Count).padEnd(3)}  H3：${summary.h3Count}  │`);
  console.log(`└────────────────────────────────────┘`);
  console.log('');

  // ---- Step 5: 构造报告数据 ----
  const reportData = {
    date: fileTag === 'demo' ? today + ' (demo)' : today,
    packs: packsUsed,
    total_candidates: totalCandidates,
    total_deduped: ranked.length,
    h1: summary.h1,
    h2: summary.h2,
    h3: summary.h3
  };

  // ---- Step 6: 写出文件 ----
  mkdirSync(args.output, { recursive: true });

  const baseName = `radar-${fileTag}`;
  const jsonPath = join(args.output, `${baseName}.json`);
  const htmlPath = join(args.output, `${baseName}.html`);
  const mdPath   = join(args.output, `${baseName}.md`);

  // JSON 原始结果
  writeFileSync(jsonPath, JSON.stringify(reportData, null, 2), 'utf8');
  console.log(`[radar] JSON 已写入: ${jsonPath}`);

  // HTML 报告
  const html = generateHtmlReport(reportData);
  writeFileSync(htmlPath, html, 'utf8');
  console.log(`[radar] HTML 已写入: ${htmlPath}`);

  // Markdown 报告
  const md = generateMarkdownReport(reportData);
  writeFileSync(mdPath, md, 'utf8');
  console.log(`[radar] Markdown 已写入: ${mdPath}`);

  console.log('');
  if (summary.h1Count > 0) {
    console.log('★ H1 精读候选：');
    summary.h1.forEach((p, i) => {
      console.log(`  ${i + 1}. [${(p.primary_tags || []).join(',')}] ${p.title.substring(0, 70)}`);
      if (p.url) console.log(`     → ${p.url}`);
    });
    console.log('');
  }

  console.log('✓ 雷达运行完成。');
  if (args.mock) {
    console.log(`  打开报告: ${htmlPath}`);
  }
}

main().catch(e => {
  console.error('[radar] 运行失败:', e);
  process.exit(1);
});
