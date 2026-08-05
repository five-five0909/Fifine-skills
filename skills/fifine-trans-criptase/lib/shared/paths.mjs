// 共享路径解析层：安装根目录与"目标项目根目录"的唯一推导入口。
// 两条主线（转录续接 / 代码检索）与全部脚本都从这里取路径，不再各自反推。
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// 本文件固定位于 <INSTALL_ROOT>/lib/shared/paths.mjs，向上三级即安装根目录。
// 按文件自身位置反推，不写死用户名/盘符，插件装到任意位置（marketplace / 共享目录 / 任意 clone 路径）都成立。
export const INSTALL_ROOT = path.dirname(path.dirname(path.dirname(fileURLToPath(import.meta.url))))
// SKILL_DIR 是 scripts/lib.mjs 历史命名，保留别名做兼容，避免搬迁时到处改名。
export const SKILL_DIR = INSTALL_ROOT

/**
 * "当前目标项目根目录"解析优先级链（用于代码检索 root_path 缺省值等场景）：
 *   显式参数 > 客户端环境变量 > cwd
 * 注意：这里解析的是"用户当前操作的项目"，与 INSTALL_ROOT（trans 自身安装位置）是两个不同概念，不能混用。
 */
export function resolveProjectRoot(explicit) {
    if (explicit) return path.resolve(explicit)
    const envRoot = process.env.CLAUDE_PROJECT_DIR || process.env.CODEX_PROJECT_ROOT
    if (envRoot) return path.resolve(envRoot)
    return process.cwd()
}
