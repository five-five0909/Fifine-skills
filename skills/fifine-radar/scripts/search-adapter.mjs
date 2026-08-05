// scripts/search-adapter.mjs
// 多源学术论文检索适配层
// 数据源：arXiv / Semantic Scholar / OpenAlex / Crossref / Unpaywall / Papers with Code

// ============================================================
// 工具函数
// ============================================================

/** 构造空白 paper 对象 */
function emptyPaper(overrides = {}) {
  return {
    title: '',
    authors: [],
    year: null,
    published_date: '',
    source: '',
    venue: '',
    url: '',
    doi: '',
    arxiv_id: '',
    abstract: '',
    pdf_status: 'unknown',
    pdf_url: '',
    code_url: '',
    citations: null,
    query_pack: '',
    matched_keywords: [],
    primary_tags: [],
    formula_tags: [],
    hook_types: [],
    hook_summary: '',
    possible_idea: '',
    possible_experiment: '',
    writing_position: [],
    risk_note: '',
    priority: '',
    reason: '',
    ...overrides
  };
}

/** 安全 fetch，失败返回 null；对开放学术 API 做短重试，避免偶发代理/握手抖动 */
async function safeFetch(url, options = {}, timeoutMs = 20000) {
  const attempts = options.attempts || 3;
  const retryStatuses = new Set([408, 429, 500, 502, 503, 504]);
  const { attempts: _attempts, headers, ...fetchOptions } = options;

  for (let attempt = 1; attempt <= attempts; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const resp = await fetch(url, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'AcademicRadar/1.1 (research tool; mailto:research@example.com)',
          'Accept': 'application/json',
          ...headers
        },
        ...fetchOptions
      });
      clearTimeout(timer);
      if (resp.ok) return resp;

      console.warn(`[search-adapter] HTTP ${resp.status} for ${url}`);
      if (!retryStatuses.has(resp.status) || attempt === attempts) return null;
    } catch (e) {
      clearTimeout(timer);
      const reason = e.name === 'AbortError' ? '超时' : `请求失败: ${e.message}`;
      console.warn(`[search-adapter] ${reason}: ${url}`);
      if (attempt === attempts) return null;
    }
    await sleep(600 * attempt);
  }
  return null;
}

/** sleep，避免请求过快 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** 计算两个标题字符串的相似度（简单 Jaccard）*/
function titleSimilarity(a, b) {
  if (!a || !b) return 0;
  const tokensA = new Set(a.toLowerCase().split(/\W+/).filter(t => t.length > 3));
  const tokensB = new Set(b.toLowerCase().split(/\W+/).filter(t => t.length > 3));
  const intersection = [...tokensA].filter(t => tokensB.has(t)).length;
  const union = new Set([...tokensA, ...tokensB]).size;
  return union === 0 ? 0 : intersection / union;
}

/**
 * 构造 days 天前的 ISO 日期字符串
 */
function daysAgoISO(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

// ============================================================
// arXiv 检索
// ============================================================

/**
 * 解析 arXiv Atom XML，返回 paper 数组
 */
function parseArxivXML(xml) {
  const entries = xml.match(/<entry>([\s\S]*?)<\/entry>/g) || [];
  return entries.map(entry => {
    const get = (tag) => {
      const m = entry.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\/${tag}>`));
      return m ? m[1].trim().replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'").replace(/&quot;/g, '"') : '';
    };
    const getAll = (tag) => {
      const matches = entry.matchAll(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\/${tag}>`, 'g'));
      return [...matches].map(m => m[1].trim());
    };

    const idFull = get('id');
    const arxivId = idFull.split('/abs/')[1] || idFull.split('/').pop() || '';
    const publishedRaw = get('published');
    const publishedDate = publishedRaw ? publishedRaw.split('T')[0] : '';
    const year = publishedDate ? parseInt(publishedDate.split('-')[0]) : null;

    const pdfLink = entry.match(/href="(https:\/\/arxiv\.org\/pdf\/[^"]+)"/)?.[1] ||
                    (arxivId ? `https://arxiv.org/pdf/${arxivId}` : '');

    const authorNames = getAll('name');

    const doiMatch = entry.match(/<arxiv:doi[^>]*>([\s\S]*?)<\/arxiv:doi>/);
    const doi = doiMatch ? doiMatch[1].trim() : '';

    return emptyPaper({
      title: get('title').replace(/\s+/g, ' '),
      authors: authorNames,
      year,
      published_date: publishedDate,
      source: 'arxiv',
      url: idFull || (arxivId ? `https://arxiv.org/abs/${arxivId}` : ''),
      doi,
      arxiv_id: arxivId,
      abstract: get('summary').replace(/\s+/g, ' '),
      pdf_status: 'open_pdf',
      pdf_url: pdfLink
    });
  });
}

