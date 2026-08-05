#!/usr/bin/env bash
# trans 双客户端卸载器（镜像 uninstall.ps1 逻辑，未在 Linux/macOS 实机验证）。
# 默认只移除 Skill 链接 + MCP 注册，保留配置与索引数据。--purge 才删除配置/索引，会先列出路径并要求确认。
#
# 用法：
#   ./uninstall.sh --clients claude,codex
#   ./uninstall.sh --clients claude,codex --purge
set -e
skill="$(cd "$(dirname "$0")" && pwd)"
clients="claude,codex"
purge=""

while [ $# -gt 0 ]; do
    case "$1" in
        --clients) clients="$2"; shift 2 ;;
        --purge) purge=1; shift ;;
        *) shift ;;
    esac
done

remove_skill_link() {
    target="$1"
    if [ ! -e "$target" ] && [ ! -L "$target" ]; then
        echo "  = 不存在，跳过: $target"
        return
    fi
    if [ -L "$target" ]; then
        rm -f "$target"
        echo "  ✓ 已移除链接: $target"
    else
        echo "  ⚠ $target 不是本安装器创建的链接（是普通目录），跳过，不删除"
    fi
}

IFS=',' read -ra CLIENT_LIST <<< "$clients"
for c in "${CLIENT_LIST[@]}"; do
    case "$c" in
        claude)
            echo ""; echo "[Claude Code]"
            remove_skill_link "$HOME/.claude/skills/trans"
            command -v claude >/dev/null 2>&1 && (claude mcp remove trans >/dev/null 2>&1 && echo "  ✓ 已移除 Claude MCP 注册" || echo "  ⚠ 移除 Claude MCP 注册失败（可能本就未注册）")
            ;;
        codex)
            echo ""; echo "[Codex CLI]"
            remove_skill_link "$HOME/.codex/skills/trans"
            command -v codex >/dev/null 2>&1 && (codex mcp remove trans >/dev/null 2>&1 && echo "  ✓ 已移除 Codex MCP 注册" || echo "  ⚠ 移除 Codex MCP 注册失败（可能本就未注册）")
            ;;
        *) echo "未知客户端: $c（支持 claude / codex）" ;;
    esac
done

if [ -n "$purge" ]; then
    targets=()
    for p in "$skill/embed-config.json" "$skill/config/config.json" "$skill/index" "$skill/data"; do
        [ -e "$p" ] && targets+=("$p")
    done
    if [ ${#targets[@]} -eq 0 ]; then
        echo ""
        echo "--purge：没有发现配置/索引数据，无需清理"
    else
        echo ""
        echo "--purge：将删除以下路径（配置 + 索引数据）："
        for t in "${targets[@]}"; do echo "  - $t"; done
        read -r -p "确认删除？输入 yes 继续: " confirm
        if [ "$confirm" = "yes" ]; then
            for t in "${targets[@]}"; do rm -rf "$t"; done
            echo "  ✓ 已清理"
        else
            echo "  已取消，未删除任何数据"
        fi
    fi
else
    echo ""
    echo "配置与索引数据已保留（默认行为）。如需连数据一起删除，加 --purge。"
fi
