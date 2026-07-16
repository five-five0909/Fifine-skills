// 代码检索子系统安全边界：root_path / path 校验，防路径穿越与符号链接逃逸。
import fs from 'node:fs'
import path from 'node:path'

function withinRoot(resolvedPath, root) {
    const r = path.resolve(root)
    return resolvedPath === r || resolvedPath.startsWith(r + path.sep)
}

/**
 * 校验路径落在 allowedRoots 内（allowedRoots 为空数组 = 不限制，调用方需在文档中提示风险）。
 * 同时校验符号链接真实落点（若路径已存在），拒绝越界逃逸。返回规范化后的绝对路径。
 */
export function assertPathAllowed(targetPath, allowedRoots = []) {
    const resolved = path.resolve(targetPath)
    if (allowedRoots.length > 0) {
        const ok = allowedRoots.some((root) => withinRoot(resolved, root))
        if (!ok) throw new Error(`路径 ${resolved} 不在 allowedRoots 范围内：${JSON.stringify(allowedRoots)}`)
    }
    if (fs.existsSync(resolved)) {
        let real
        try { real = fs.realpathSync(resolved) } catch { real = resolved }
        if (allowedRoots.length > 0) {
            const okReal = allowedRoots.some((root) => withinRoot(real, root))
            if (!okReal) throw new Error(`路径 ${resolved} 的真实位置 ${real} 逃逸出 allowedRoots`)
        }
    }
    return resolved
}

/** 校验 relOrAbs（相对或绝对）解析后仍落在 root 内，拒绝 ".." 穿越。返回规范化绝对路径。 */
export function assertNoTraversal(root, relOrAbs) {
    const resolvedRoot = path.resolve(root)
    const full = path.isAbsolute(relOrAbs) ? path.resolve(relOrAbs) : path.resolve(resolvedRoot, relOrAbs)
    if (full !== resolvedRoot && !full.startsWith(resolvedRoot + path.sep)) {
        throw new Error(`路径穿越: ${relOrAbs} 逃逸出 ${resolvedRoot}`)
    }
    return full
}
