#!/usr/bin/env python3
"""Hard-coded task type → stage sequence router for dev-done-flow.

Writes .dev-done-flow/manifest.json and prints a TODO list with the
ordered stages. AI must follow this output — never invent its own order.

required=True  → stage cannot be skipped or merged
required=False → AI may skip or merge with adjacent stage,
                 but must record the reason in stages/skipped.md
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# Each stage: (name, required)
STAGE_SEQUENCES: Dict[str, List[Tuple[str, bool]]] = {
    "new-feature": [
        ("goal", True),
        ("context-discovery", True),
        ("requirements", True),
        ("flow-design", True),
        ("technical-design", True),
        ("task-planning", True),
        ("tdd-plan", False),
        ("implementation", True),
        ("verification", True),
        ("release", False),
        ("observability", False),
        ("feedback", False),
        ("iteration", False),
    ],
    "java-backend": [
        ("goal", True),
        ("existing-code-discovery", True),
        ("backend-requirements", True),
        ("business-flow-state-design", True),
        ("java-technical-design", True),
        ("api-db-transaction-design", True),
        ("task-planning", True),
        ("tdd-plan", False),
        ("unit-integration-regression-verification", True),
        ("release", False),
        ("jvm-api-db-observability", False),
        ("iteration", False),
    ],
    "llm-app": [
        ("goal", True),
        ("use-case-discovery", True),
        ("llm-requirements", True),
        ("conversation-flow-design", True),
        ("llm-technical-design", True),
        ("eval-planning", True),
        ("implementation", True),
        ("offline-evaluation", True),
        ("release", False),
        ("llm-observability", False),
        ("bad-case-feedback", False),
        ("iteration", False),
    ],
    "rag": [
        ("goal", True),
        ("use-case-discovery", True),
        ("rag-requirements", True),
        ("retrieval-flow-design", True),
        ("llm-technical-design", True),
        ("eval-planning", True),
        ("implementation", True),
        ("offline-evaluation", True),
        ("release", False),
        ("retrieval-observability", False),
        ("bad-case-feedback", False),
        ("iteration", False),
    ],
    "agent": [
        ("goal", True),
        ("use-case-discovery", True),
        ("agent-requirements", True),
        ("agent-flow-tool-design", True),
        ("llm-technical-design", True),
        ("eval-planning", True),
        ("implementation", True),
        ("offline-evaluation", True),
        ("release", False),
        ("agent-observability", False),
        ("bad-case-feedback", False),
        ("iteration", False),
    ],
    "architecture": [
        ("goal", True),
        ("current-architecture-discovery", True),
        ("problems", True),
        ("architecture-requirements", True),
        ("rfc-technical-design", True),
        ("migration-plan", True),
        ("task-planning", True),
        ("characterization-tests", True),
        ("refactor", True),
        ("regression-verification", True),
        ("release", False),
        ("observability", False),
        ("iteration", False),
    ],
    "refactoring": [
        ("goal", True),
        ("current-code-discovery", True),
        ("problems", True),
        ("refactoring-requirements", True),
        ("technical-design", True),
        ("task-planning", True),
        ("characterization-tests", False),
        ("refactor", True),
        ("regression-verification", True),
        ("release", False),
        ("iteration", False),
    ],
    "bug-diagnosis": [
        ("symptom", True),
        ("triage", True),
        ("reproduction", True),
        ("expected-vs-actual", True),
        ("evidence-collection", True),
        ("root-cause-analysis", True),
        ("failing-test", False),
        ("fix-plan", True),
        ("implementation", True),
        ("regression-test", True),
        ("release", False),
        ("postmortem", False),
    ],
    "performance": [
        ("goal", True),
        ("performance-baseline", True),
        ("profiling", True),
        ("bottleneck-analysis", True),
        ("optimization-design", True),
        ("task-planning", True),
        ("implementation", True),
        ("benchmark-verification", True),
        ("release", False),
        ("performance-observability", False),
        ("iteration", False),
    ],
    "security": [
        ("goal", True),
        ("threat-model", True),
        ("vulnerability-discovery", True),
        ("security-requirements", True),
        ("security-design", True),
        ("task-planning", True),
        ("implementation", True),
        ("security-verification", True),
        ("release", False),
        ("security-observability", False),
        ("iteration", False),
    ],
    "long-running": [
        ("goal", True),
        ("context-discovery", True),
        ("requirements", True),
        ("technical-design", True),
        ("milestone-planning", True),
        ("task-planning", True),
        ("tdd-plan", False),
        ("implementation", True),
        ("verification", True),
        ("release", False),
        ("observability", False),
        ("feedback", False),
        ("iteration", False),
    ],
}

FIRST_QUESTIONS: Dict[str, List[str]] = {
    "new-feature": [
        "这个功能解决的是谁的什么问题？",
        "成功的标准是什么？",
        "有哪些明确的非目标 / 范围外内容？",
        "主流程是什么？最重要的边界情况有哪些？",
    ],
    "java-backend": [
        "用的是什么 Spring 模块结构？涉及哪些 API / DTO / Entity？",
        "会动哪些数据库表？需要 migration 吗？",
        "有没有幂等性、并发、权限、缓存、消息队列相关要求？",
        "需要保护这次变更的测试策略是什么？",
    ],
    "llm-app": [
        "典型输入和理想输出各是什么？",
        "是否需要 RAG / 工具调用 / 结构化输出 / 记忆 / 人工审批？",
        "已知哪些 bad case？",
        "延迟、成本、安全和可观测性约束是什么？",
    ],
    "rag": [
        "知识库数据来源和格式是什么？",
        "典型查询和理想答案各是什么？",
        "已知哪些检索失败 / 幻觉 case？",
        "延迟、成本和可观测性约束是什么？",
    ],
    "agent": [
        "Agent 需要完成什么任务？可以调用哪些工具？",
        "典型输入和期望行为各是什么？",
        "已知哪些 bad case / 失控场景？",
        "延迟、成本、安全和可观测性约束是什么？",
    ],
    "architecture": [
        "当前架构最严重的耦合 / 模块边界问题是什么？",
        "有哪些高风险区域？",
        "缺失哪些测试来保障重构安全？",
        "期望可以量化的改善指标是什么？",
    ],
    "refactoring": [
        "重构目标是什么？想改善可读性、可测性还是性能？",
        "当前最难维护的代码在哪里？",
        "有没有已有测试可以作为回归保护？",
        "重构后如何验证行为没有变化？",
    ],
    "bug-diagnosis": [
        "症状是什么？预期行为 vs 实际行为？",
        "如何稳定复现？影响范围和环境是什么？",
        "有哪些日志、报错、链路追踪或最近变更可以参考？",
        "能写出什么样的最小失败测试来证明这个 bug？",
    ],
    "performance": [
        "性能基线是多少？目标指标是什么（延迟 P99 / 吞吐量等）？",
        "已知的瓶颈或猜测方向是什么？",
        "如何做 profiling？有没有现成的 benchmark？",
        "优化后如何验证不引入回归？",
    ],
    "security": [
        "威胁模型是什么？攻击面在哪里？",
        "已知或怀疑的漏洞是什么？",
        "安全修复的优先级和范围如何界定？",
        "如何验证修复后安全性达标？",
    ],
    "long-running": [
        "这个工程目标的最终交付物是什么？",
        "大致时间线和里程碑是什么？",
        "最高风险的依赖 / 未知点是什么？",
        "如何分解成可独立验证的阶段？",
    ],
}

KEYWORD_ROUTING: Dict[str, List[str]] = {
    "bug-diagnosis": ["bug", "错误", "报错", "exception", "crash", "崩溃", "fix", "修复", "异常", "失败"],
    "java-backend": ["java", "spring", "后端", "jdbc", "jpa", "mybatis", "controller", "service"],
    "rag": ["rag", "retrieval", "检索", "知识库", "向量", "embedding"],
    "agent": ["agent", "智能体", "tool call", "工具调用", "multi-agent", "多智能体"],
    "llm-app": ["llm", "gpt", "prompt", "对话", "聊天", "语言模型", "大模型", "claude", "openai"],
    "architecture": ["architecture", "架构", "模块边界", "解耦", "microservice", "微服务", "拆分"],
    "refactoring": ["refactor", "重构", "重写", "cleanup", "clean up", "优化代码"],
    "performance": ["performance", "性能", "慢", "slow", "latency", "延迟", "throughput", "吞吐"],
    "security": ["security", "安全", "漏洞", "vulnerability", "xss", "sql injection", "csrf"],
    "long-running": ["long-term", "长期", "roadmap", "持续", "ongoing", "季度", "年度"],
}


def detect_task_type(request_text: str) -> str:
    text_lower = request_text.lower()
    for task_type, keywords in KEYWORD_ROUTING.items():
        if any(kw in text_lower for kw in keywords):
            return task_type
    return "new-feature"


def render_todo(stages: List[dict]) -> str:
    lines = ["=== TODO ==="]
    for s in stages:
        status = s["status"]
        name = s["name"]
        req = "" if s["required"] else " [optional]"
        if status == "done":
            marker = "✅"
        elif status == "skipped":
            marker = "⏭ "
        elif status == "in_progress":
            marker = "▶ "
        else:
            marker = "◻ "
        lines.append(f"{marker} {name}{req}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="dev-done-flow 任务类型 → 阶段队列路由")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument(
        "--task-type", default="",
        help=f"任务类型；不提供则从 --request-text 自动推断。可选值：{', '.join(STAGE_SEQUENCES)}",
    )
    parser.add_argument("--request-text", default="", help="用户原始请求；用于自动推断任务类型")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    flow_dir = root / ".dev-done-flow"
    flow_dir.mkdir(parents=True, exist_ok=True)

    task_type = args.task_type.strip()
    if not task_type or task_type not in STAGE_SEQUENCES:
        task_type = detect_task_type(args.request_text)

    stage_defs = STAGE_SEQUENCES[task_type]
    questions = FIRST_QUESTIONS[task_type]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest_path = flow_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["updated_at"] = now
        manifest["request_text"] = args.request_text
        # Preserve existing stage statuses; add new stages if task_type changed
        existing_statuses = {s["name"]: s["status"] for s in manifest.get("stages", [])}
        manifest["stages"] = [
            {
                "name": name,
                "required": req,
                "status": existing_statuses.get(name, "pending"),
            }
            for name, req in stage_defs
        ]
        # Recompute current_stage
        current = next(
            (s["name"] for s in manifest["stages"] if s["status"] == "in_progress"),
            next(
                (s["name"] for s in manifest["stages"] if s["status"] == "pending"),
                manifest["stages"][-1]["name"],
            ),
        )
        manifest["current_stage"] = current
    else:
        stages = [
            {"name": name, "required": req, "status": "pending"}
            for name, req in stage_defs
        ]
        stages[0]["status"] = "in_progress"
        manifest = {
            "task_type": task_type,
            "stages": stages,
            "current_stage": stages[0]["name"],
            "created_at": now,
            "updated_at": now,
            "request_text": args.request_text,
        }

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"task_type={task_type}")
    print(f"stage_count={len(manifest['stages'])}")
    print(f"current_stage={manifest['current_stage']}")
    print(f"manifest={manifest_path}")
    print()
    print(render_todo(manifest["stages"]))
    print()
    print("=== First-stage questions ===")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
    print()
    print("[NOTE] optional 阶段：AI 可在判断后跳过或合并，但必须将原因写入 stages/skipped.md")


if __name__ == "__main__":
    main()
