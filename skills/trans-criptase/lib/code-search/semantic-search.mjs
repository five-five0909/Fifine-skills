// semantic 检索：查询向量 · 索引向量点积排序（向量已归一化，点积=余弦相似度），复用 scripts/lib.mjs 的 embedBatch/normalize。
import { embedBatch, normalize } from '../../scripts/lib.mjs'

export async function semanticSearch(indexes, queryText, limit = 200) {
    const vecIndexes = indexes.filter((ix) => ix.fa)
    if (!vecIndexes.length) return { hits: [], notes: ['索引无向量（纯关键词索引），填好 key 后 force 重建可升级'] }

    const notes = []
    let qv
    try {
        qv = normalize(Float32Array.from((await embedBatch([queryText], true))[0]))
    } catch (e) {
        return { hits: [], notes: [`向量检索不可用: ${String(e.message).slice(0, 160)}`], failed: true }
    }

    const hits = []
    for (const ix of vecIndexes) {
        const dims = ix.state.dims
        if (dims !== qv.length) { notes.push(`${ix.enc} 索引维度 ${dims} ≠ 当前查询维度 ${qv.length}，已跳过（embedding 模型换过？force 重建）`); continue }
        for (let i = 0; i < ix.n; i++) {
            let s = 0
            const off = i * dims
            for (let d = 0; d < dims; d++) s += ix.fa[off + d] * qv[d]
            hits.push({ ix, i, score: s })
        }
    }
    hits.sort((a, b) => b.score - a.score)
    return { hits: hits.slice(0, limit), notes }
}
