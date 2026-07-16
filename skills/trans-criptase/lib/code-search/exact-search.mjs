// exact 检索：子串/分词命中打分，复用 scripts/lib.mjs 的 keywordScores（对 meta.text 通用，与转录索引共用同一算法）。
import { keywordScores } from '../../scripts/lib.mjs'

export function exactSearch(indexes, queryText, limit = 200) {
    return keywordScores(queryText, indexes).slice(0, limit).map((h) => ({ ix: h.ix, i: h.i, score: h.kw }))
}
