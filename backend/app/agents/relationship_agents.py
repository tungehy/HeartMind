"""关系分析类 Agent：Stage / Score / TurningPoint / Compatibility / Advice / DateReview。

均遵循：LLM 可用则用 LLM，否则回退规则引擎；结论写入 AgentRun 以便追溯。
"""
from __future__ import annotations

from typing import Any

from ..domain.stages import STAGE_LABELS, STATE_LABELS
from ..agents import rule_engine
from ..llm import get_llm

SCORE_DIMS = ["沟通质量", "互动积极度", "兴趣匹配", "价值观匹配", "情绪连接",
              "见面表现", "主动程度", "稳定性", "未来规划匹配", "用户主观满意度"]
COMPAT_DIMS = ["价值观", "生活方式", "兴趣", "城市规划", "婚恋观", "沟通方式",
               "家庭观念", "未来规划"]


class StageAgent:
    name = "StageAgent"

    def __init__(self):
        self.llm = get_llm()

    def judge(self, messages: list[dict], has_date: bool) -> dict[str, Any]:
        metrics = rule_engine.interaction_metrics(messages)
        emotion = rule_engine.emotion_trend(messages)
        if self.llm.available and messages:
            sample = "\n".join(f"{m.get('sender')}: {m.get('content')}" for m in messages[-40:])
            data = self.llm.complete_json(
                f"根据以下聊天记录判断两人关系阶段（STAGE_1刚认识~STAGE_9结束）。"
                f'输出 JSON：{{"stage":"STAGE_x","confidence":0~1,"evidence":["依据"]}}。\n\n{sample}',
                system="你是关系阶段判断助手，只输出JSON。",
            )
            if data and "stage" in data:
                data.setdefault("evidence", [])
                data["state"] = rule_engine.stage_to_state(data["stage"], emotion)
                data["emotion"] = emotion
                return data
        stage, conf, evidence = rule_engine.infer_stage(metrics, len(messages), has_date, emotion)
        return {"stage": stage, "confidence": conf, "evidence": evidence,
                "state": rule_engine.stage_to_state(stage, emotion), "emotion": emotion}


class ScoreAgent:
    name = "ScoreAgent"

    def score(self, messages: list[dict], facts: dict, has_date: bool,
              completeness: float) -> dict[str, Any]:
        metrics = rule_engine.interaction_metrics(messages)
        emotion = rule_engine.emotion_trend(messages)
        pr = metrics.get("person_ratio", 0)
        alen = metrics.get("person_avg_len", 0)

        def clamp(x): return max(20, min(98, round(x)))

        dims = {
            "沟通质量": clamp(50 + alen * 2),
            "互动积极度": clamp(40 + metrics.get("sample_count", 0) * 0.6),
            "兴趣匹配": clamp(55 + len(facts.get("hobbies", {}).get("value", []) or []) * 6),
            "价值观匹配": clamp(50 + (10 if facts.get("values", {}).get("value") else 0)),
            "情绪连接": clamp(70 if emotion == "positive" else 45 if emotion == "negative" else 58),
            "见面表现": clamp(70 if has_date else 40),
            "主动程度": clamp(40 + pr * 60),
            "稳定性": clamp(60 if emotion != "negative" else 42),
            "未来规划匹配": clamp(55 + (15 if facts.get("future_city", {}).get("value") else 0)),
            "用户主观满意度": 60,
        }
        overall = round(sum(dims.values()) / len(dims), 1)
        plus, minus = [], []
        if pr > 0.45:
            plus.append("对方回复积极、参与度较高")
        if alen > 8:
            plus.append("对方消息内容充实")
        if facts.get("hobbies", {}).get("value"):
            plus.append("已识别共同兴趣点")
        if emotion == "negative":
            minus.append("近期情绪偏负面")
        if not has_date:
            minus.append("尚无线下见面记录")
        if completeness < 0.5:
            minus.append("画像数据尚不完整")
        return {
            "dimensions": dims, "overall": overall,
            "trend": "up" if emotion == "positive" else "down" if emotion == "negative" else "stable",
            "plus_factors": plus, "minus_factors": minus,
            "data_completeness": completeness,
            "confidence": round(0.4 + completeness * 0.5, 2),
        }


