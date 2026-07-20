// hybrid 检索：exact + semantic 的 RRF 融合，复用 scripts/lib.mjs 的 rrfFuse；语义腿失败时纯关键词降级。
import { rrfFuse } from '../../scripts/lib.mjs'
import { exactSearch } from './exact-search.mjs'
import { semanticSearch } from './semantic-search.mjs'

export async function hybridSearch(indexes, queryText, limit = 200) {
    const kwList = exactSearch(indexes, queryText, limit)
    const { hits: vecList, notes, failed } = await semanticSearch(indexes, queryText, limit)

    let ranked
    if (vecList.length && kwList.length) ranked = rrfFuse(vecList, kwList)
    else if (vecList.length) ranked = vecList
    else ranked = kwList.map((h) => ({ ix: h.ix, i: h.i, score: h.score }))

    return { ranked, notes, usedVec: vecList.length > 0, usedKw: kwList.length > 0, degraded: failed === true || vecList.length === 0 }
}
