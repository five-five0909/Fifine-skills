#!/usr/bin/env python3
"""
grill.py — Grill Me 会话记录器
把每次 grill 过程存到当前项目的 .claude/.grill-me/YYYY-MM-DD/HH-MM-SS.md
"""
import sys, argparse
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode',     required=True, help='A / B / D')
    parser.add_argument('--topic',    required=True, help='本次 grill 的主题')
    parser.add_argument('--findings', default='',    help='发现的主要问题，逗号分隔')
    parser.add_argument('--outcome',  default='',    help='结论或下一步行动')
    args = parser.parse_args()

    now       = datetime.now()
    date_str  = now.strftime('%Y-%m-%d')
    time_str  = now.strftime('%H-%M-%S')
    mode_name = {'A': '方案审查', 'B': '执行任务', 'D': '工作流审计'}.get(args.mode, args.mode)

    # 存到当前工作目录下的 .claude/.grill-me/
    out_dir = Path.cwd() / '.claude' / '.grill-me' / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'{time_str}.md'

    findings_list = [f.strip() for f in args.findings.split(',') if f.strip()]
    findings_md   = '\n'.join(f'- {f}' for f in findings_list) if findings_list else '- 无'

    content = f"""# Grill 记录

- **时间**：{now.strftime('%Y-%m-%d %H:%M:%S')}
- **模式**：{mode_name}
- **主题**：{args.topic}

## 发现的问题
{findings_md}

## 结论 / 下一步
{args.outcome or '未记录'}
"""

    out_file.write_text(content, encoding='utf-8')
    print(f'已记录：{out_file}')


if __name__ == '__main__':
    main()
