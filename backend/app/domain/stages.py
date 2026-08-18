"""Relationship Stage Model（V2 第三节）+ 信息价值模型（第四~八节）。

阶段允许反复变化，不做严格线性状态机。
信息价值是 Relationship Context 的动态函数，而非字段静态属性。
"""
from __future__ import annotations

# 关系阶段
STAGES = [
    "STAGE_0",  # 尚未认识
    "STAGE_1",  # 刚认识
    "STAGE_2",  # 初步了解
    "STAGE_3",  # 持续互动
    "STAGE_4",  # 关系升温
    "STAGE_5",  # 暧昧/互有好感
    "STAGE_6",  # 稳定交往
    "STAGE_7",  # 深入了解/长期规划
    "STAGE_8",  # 关系降温
    "STAGE_9",  # 关系结束
]
STAGE_LABELS = {
    "STAGE_0": "尚未认识", "STAGE_1": "刚认识", "STAGE_2": "初步了解",
    "STAGE_3": "持续互动", "STAGE_4": "关系升温", "STAGE_5": "暧昧/互有好感",
    "STAGE_6": "稳定交往", "STAGE_7": "深入了解/长期规划", "STAGE_8": "关系降温",
    "STAGE_9": "关系结束",
}

# 关系状态（甘特图颜色）
STATES = ["warming", "stable", "cooling", "coldwar", "ended"]
STATE_LABELS = {
    "warming": "关系升温", "stable": "稳定发展", "cooling": "感情降温",
    "coldwar": "冷战/踩雷", "ended": "已结束",
}
STATE_COLORS = {
    "warming": "#16a34a", "stable": "#2563eb", "cooling": "#d97706",
    "coldwar": "#dc2626", "ended": "#4b5563",
}

# 阶段进度（用于判断"当前适合了解什么"），越大越深入
STAGE_DEPTH = {s: i for i, s in enumerate(STAGES)}


# ---------- 画像字段元数据 ----------
# 每个字段：中文名 / 重要程度(0~1) / 敏感度(0~1) / 建议了解时机(最早阶段深度) / 获取方式
FIELD_META: dict[str, dict] = {
    # 低敏感、刚认识即可了解
    "nickname":      {"label": "称呼",     "importance": 0.4, "sensitivity": 0.05, "min_depth": 1, "method": "直接询问"},
    "age":           {"label": "年龄",     "importance": 0.6, "sensitivity": 0.2,  "min_depth": 1, "method": "直接询问"},
    "city":          {"label": "所在城市", "importance": 0.7, "sensitivity": 0.15, "min_depth": 1, "method": "直接询问"},
    "occupation":    {"label": "职业",     "importance": 0.7, "sensitivity": 0.2,  "min_depth": 1, "method": "直接询问"},
    "hobbies":       {"label": "兴趣爱好", "importance": 0.8, "sensitivity": 0.05, "min_depth": 1, "method": "自然聊天"},
    "weekend_life":  {"label": "周末生活", "importance": 0.7, "sensitivity": 0.05, "min_depth": 1, "method": "自然聊天"},
    "chat_style":    {"label": "聊天偏好", "importance": 0.6, "sensitivity": 0.05, "min_depth": 2, "method": "观察行为"},
    "personality":   {"label": "基础性格", "importance": 0.8, "sensitivity": 0.2,  "min_depth": 2, "method": "AI从聊天中推断"},
    # 中敏感、初步了解后
    "education":     {"label": "学历",     "importance": 0.5, "sensitivity": 0.3,  "min_depth": 2, "method": "自然聊天"},
    "height":        {"label": "身高",     "importance": 0.3, "sensitivity": 0.3,  "min_depth": 2, "method": "自然聊天"},
    "music_taste":   {"label": "音乐品味", "importance": 0.4, "sensitivity": 0.05, "min_depth": 2, "method": "直接询问"},
    "food_taste":    {"label": "饮食偏好", "importance": 0.5, "sensitivity": 0.05, "min_depth": 2, "method": "约会观察"},
    "lifestyle":     {"label": "生活方式", "importance": 0.7, "sensitivity": 0.2,  "min_depth": 3, "method": "约会观察"},
    "work_pressure": {"label": "工作状态", "importance": 0.5, "sensitivity": 0.3,  "min_depth": 3, "method": "自然聊天"},
    # 高敏感、升温后
    "consumption":   {"label": "消费观",   "importance": 0.8, "sensitivity": 0.6,  "min_depth": 4, "method": "约会观察"},
    "family":        {"label": "家庭情况", "importance": 0.8, "sensitivity": 0.6,  "min_depth": 5, "method": "自然聊天"},
    "relationship_view": {"label": "婚恋观", "importance": 0.95, "sensitivity": 0.7, "min_depth": 5, "method": "自然聊天"},
    "future_city":   {"label": "未来城市", "importance": 0.9, "sensitivity": 0.5,  "min_depth": 5, "method": "自然聊天"},
    "values":        {"label": "价值观",   "importance": 0.9, "sensitivity": 0.5,  "min_depth": 5, "method": "约会观察"},
    # 极高敏感、长期交往
    "income":        {"label": "收入",     "importance": 0.6, "sensitivity": 0.9,  "min_depth": 6, "method": "等待未来事件"},
    "assets":        {"label": "资产",     "importance": 0.5, "sensitivity": 0.95, "min_depth": 7, "method": "等待未来事件"},
    "marriage_plan": {"label": "婚姻安排", "importance": 0.9, "sensitivity": 0.8,  "min_depth": 6, "method": "自然聊天"},
    "child_plan":    {"label": "生育计划", "importance": 0.9, "sensitivity": 0.85, "min_depth": 7, "method": "自然聊天"},
    "family_conflict": {"label": "家庭矛盾", "importance": 0.5, "sensitivity": 0.9, "min_depth": 7, "method": "等待未来事件"},
}

