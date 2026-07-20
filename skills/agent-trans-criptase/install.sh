#!/usr/bin/env bash
# trans 双客户端安装器：Claude Code + Codex CLI 通用（镜像 install.ps1 的逻辑，未在 Linux/macOS 实机验证，
# 逻辑与 Windows 版一一对应，供审查/后续实机测试用）。
#
# 不会移动/复制仓库文件——共享源就是"当前脚本所在目录"，两个客户端都创建 symlink 指向这里。
# 如需搬到统一的 ~/.agent-tools/trans 共享目录，用 scripts/migrate-config.mjs（需交互确认）。
#
# 用法：
#   ./install.sh --clients claude,codex
#   ./install.sh --clients claude
#   ./install.sh --baseUrl https://api.mistral.ai/v1 --apiKey sk-xxx --model mistral-embed
#   ./install.sh --provider local --localDtype q8
#   ./install.sh --skip-index
#   ./install.sh --exact-only
set -e
skill="$(cd "$(dirname "$0")" && pwd)"
server="$skill/mcp/server.mjs"

clients="claude,codex"
skip_index=""
exact_only=""
cfg_args=()

while [ $# -gt 0 ]; do
    case "$1" in
        --clients) clients="$2"; shift 2 ;;
        --skip-index) skip_index=1; shift ;;
        --exact-only) exact_only=1; shift ;;
        --provider|--baseUrl|--apiKey|--model|--rerankModel|--localDtype)
            cfg_args+=("$1" "$2"); shift 2 ;;
        *) shift ;;
    esac
done

echo "trans 安装器 —— 共享源目录: $skill"

new_skill_link() {
    target="$1"
    src="$2"
    mkdir -p "$(dirname "$target")"
    if [ -L "$target" ]; then
        current="$(readlink "$target")"
        if [ "$current" = "$src" ]; then
            echo "  = 已存在且指向正确: $target"
            return
        fi
        echo "  ⚠ $target 已是链接但指向别处 ($current)，重建为指向当前仓库"
        rm -f "$target"
    elif [ -e "$target" ]; then
        echo "  ⚠ $target 已存在且是普通目录（非本安装器创建的链接），跳过，不覆盖用户数据"
        return
    fi
    ln -s "$src" "$target"
    echo "  ✓ 创建链接: $target -> $src"
}

install_claude() {
    new_skill_link "$HOME/.claude/skills/trans" "$skill"
    # 不额外跑 claude mcp add：Skill 目录自带 .mcp.json，Claude Code 发现 Skill 时会自动把它注册成
    # plugin 作用域的 MCP server（自动 Connected）。之前这里还跑一遍 `claude mcp add --scope user`，
    # 实测会跟 plugin 作用域的自动注册产生"同一个 name 多 scope 不同 endpoint"的冲突提示，去掉即根治。
    if command -v claude >/dev/null 2>&1; then
        echo "  ✓ Claude 会在下次发现 Skill 目录时自动注册 MCP（plugin 作用域，无需额外命令）"
    else
        echo "  ⚠ 未找到 claude CLI，跳过（不影响 Codex 侧安装）。装好 Claude Code 后 Skill 会自动生效，无需手动注册 MCP"
    fi
}

install_codex() {
    new_skill_link "$HOME/.agents/skills/trans" "$skill"
    if command -v codex >/dev/null 2>&1; then
        if codex mcp add trans -- node "$server" >/dev/null 2>&1; then
            echo "  ✓ Codex MCP 已注册"
        else
            echo "  ⚠ Codex MCP 注册失败（可能已注册过）。手动执行：codex mcp add trans -- node \"$server\""
        fi
    else
        echo "  ⚠ 未找到 codex CLI，跳过 MCP 注册（不影响 Claude 侧安装）。装好后手动执行："
        echo "    codex mcp add trans -- node \"$server\""
    fi
}

# 1. 配置
if [ -n "$exact_only" ]; then
    node "$skill/scripts/write-config.mjs" --provider api --apiKey ''
    echo "仅关键词模式：跳过 embedding 配置，semantic/hybrid 不可用，exact 立即可用"
else
    node "$skill/scripts/write-config.mjs" "${cfg_args[@]}"
fi

# 2. 逐客户端安装：互不阻断
IFS=',' read -ra CLIENT_LIST <<< "$clients"
for c in "${CLIENT_LIST[@]}"; do
    case "$c" in
        claude) echo ""; echo "[Claude Code]"; install_claude ;;
        codex) echo ""; echo "[Codex CLI]"; install_codex ;;
        *) echo "未知客户端: $c（支持 claude / codex）" ;;
    esac
done

# 3. 首次自检：验证 MCP JSON-RPC、embedding 配置，并后台启动适合当前配置的初始索引。
bootstrap_args=("$skill/scripts/bootstrap.mjs" --clients "$clients")
if [ -n "$skip_index" ]; then bootstrap_args+=(--no-index); fi
node "${bootstrap_args[@]}"

echo ""
echo "── 安装完成 ──"
echo "  共享源目录   : $skill"
echo "  MCP Server   : $server"
echo "  Claude Skill : $HOME/.claude/skills/trans"
echo "  Codex Skill  : $HOME/.agents/skills/trans"
echo "  验证         : node scripts/doctor.mjs"
echo "  卸载         : ./uninstall.sh --clients claude,codex        （加 --purge 连索引/配置一起删）"
