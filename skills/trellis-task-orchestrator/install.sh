#!/usr/bin/env bash
# Trellis Task Orchestrator — 安装脚本
# 用法：bash install.sh [--global | --local] [--target agents|claude|codex]
# --global（默认）：安装到 $HOME 下对应宿主的 skills 目录
# --local：安装到当前项目下对应宿主的 skills 目录

set -e

SKILL_NAME="trellis-task-orchestrator"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 解析参数
MODE="global"
TARGET_KIND="agents"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --local)
      MODE="local"
      shift
      ;;
    --global)
      MODE="global"
      shift
      ;;
    --target=*)
      TARGET_KIND="${1#--target=}"
      shift
      ;;
    --target)
      shift
      TARGET_KIND="${1:-agents}"
      [[ $# -gt 0 ]] && shift
      ;;
    *)
      echo "⚠️  忽略未知参数：$1"
      shift
      ;;
  esac
done

case "$TARGET_KIND" in
  agents) SKILLS_ROOT=".agents/skills" ;;
  claude) SKILLS_ROOT=".claude/skills" ;;
  codex) SKILLS_ROOT=".codex/skills" ;;
  *)
    echo "❌ 不支持的 target：$TARGET_KIND（允许：agents / claude / codex）"
    exit 1
    ;;
esac

if [[ "$MODE" == "global" ]]; then
  TARGET_DIR="$HOME/$SKILLS_ROOT/$SKILL_NAME"
else
  # 找项目根（有 .trellis/ 或 .git/ 的目录）
  PROJECT_ROOT="$(pwd)"
  while [[ "$PROJECT_ROOT" != "/" ]]; do
    if [[ -d "$PROJECT_ROOT/.trellis" || -d "$PROJECT_ROOT/.git" ]]; then
      break
    fi
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
  done
  TARGET_DIR="$PROJECT_ROOT/$SKILLS_ROOT/$SKILL_NAME"
fi

echo ""
echo "🌿 Trellis Task Orchestrator 安装器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "安装模式：$MODE"
echo "目标宿主：$TARGET_KIND"
echo "目标路径：$TARGET_DIR"
echo ""

# 备份旧版本
if [[ -d "$TARGET_DIR" ]]; then
  BACKUP="$TARGET_DIR.bak.$(date +%Y%m%d_%H%M%S)"
  echo "⚠️  发现旧版本，备份到：$BACKUP"
  mv "$TARGET_DIR" "$BACKUP"
fi

# 创建目录并复制文件
mkdir -p "$TARGET_DIR/references"
cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/SKILL.md"
cp "$SCRIPT_DIR/references/"*.md "$TARGET_DIR/references/"

echo "✅ 文件安装完成"
echo ""
echo "安装结构："
find "$TARGET_DIR" -type f | sort | sed "s|$TARGET_DIR|  $SKILL_NAME|"
echo ""

# 验证
if [[ -f "$TARGET_DIR/SKILL.md" ]]; then
  echo "✅ SKILL.md 验证通过"
else
  echo "❌ 安装失败，SKILL.md 未找到"
  exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 安装完成！"
echo ""
echo "使用方式："
echo "  在对应宿主工具中直接描述任务即可触发，例如："
echo "  '帮我开发 PISFM 的 BiMamba 双向注意力模块'"
echo "  '修复 spectral_preprocessing.py 的 NaN 问题'"
echo "  '新增 Spring Boot 用户权限管理模块'"
echo ""
echo "  或显式调用（如果你的 Claude Code 版本支持斜杠命令）："
echo "  /trellis-task-orchestrator 你的任务描述"
echo ""
if [[ "$MODE" == "global" ]]; then
  echo "  重启对应宿主工具后生效（全局安装通常需重启）"
else
  echo "  在当前项目中立即生效"
fi
echo ""