TIMING_LABELS = {
    "now": "现在适合了解", "soon": "近期适合了解", "later": "暂缓了解",
    "not_relevant": "暂不相关", "unknown": "未知", "known": "已知",
}


def information_value(field: str, stage: str, has_evidence: bool = False) -> float:
    """Context-aware Information Value（V2 第五、七节）。

    价值 = 重要程度 × 阶段适配度 × 时机惩罚。
    - 阶段越深，高敏感字段价值越高（到了该了解的时候）。
    - 阶段太浅时，高敏感字段价值被压制（现在问太突兀）。
    """
    meta = FIELD_META.get(field)
    if not meta:
        return 0.3
    depth = STAGE_DEPTH.get(stage, 1)
    importance = meta["importance"]
    sensitivity = meta["sensitivity"]
    min_depth = meta["min_depth"]

    # 阶段适配度：达到 min_depth 后随深度上升；未达则打折
    if depth >= min_depth:
        stage_fit = min(1.0, 0.6 + 0.1 * (depth - min_depth))
    else:
        gap = min_depth - depth
        stage_fit = max(0.1, 0.5 - 0.15 * gap)

    # 时机惩罚：阶段太浅时，敏感度越高惩罚越重
    timing_penalty = 1.0
    if depth < min_depth:
        timing_penalty = 1.0 - 0.5 * sensitivity

    value = importance * stage_fit * timing_penalty
    if has_evidence:
        value *= 0.4  # 已有线索，价值下降
    return round(max(0.0, min(1.0, value)), 3)


def field_timing(field: str, stage: str) -> str:
    meta = FIELD_META.get(field)
    if not meta:
        return "unknown"
    depth = STAGE_DEPTH.get(stage, 1)
    if depth >= meta["min_depth"] + 1:
        return "now"
    if depth >= meta["min_depth"]:
        return "soon"
    return "later"


def field_method(field: str) -> str:
    return FIELD_META.get(field, {}).get("method", "自然聊天")
