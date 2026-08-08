from __future__ import annotations
from schema import STAGE_ORDER

def resolve_mode(request_text: str, explicit_mode: str | None = None):
    if explicit_mode and explicit_mode != 'auto':
        mode = explicit_mode
    else:
        t = (request_text or '').lower()
        if any(k in t for k in ['完整', '全部', '全流程', 'full']):
            mode = 'full'
        elif any(k in t for k in ['hook', 'idea', '卡片', '实验卡', '写作卡']):
            mode = 'hook-pass'
        else:
            mode = 'scan'
    if mode == 'scan':
        stages = STAGE_ORDER[:5]
    else:
        stages = STAGE_ORDER
    return mode, stages
