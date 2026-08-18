"""Profile 引擎：字段管理、完整度、事实/推断分离、冲突检测。

对应 V2：第十节(Confidence)、第十一节(收敛)、原则二(事实/推断分离)、
原则三(未知也是数据)、原则四(持续演化)。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..domain.stages import FIELD_META, information_value, field_timing, field_method


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_field(
    value: Any = None,
    source: str = "user",
    confidence: float = 0.0,
    status: str = "unknown",
    evidence: list | None = None,
    stage: str = "STAGE_1",
) -> dict:
    """构建一个 ProfileField（V2 第十节结构）。"""
    return {
        "value": value,
        "source": source,                 # user/conversation/date_review/ai_inferred
        "confidence": round(confidence, 3),
        "status": status,                 # confirmed/inferred/unknown/conflicting/outdated
        "evidence": evidence or [],
        "last_updated": now_iso(),
        "timing": field_timing(_field_key(value), stage) if isinstance(value, str) else "unknown",
        "information_value": 0.0,
    }


def _field_key(_: Any) -> str:
    return ""  # timing 由调用方按字段名计算，这里仅占位


def get_field(facts: dict, name: str, stage: str) -> dict:
    """读取字段；不存在则返回带时机/信息价值的 unknown 字段。"""
    if name in facts and isinstance(facts[name], dict):
        f = dict(facts[name])
        f["timing"] = field_timing(name, stage)
        f["information_value"] = information_value(name, stage, has_evidence=bool(f.get("evidence")))
        return f
    return {
        "value": None,
        "source": "user",
        "confidence": 0.0,
        "status": "unknown",
        "evidence": [],
        "last_updated": now_iso(),
        "timing": field_timing(name, stage),
        "information_value": information_value(name, stage),
    }


def set_field(facts: dict, name: str, value: Any, source: str, confidence: float,
              status: str, stage: str, evidence: list | None = None) -> tuple[dict, bool]:
    """写入字段，返回 (新 facts, 是否发生冲突)。

    冲突处理（V2 第十节）：不同来源的非空值不一致 → 标记 conflicting，不静默覆盖。
    """
    facts = dict(facts)
    existing = facts.get(name)
    conflict = False
    if existing and existing.get("value") not in (None, "", []) and existing["value"] != value:
        # 来源不同且值不同 → 冲突；同源同值 → 更新
        if existing.get("source") != source:
            conflict = True
            facts[name] = {
                **existing,
                "status": "conflicting",
                "conflict_with": {"value": value, "source": source, "evidence": evidence or []},
                "last_updated": now_iso(),
            }
            return facts, conflict

    facts[name] = {
        "value": value,
        "source": source,
        "confidence": round(confidence, 3),
        "status": status,
        "evidence": (evidence or []) + (existing.get("evidence", []) if existing else []),
        "last_updated": now_iso(),
        "timing": field_timing(name, stage),
        "information_value": information_value(name, stage, has_evidence=bool(evidence)),
    }
    return facts, conflict


def mark_unknown(facts: dict, name: str, stage: str, source: str = "user") -> dict:
    """用户选择"不知道"（V2 第九节）：记录 unknown，不无限追问。"""
    facts = dict(facts)
    facts[name] = {
        "value": None, "source": source, "confidence": 0.0, "status": "unknown",
        "evidence": [], "last_updated": now_iso(),
        "timing": field_timing(name, stage),
        "information_value": information_value(name, stage),
    }
    return facts


def completeness(facts: dict, stage: str) -> float:
    """画像完整度：当前阶段"适合了解"的字段中已确认/推断的比例。

    完整 ≠ 所有字段已知；= 当前阶段该了解的已基本覆盖（V2 第三十二节）。
    """
    from ..domain.stages import STAGE_DEPTH
    depth = STAGE_DEPTH.get(stage, 1)
    relevant = [k for k, m in FIELD_META.items() if m["min_depth"] <= depth + 1]
    if not relevant:
        return 0.0
    known = sum(1 for k in relevant
                if facts.get(k, {}).get("status") in ("confirmed", "inferred"))
    return round(known / len(relevant), 3)


def summarize(facts: dict, stage: str) -> dict:
    """画像小结（V2 第十一节）：已确认 / 初步推断 / 未知 / 当前最值得了解。"""
    confirmed, inferred, unknown = [], [], []
    for name, meta in FIELD_META.items():
        f = facts.get(name)
        label = meta["label"]
        if f and f.get("status") == "confirmed":
            confirmed.append({"field": name, "label": label, "value": f.get("value")})
        elif f and f.get("status") == "inferred":
            inferred.append({"field": name, "label": label, "value": f.get("value"),
                             "confidence": f.get("confidence")})
        else:
            unknown.append({
                "field": name, "label": label,
                "importance": meta["importance"],
                "timing": field_timing(name, stage),
                "information_value": information_value(name, stage),
                "method": field_method(name),
            })
    # 当前最值得了解：现阶段高价值且时机为 now/soon
    worth_now = sorted(
        [u for u in unknown if u["timing"] in ("now", "soon")],
        key=lambda x: x["information_value"], reverse=True,
    )[:3]
    defer = [u for u in unknown if u["timing"] == "later" and u["importance"] >= 0.8]
    return {
        "confirmed": confirmed,
        "inferred": inferred,
        "unknown": unknown,
        "worth_now": worth_now,
        "defer": defer,
        "completeness": completeness(facts, stage),
    }