class TurningPointAgent:
    name = "TurningPointAgent"

    def detect(self, messages: list[dict]) -> list[dict[str, Any]]:
        """规则降级：检测情绪/互动突变。LLM 模式可扩展。"""
        points = []
        emo = rule_engine.emotion_trend(messages)
        if emo == "negative" and len(messages) > 10:
            points.append({
                "title": "检测到可能的关系降温节点",
                "what": "近期聊天中负面/压力类表达增多",
                "why": "基于聊天行为的推断：负面词频上升、互动趋于简短",
                "before": "此前互动较为平稳",
                "after": "回复趋于简短，情绪偏负面",
                "possible_causes": ["工作压力", "生活节奏变化", "沟通误会"],
                "suggestion": "给予空间，避免追问；待情绪缓和后自然关心",
                "evidence": [m.get("content", "")[:50] for m in messages[-5:]],
                "confidence": 0.55,
            })
        return points


class MatchAgent:
    name = "MatchAgent"

    def analyze(self, user_facts: dict, person_facts: dict) -> dict[str, Any]:
        """用户画像 × 对象画像 → 匹配分析。区分 已确认/未知/冲突/AI推测。"""
        confirmed, unknown, conflicts, inferred = [], [], [], []
        dims = {}

        uh = set(user_facts.get("hobbies", {}).get("value", []) or [])
        ph = set(person_facts.get("hobbies", {}).get("value", []) or [])
        shared = sorted(uh & ph)
        dims["兴趣"] = 60 + len(shared) * 10 if (uh or ph) else 0
        if shared:
            confirmed.append(f"共同兴趣：{'、'.join(shared)}")
        elif not ph:
            unknown.append("兴趣")

        for dim, uf, pf in [
            ("城市规划", "future_city", "future_city"),
            ("婚恋观", "relationship_view", "relationship_view"),
            ("价值观", "values", "values"),
            ("家庭观念", "family", "family"),
        ]:
            uv = user_facts.get(uf, {}).get("value")
            pv = person_facts.get(pf, {}).get("value")
            if uv and pv:
                if uv == pv:
                    dims[dim] = 85
                    confirmed.append(f"{dim}一致")
                else:
                    dims[dim] = 45
                    conflicts.append(f"{dim}存在差异（你：{uv} / 对方：{pv}）")
            else:
                dims[dim] = 0
                unknown.append(dim)

        for d in ["生活方式", "沟通方式", "未来规划"]:
            dims.setdefault(d, 0)
            if d not in unknown:
                unknown.append(d)

        known = [v for v in dims.values() if v > 0]
        overall = round(sum(known) / len(known), 1) if known else 0
        confidence = round(len(known) / len(COMPAT_DIMS), 2)
        return {
            "overall": overall, "dimensions": dims,
            "confirmed": confirmed, "unknown": unknown,
            "conflicts": conflicts, "inferred": inferred,
            "confidence": confidence,
            "note": "当前匹配判断可信度受限于未知信息；建议优先了解未知区域。",
        }


