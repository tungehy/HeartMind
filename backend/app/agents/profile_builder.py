"""Profile Builder Agent（V2 第三十一节）—— HeartMind 最核心的 Agent。

Loop：读 Profile → 读证据 → 读 Stage → 识别未知 → 计算信息价值 →
      过滤不适合 → 选下一问 → 等用户输入 → 解析 → 更新 → 重算完整度 → 判收敛。

目标不是填满表格，而是在当前关系阶段以自然方式降低认知不确定性（原则八）。
LLM 可用时用 LLM 抽取与生成问题；否则回退规则引擎。
"""
from __future__ import annotations

from typing import Any

from ..domain.stages import (
    FIELD_META, STAGE_LABELS, information_value, field_timing, field_method,
)
from ..services import profile_service as ps
from ..agents import rule_engine
from ..llm import get_llm

# 系统状态：collecting / clarifying / converging / paused / completed
STOP_COMPLETENESS = 0.75


class ProfileBuilderAgent:
    name = "ProfileBuilderAgent"

    def __init__(self, owner_type: str = "person"):
        self.owner_type = owner_type  # person / user
        self.llm = get_llm()

    # ---------- 摄入：从自然语言/聊天建立或更新画像 ----------
    def ingest_text(self, facts: dict, text: str, stage: str,
                    source: str = "user") -> dict[str, Any]:
        extracted = self._extract(text)
        conflicts = []
        for name, payload in extracted.items():
            facts, conflict = ps.set_field(
                facts, name, payload["value"], source=source,
                confidence=payload.get("confidence", 0.9 if source == "user" else 0.75),
                status="confirmed" if source == "user" else "inferred",
                stage=stage, evidence=payload.get("evidence", [text[:60]]),
            )
            if conflict:
                conflicts.append(name)
        return {"facts": facts, "extracted": list(extracted.keys()), "conflicts": conflicts}

    def _extract(self, text: str) -> dict[str, Any]:
        if self.llm.available:
            prompt = (
                "从下面这段对一个人的描述中，抽取画像字段。"
                f"可选字段：{', '.join(FIELD_META.keys())}。"
                "只抽取文本中明确出现的信息，不要推测。"
                '输出 JSON：{"字段名": {"value": 值, "evidence": ["原文片段"]}}。\n\n'
                f"描述：{text}"
            )
            data = self.llm.complete_json(prompt, system="你是信息抽取助手，只输出JSON。")
            if data:
                return {k: v for k, v in data.items() if k in FIELD_META}
        return rule_engine.extract_from_text(text)

    # ---------- 生成下一轮问题 ----------
    def next_questions(self, facts: dict, stage: str, limit: int = 3) -> dict[str, Any]:
        summary = ps.summarize(facts, stage)
        candidates = [u for u in summary["unknown"] if u["timing"] in ("now", "soon")]
        candidates.sort(key=lambda x: x["information_value"], reverse=True)
        picked = candidates[:limit]

        questions = []
        for c in picked:
            meta = FIELD_META[c["field"]]
            questions.append({
                "field": c["field"],
                "label": c["label"],
                "question": self._phrase_question(c["field"], c["label"]),
                "method": c["method"],
                "information_value": c["information_value"],
                "timing": c["timing"],
                "importance": meta["importance"],
                "options": self._options_for(c["field"]),
            })
        return {
            "stage": stage,
            "stage_label": STAGE_LABELS.get(stage, stage),
            "questions": questions,
            "completeness": summary["completeness"],
            "should_converge": self._should_converge(summary),
        }

    def _phrase_question(self, field: str, label: str) -> str:
        method = field_method(field)
        if method == "直接询问":
            return f"方便了解一下她的{label}吗？"
        if method == "观察行为" or method == "约会观察":
            return f"关于她的{label}，建议通过{method}自然了解，你目前有什么观察吗？"
        if method == "AI从聊天中推断":
            return f"关于她的{label}，我可以从聊天中推断；你也可以直接补充。"
        if method == "等待未来事件":
            return f"{label}属于较敏感信息，建议等待合适时机，暂不强求。"
        return f"关于她的{label}，你了解多少？（可回答 / 不知道 / 以后再说）"

    def _options_for(self, field: str) -> list[str]:
        """AI 提供的候选答案（1~3 个真实选项）。

        不再混入"不知道/以后再说/跳过"这类否定项 —— 那些统一由前端一个
        「跳过」按钮承担。这里只给出对该字段最可能的回答候选。
        """
        presets = {
            "personality": ["开朗外向", "慢热内向", "理性沉稳"],
            "hobbies": ["旅行", "美食", "运动", "阅读", "音乐"],
            "relationship_view": ["重视稳定", "顺其自然", "事业优先"],
            "city": ["上海", "杭州", "南通"],
            "weekend_life": ["宅家休息", "出门探店", "户外运动"],
            "consumption": ["理性节俭", "适度享受", "品质优先"],
            "future_city": ["留在本地", "去一线城市", "还没想好"],
            "chat_style": ["秒回话痨", "慢热简短", "看心情"],
            "lifestyle": ["规律健康", "自由随性", "忙碌充实"],
            "music_taste": ["流行", "民谣", "古典"],
            "food_taste": ["清淡", "重口麻辣", "甜食"],
        }
        return presets.get(field, [])

    def _should_converge(self, summary: dict) -> bool:
        """收敛条件（V2 第三十二节）：完整度够 + 高价值未知减少。"""
        if summary["completeness"] >= STOP_COMPLETENESS:
            return True
        high_value_left = [u for u in summary["worth_now"] if u["information_value"] > 0.6]
        return summary["completeness"] >= 0.5 and len(high_value_left) == 0

    # ---------- 处理用户回答 ----------
    def answer(self, facts: dict, field: str, answer: Any, stage: str) -> dict[str, Any]:
        if answer in ("不知道", "以后再说", "跳过", None, ""):
            facts = ps.mark_unknown(facts, field, stage)
            return {"facts": facts, "recorded": "unknown"}
        facts, conflict = ps.set_field(
            facts, field, answer, source="user", confidence=0.95,
            status="confirmed", stage=stage, evidence=[f"用户补充：{answer}"],
        )
        return {"facts": facts, "recorded": "confirmed", "conflict": conflict}

    # ---------- 小结 ----------
    def summarize(self, facts: dict, stage: str) -> dict[str, Any]:
        return ps.summarize(facts, stage)