/**
 * 搜索 arXiv
 * @param {string} query - 搜索关键词
 * @param {number} days - 最近几天
 * @param {number} max - 最多几条
 * @param {string} queryPack - 来源 pack 名称
 */
export async function searchArxiv(query, { days = 1, max = 20, queryPack = '' } = {}) {
  // 取前3个关键词构造 title+abstract OR 查询（比 all: 更精准）
  const terms = query.split(/\s+OR\s+/i).map(t => t.trim()).filter(Boolean);
  const primaryTerms = terms.slice(0, 3);
  const arxivParts = primaryTerms.map(t => {
    const normalized = t.replace(/^["']|["']$/g, '').replace(/\s+/g, ' ');
    const arxivTerm = /\s/.test(normalized) ? `"${normalized}"` : normalized;
    return `(ti:${encodeURIComponent(arxivTerm)}+OR+abs:${encodeURIComponent(arxivTerm)})`;
  });
  const arxivQuery = arxivParts.join('+OR+');
  // 多抓一些，客户端过滤日期
  const fetchMax = Math.max(max * 3, 50);
  const url = `https://export.arxiv.org/api/query?search_query=${arxivQuery}&max_results=${fetchMax}&sortBy=submittedDate&sortOrder=descending`;

  const resp = await safeFetch(url, { headers: { 'Accept': 'application/xml' } });
  if (!resp) return [];

  const xml = await resp.text();
  const papers = parseArxivXML(xml);

  // 有效日期过滤：短窗口时加 2 天缓冲（arXiv 时区/提交延迟），但不强制覆盖用户设置
  const effectiveDays = days < 3 ? days + 2 : days;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - effectiveDays);
  const nowYear = new Date().getFullYear();

  const filtered = papers.filter(p => {
    if (!p.published_date) return true;
    const pub = new Date(p.published_date);
    if (pub.getFullYear() > nowYear + 1) return false; // 过滤异常未来日期
    return pub >= cutoff;
  });

  return filtered.slice(0, max).map(p => ({ ...p, query_pack: queryPack }));
}

// ============================================================
// Semantic Scholar 检索
// ============================================================

export async function searchSemanticScholar(query, { max = 20, queryPack = '' } = {}) {
  const fields = 'title,authors,year,publicationDate,venue,externalIds,abstract,citationCount,openAccessPdf,fieldsOfStudy';
  const url = `https://api.semanticscholar.org/graph/v1/paper/search?query=${encodeURIComponent(query)}&limit=${max}&fields=${fields}`;

  const resp = await safeFetch(url);
  if (!resp) return [];

  let data;
  try {
    data = await resp.json();
  } catch {
    return [];
  }

  const papers = (data.data || []).map(item => {
    const doi = item.externalIds?.DOI || '';
    const arxivId = item.externalIds?.ArXiv || '';
    const pubDate = item.publicationDate || (item.year ? `${item.year}-01-01` : '');
    const oaPdf = item.openAccessPdf?.url || '';

    return emptyPaper({
      title: item.title || '',
      authors: (item.authors || []).map(a => a.name || ''),
      year: item.year || null,
      published_date: pubDate,
      source: 'semantic_scholar',
      url: item.externalIds?.ArXiv
        ? `https://arxiv.org/abs/${item.externalIds.ArXiv}`
        : `https://www.semanticscholar.org/paper/${item.paperId}`,
      doi,
      arxiv_id: arxivId,
      abstract: item.abstract || '',
      pdf_status: oaPdf ? 'open_pdf' : 'unknown',
      pdf_url: oaPdf,
      citations: item.citationCount ?? null,
      venue: item.venue || '',
      query_pack: queryPack
    });
  });

  return papers;
}

// ============================================================
// OpenAlex 检索
// ============================================================

function openAlexConceptFilters(queryPack) {
  const conceptsByPack = {
    'mamba-ssm': ['C41008148'],              // Computer Science
    'vision-remote-mamba': ['C41008148'],    // Computer Science
    'hyperspectral': ['C41008148'],
    'efficient-components': ['C41008148'],
    'soil-soc': [],
    'pinn-soilml': []                        // Too broad: keep query-driven
  };
  return conceptsByPack[queryPack] || [];
}

function isRelevantToQuery(paper, query) {
  const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase();
  const normalizedQuery = query.toLowerCase().replace(/[-_]/g, ' ').replace(/\s+/g, ' ').trim();
  if (normalizedQuery && text.includes(normalizedQuery)) return true;

  const stop = new Set([
    'prediction', 'predictive', 'estimation', 'estimating', 'model', 'models',
    'modeling', 'modelling', 'machine', 'learning', 'digital', 'mapping',
    'function', 'using', 'based', 'near', 'infrared'
  ]);
  const tokens = normalizedQuery
    .split(/\W+/)
    .filter(t => t.length >= 3 && !stop.has(t));

  if (tokens.length === 0) return true;
  if (normalizedQuery.split(/\W+/).length > 1 && tokens.length < 2) return false;
  if (tokens.length === 1) return text.includes(tokens[0]);

  const matched = tokens.filter(t => text.includes(t)).length;
  return matched >= Math.ceil(tokens.length * 0.75);
}

function isRelevantToPack(paper, queryPack) {
  if (queryPack !== 'soil-soc') return true;
  const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase();
  const strongPatterns = [
    /soil organic carbon/,
    /soil organic matter/,
    /\bsoc\b/,
    /\bsom\b/,
    /soil spectroscop/,
    /vis[\s-]?nir/,
    /near infrared spectroscop/,
    /digital soil mapping/,
    /soil carbon/
  ];
  return strongPatterns.some(pattern => pattern.test(text));
}

export async function searchOpenAlex(query, { days = 7, max = 20, queryPack = '', conceptIds = null } = {}) {
  const fromDate = daysAgoISO(days);
  const today = new Date().toISOString().split('T')[0];
  const filters = [
    `from_publication_date:${fromDate}`,
    `to_publication_date:${today}`,
    `title_and_abstract.search:${query}`
  ];
  const conceptFilters = conceptIds ?? openAlexConceptFilters(queryPack);
  for (const conceptId of conceptFilters) filters.push(`concepts.id:${conceptId}`);
  const filter = filters.join(',');
  const url = `https://api.openalex.org/works?filter=${encodeURIComponent(filter)}&per-page=${max}&sort=publication_date:desc&select=title,authorships,publication_year,publication_date,primary_location,doi,abstract_inverted_index,cited_by_count,open_access,ids`;

  const resp = await safeFetch(url, {
    headers: { 'Accept': 'application/json', 'User-Agent': 'AcademicRadar/1.1 (mailto:research@example.com)' },
    attempts: 3
  }, 25000);
  if (!resp) return [];

  let data;
  try { data = await resp.json(); } catch { return []; }

  const nowYear = new Date().getFullYear();
  const papers = (data.results || []).filter(item => {
    // 过滤未来异常日期（OpenAlex 预印本/在线优先发表有时日期错误）
    const year = item.publication_year;
    return !year || year <= nowYear + 1;
  }).map(item => {
    // 还原摘要（OpenAlex 使用倒排索引格式）
    let abstract = '';
    if (item.abstract_inverted_index) {
      try {
        const positions = {};
        for (const [word, positions_arr] of Object.entries(item.abstract_inverted_index)) {
          for (const pos of positions_arr) {
            positions[pos] = word;
          }
        }
        const maxPos = Math.max(...Object.keys(positions).map(Number));
        abstract = Array.from({ length: maxPos + 1 }, (_, i) => positions[i] || '').join(' ');
      } catch { abstract = ''; }
    }

    const doi = item.doi ? item.doi.replace('https://doi.org/', '') : '';
    const arxivId = item.ids?.arxiv ? item.ids.arxiv.replace('https://arxiv.org/abs/', '') : '';
    const oaUrl = item.open_access?.oa_url || '';

    return emptyPaper({
      title: item.title || '',
      authors: (item.authorships || []).map(a => a.author?.display_name || ''),
      year: item.publication_year || null,
      published_date: item.publication_date || '',
      source: 'openalex',
      url: arxivId ? `https://arxiv.org/abs/${arxivId}` : (doi ? `https://doi.org/${doi}` : ''),
      doi,
      arxiv_id: arxivId,
      abstract,
      pdf_status: oaUrl ? 'open_pdf' : (item.open_access?.is_oa ? 'open_pdf' : 'unknown'),
      pdf_url: oaUrl,
      citations: item.cited_by_count ?? null,
      venue: item.primary_location?.source?.display_name || '',
      query_pack: queryPack
    });
  });

  return papers.filter(p => isRelevantToQuery(p, query) && isRelevantToPack(p, queryPack));
}

// ============================================================
// Papers with Code 代码链接补充
// ============================================================

export async function searchPapersWithCode(query, { max = 10, queryPack = '' } = {}) {
  const url = `https://paperswithcode.com/api/v1/papers/?q=${encodeURIComponent(query)}&items_per_page=${max}&ordering=-published`;

  const resp = await safeFetch(url);
  if (!resp) return [];

  let data;
  try { data = await resp.json(); } catch { return []; }

  return (data.results || []).map(item => {
    const arxivId = item.arxiv_id || '';
    return emptyPaper({
      title: item.title || '',
      authors: [],
      year: item.published ? parseInt(item.published.split('-')[0]) : null,
      published_date: item.published || '',
      source: 'papers_with_code',
      url: arxivId ? `https://arxiv.org/abs/${arxivId}` : (item.url_pdf || ''),
      arxiv_id: arxivId,
      abstract: item.abstract || '',
      pdf_status: item.url_pdf ? 'open_pdf' : 'unknown',
      pdf_url: item.url_pdf || '',
      code_url: item.repository_url || '',
      citations: null,
      query_pack: queryPack
    });
  });
}

// ============================================================
// Unpaywall OA 状态补充（按 DOI 查询）
// ============================================================

export async function checkUnpaywall(doi, email = 'research@example.com') {
  if (!doi) return null;
  const url = `https://api.unpaywall.org/v2/${encodeURIComponent(doi)}?email=${email}`;
  const resp = await safeFetch(url);
  if (!resp) return null;
  try {
    const data = await resp.json();
    const oaUrl = data.best_oa_location?.url_for_pdf || data.best_oa_location?.url || '';
    return {
      pdf_status: oaUrl ? 'open_pdf' : (data.is_oa ? 'open_pdf' : 'needs_institution'),
      pdf_url: oaUrl
    };
  } catch {
    return null;
  }
}

// ============================================================
// 去重逻辑
// ============================================================

/**
 * 对多源论文进行去重
 * 优先级：DOI → arXiv ID → 标题相似度（Jaccard >= 0.7）
 */
export function deduplicatePapers(papers) {
  const seen_doi = new Map();    // doi → paper
  const seen_arxiv = new Map();  // arxiv_id → paper
  const unique = [];

  for (const paper of papers) {
    const doi = (paper.doi || '').trim().toLowerCase();
    const arxiv = (paper.arxiv_id || '').trim();
    const title = (paper.title || '').trim();

    // DOI 去重
    if (doi) {
      if (seen_doi.has(doi)) {
        const existing = seen_doi.get(doi);
        if (!existing.code_url && paper.code_url) existing.code_url = paper.code_url;
        if (!existing.pdf_url && paper.pdf_url) existing.pdf_url = paper.pdf_url;
        if (paper.pdf_status === 'open_pdf') existing.pdf_status = 'open_pdf';
        // 补充 arXiv ID（可能另一来源带来的）
        if (!existing.arxiv_id && arxiv) { existing.arxiv_id = arxiv; seen_arxiv.set(arxiv, existing); }
        continue;
      }
      seen_doi.set(doi, paper);
    }

    // arXiv ID 去重
    if (arxiv) {
      if (seen_arxiv.has(arxiv)) {
        const existing = seen_arxiv.get(arxiv);
        if (!existing.code_url && paper.code_url) existing.code_url = paper.code_url;
        if (!existing.pdf_url && paper.pdf_url) existing.pdf_url = paper.pdf_url;
        if (paper.pdf_status === 'open_pdf') existing.pdf_status = 'open_pdf';
        // 补充 DOI
        if (!existing.doi && doi) { existing.doi = doi; seen_doi.set(doi, existing); }
        continue;
      }
      seen_arxiv.set(arxiv, paper);
    }

    // 标题相似度去重
    const isDuplicate = unique.some(existing =>
      titleSimilarity(existing.title, title) >= 0.7
    );
    if (isDuplicate) continue;

    unique.push(paper);
  }

  return unique;
}

// ============================================================
// 批量检索入口
// ============================================================

/**
 * 针对单个 query pack 的多源检索
 * @param {Object} pack - { name, keywords, primary_tags, formula_tags }
 * @param {Object} opts - { days, max, sources }
 */
export async function searchForPack(pack, { days = 1, max = 20, sources = ['arxiv', 'semantic_scholar', 'openalex'] } = {}) {
  const keywords = pack.keywords || [];
  const packName = pack.name || '';

  // 构造查询字符串（取前 5 个关键词 OR 组合）
  const queryTerms = keywords.slice(0, 5).join(' OR ');
  const results = [];

  const perSourceMax = Math.ceil(max * 1.5); // 多拉一些，去重后取 max

  if (sources.includes('arxiv')) {
    console.log(`[search] arXiv: ${queryTerms.substring(0, 60)}...`);
    const arxivResults = await searchArxiv(queryTerms, { days, max: perSourceMax, queryPack: packName });
    results.push(...arxivResults);
    await sleep(1000); // arXiv 限速
  }

  if (sources.includes('semantic_scholar')) {
    console.log(`[search] Semantic Scholar: ${queryTerms.substring(0, 60)}...`);
    const s2Results = await searchSemanticScholar(queryTerms, { max: perSourceMax, queryPack: packName });
    results.push(...s2Results);
    await sleep(500);
  }

  if (sources.includes('openalex')) {
    console.log(`[search] OpenAlex: ${queryTerms.substring(0, 60)}...`);
    const perKeywordMax = Math.max(3, Math.ceil(perSourceMax / Math.min(keywords.length || 1, 5)));
    for (const keyword of keywords.slice(0, 5)) {
      const oaResults = await searchOpenAlex(keyword, { days, max: perKeywordMax, queryPack: packName });
      results.push(...oaResults);
      await sleep(250);
    }
    await sleep(500);
  }

  if (sources.includes('papers_with_code')) {
    console.log(`[search] Papers with Code: ${queryTerms.substring(0, 60)}...`);
    const pwcResults = await searchPapersWithCode(keywords[0] || '', { max: 10, queryPack: packName });
    results.push(...pwcResults);
  }

  // 去重
  const deduped = deduplicatePapers(results);

  // 只保留有标题的，限制数量
  return deduped.filter(p => p.title).slice(0, max);
}

// ============================================================
// YAML 解析工具（轻量，无依赖）
// ============================================================

/**
 * 解析极简 YAML（只支持本项目 query-packs 用到的格式）
 * 支持：顶层 key: value、列表项 `  - item`、内联数组 `[A, B, C]`
 */
export function parseSimpleYaml(yamlStr) {
  const result = {};
  let currentKey = null;

  for (const rawLine of yamlStr.split('\n')) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith('#')) continue;

    // 列表项
    if (line.match(/^\s+-\s+(.+)/) && currentKey) {
      const item = line.match(/^\s+-\s+(.+)/)[1].trim();
      if (!Array.isArray(result[currentKey])) result[currentKey] = [];
      result[currentKey].push(item);
      continue;
    }

    // key: value 或 key:
    const kvMatch = line.match(/^(\w[\w-]*)\s*:\s*(.*)/);
    if (kvMatch) {
      currentKey = kvMatch[1];
      const val = kvMatch[2].trim();

      if (val.startsWith('[') && val.endsWith(']')) {
        // 内联数组 [A, B, C] 或 ["A", "B"] 或 ['A', 'B']
        result[currentKey] = val.slice(1, -1).split(',').map(s => s.trim().replace(/^["']|["']$/g, '')).filter(Boolean);
      } else if (val === '') {
        // 后面是列表
        result[currentKey] = [];
      } else {
        result[currentKey] = val;
      }
    }
  }

  return result;
}