class AdviceAgent:
    name = "AdviceAgent"

    def advise(self, stage: str, state: str, facts: dict,
               match: dict, metrics: dict) -> dict[str, Any]:
        stage_label = STAGE_LABELS.get(stage, stage)
        state_label = STATE_LABELS.get(state, state)
        finding, evidence, suggestion, method = "", [], "", ""
        risk, opportunity, timing = "", "", "未来一周"

        unknown_high = [u for u in match.get("unknown", [])]
        if state == "warming":
            finding = "对方近期互动积极，关系处于升温期"
            evidence = ["回复速度与主动开启话题增加"]
            opportunity = "可顺势推进线下互动"
            suggestion = "适当增加线下见面，从共同兴趣切入"
            method = "以共同兴趣发起邀约，而非直接谈关系"
            risk = "避免节奏过快给对方压力"
        elif state == "cooling":
            finding = "近期互动趋于减少，关系有降温迹象"
            evidence = ["回复间隔变长", "主动话题减少"]
            suggestion = "给予空间，降低联系频率，待对方状态缓和"
            method = "以轻松、低压力的方式重新连接"
            risk = "追问关系定位易引发抵触"
            timing = "未来两周内观察"
        elif state == "coldwar":
            finding = "双方处于冷战/僵持状态"
            suggestion = "先真诚沟通化解误会，再评估是否继续"
            method = "以理解和道歉开场，避免讲道理"
            risk = "对立情绪可能加剧"
            timing = "尽快但需真诚"
        elif state == "ended":
            finding = "关系已结束"
            suggestion = "归档保留记录，将精力投入其他关系"
            method = "—"
            risk = "—"
        else:
            finding = "关系处于稳定发展阶段"
            suggestion = "在稳定中逐步加深了解"
            method = "围绕生活方式与价值观自然展开"
            risk = "避免长期停留在表面话题"
            opportunity = "可逐步了解更深层的价值观与规划"

        if unknown_high and state in ("stable", "warming"):
            suggestion += f"；当前值得了解：{'、'.join(unknown_high[:2])}"
        return {
            "current_state": f"{stage_label} / {state_label}",
            "finding": finding, "evidence": evidence, "risk": risk,
            "opportunity": opportunity, "suggestion": suggestion,
            "timing": timing, "method": method,
        }


class DateReviewAgent:
    name = "DateReviewAgent"

    def __init__(self):
        self.llm = get_llm()

    def analyze(self, description: str) -> dict[str, Any]:
        """第一轮：从自然描述中抽取约会信息。"""
        if self.llm.available:
            data = self.llm.complete_json(
                "从这段约会复盘中抽取信息。输出 JSON，字段："
                "location, topics[], events[], person_behavior, user_behavior, "
                "user_feeling, relation_change, new_facts{字段:值}, risks[], highlights[]。"
                f"\n\n描述：{description}",
                system="你是约会复盘分析助手，只输出JSON。",
            )
            if data:
                return data
        # 规则降级
        facts = rule_engine.extract_from_text(description)
        topics = [w for w in ["火锅", "咖啡", "电影", "散步", "工作", "旅游", "大学"] if w in description]
        feeling = "轻松" if any(k in description for k in ["轻松", "开心", "愉快", "不错"]) else "一般"
        return {
            "location": "", "topics": topics, "events": [description[:60]],
            "person_behavior": "", "user_behavior": "", "user_feeling": feeling,
            "relation_change": "轻微升温" if feeling == "轻松" else "平稳",
            "new_facts": {k: v["value"] for k, v in facts.items()},
            "risks": [], "highlights": topics,
        }

    def followup_questions(self, extracted: dict, person_facts: dict) -> list[str]:
        """第二轮：识别仍不确定且值得补充的信息。"""
        qs = []
        if not extracted.get("person_behavior"):
            qs.append("这次见面中，她的情绪和参与度整体如何？")
        if not person_facts.get("future_city", {}).get("value"):
            qs.append("她有没有提到未来的工作或城市规划？")
        if not extracted.get("relation_change") or extracted.get("relation_change") == "平稳":
            qs.append("你感觉这次见面后，她对你的主动程度有没有变化？")
        return qs[:3]

    def summarize(self, extracted: dict) -> dict[str, Any]:
        change = extracted.get("relation_change", "平稳")
        highlights = extracted.get("highlights") or extracted.get("topics") or []
        return {
            "评价": "较好" if change in ("轻微升温", "升温") else "一般",
            "关系变化": change,
            "主要原因": [f"+ {h}" for h in highlights[:2]] or ["+ 正常交流"],
            "需要关注": extracted.get("risks") or ["对未来规划仍缺乏信息"],
            "新增人物信息": [f"{k}：{v}" for k, v in (extracted.get("new_facts") or {}).items()],
            "建议": "下次可以继续围绕兴趣和生活方式展开。",
        }
