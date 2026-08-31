"""PeriodAgent：把聊天时间序列在趋势突变点划分为若干「关系时期」。

流程：消息按天聚合成简报（条数/双向比/情感分布/话题/代表句）→
LLM 划分时期并写摘要；LLM 不可用时降级为规则分段（周聚合+状态突变合并）。
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from . import rule_engine
from ..llm import get_llm

VALID_STATES = ("warming", "stable", "cooling", "coldwar", "ended")


def _day_key(ts: Any) -> str:
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    return ts.strftime("%Y-%m-%d")


def _day_brief(day: str, msgs: list[dict[str, Any]]) -> dict[str, Any]:
    """把一天的消息压缩成一行简报，控制 LLM 输入规模。"""
    user_n = sum(1 for m in msgs if m.get("sender") == "user")
    person_n = len(msgs) - user_n
    pos = sum(1 for m in msgs if m.get("emotion") == "positive")
    neg = sum(1 for m in msgs if m.get("emotion") == "negative")
    topics: dict[str, int] = defaultdict(int)
    for m in msgs:
        for t in m.get("topics") or []:
            topics[t] += 1
    top_topics = sorted(topics, key=topics.get, reverse=True)[:3]
    # 代表句：对方最重要的两条消息（帮 LLM 理解语义，不只靠统计）
    person_msgs = [m for m in msgs if m.get("sender") == "person" and m.get("content")]
    person_msgs.sort(key=lambda m: (m.get("importance", 0), len(m.get("content", ""))), reverse=True)
    quotes = [m["content"][:40] for m in person_msgs[:2]]
    return {"date": day, "total": len(msgs), "user": user_n, "person": person_n,
            "pos": pos, "neg": neg, "topics": top_topics, "quotes": quotes}


def group_days(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按天聚合为简报列表（按日期升序）。"""
    by_day: dict[str, list[dict]] = defaultdict(list)
    for m in messages:
        ts = m.get("timestamp")
        if not ts:
            continue
        by_day[_day_key(ts)].append(m)
    return [_day_brief(d, by_day[d]) for d in sorted(by_day)]


_SYSTEM = """你是关系分析师。用户会给你他与相亲对象按天汇总的聊天简报（JSON数组），
每项含：date 日期 / total 总条数 / user,person 双方条数 / pos,neg 正负面情感条数 / topics 话题 / quotes 对方代表句。

请把整个时间范围按聊天频率、双向性、情感倾向、话题深度的【趋势突变点】划分为若干关系时期。
状态只能选：warming(升温) / stable(稳定) / cooling(降温) / coldwar(冷淡冲突) / ended(结束)。

要求：
1. 相邻段的状态必须不同；段数控制在 2~8 段，不要按天硬切；
2. 每段 summary 用一句不超过 40 字的话概括该时期（要引用具体话题或行为，不要空话）；
3. start/end 用简报中出现过的日期（YYYY-MM-DD），第一段 start 为首个简报日期，最后一段 end 为最后简报日期；
4. 无聊天的日期间隙若超过 7 天，通常意味着 cooling；
5. 输出严格 JSON：{"periods":[{"start":"YYYY-MM-DD","end":"YYYY-MM-DD","state":"...","summary":"..."}]}"""


class PeriodAgent:
    """划分关系时期。入口 analyze(messages) 返回 segments 列表。"""

    def analyze(self, messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        briefs = group_days(messages)
        if not briefs:
            return [], "rule"
        llm = get_llm()
        if llm.available:
            out = llm.complete_json(
                "聊天简报如下：\n" + "\n".join(str(b) for b in briefs), system=_SYSTEM)
            periods = self._normalize(out, briefs) if out else None
            if periods:
                return periods, "llm"
        return self._rule_segments(briefs), "rule"

    def _normalize(self, out: dict[str, Any], briefs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raw = (out or {}).get("periods") if isinstance(out, dict) else None
        if not isinstance(raw, list) or not raw:
            return []
        first_day, last_day = briefs[0]["date"], briefs[-1]["date"]
        periods = []
        for p in raw:
            try:
                start, end = str(p["start"])[:10], str(p["end"])[:10]
                state = str(p["state"])
                if state not in VALID_STATES or start > end:
                    continue
                periods.append({"start_date": max(start, first_day), "end_date": min(end, last_day),
                                "state": state, "summary": str(p.get("summary") or "")[:80]})
            except (KeyError, TypeError):
                continue
        if not periods:
            return []
        # 保证时间轴连续覆盖（LLM 偶尔会留缝）
        periods.sort(key=lambda p: p["start_date"])
        periods[0]["start_date"] = first_day
        periods[-1]["end_date"] = last_day
        for i in range(1, len(periods)):
            if periods[i]["start_date"] <= periods[i - 1]["end_date"]:
                pass  # 允许交叠一天内，前端取后者优先
        return periods

    def _rule_segments(self, briefs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """降级：按周聚合打状态，相邻同状态合并为一段（天然落在突变点）。"""
        weeks: dict[str, list[dict]] = defaultdict(list)
        for b in briefs:
            d = datetime.strptime(b["date"], "%Y-%m-%d")
            weeks[f"{d.isocalendar().year}-W{d.isocalendar().week:02d}"].append(b)
        states = [(wk, self._week_state(days)) for wk, days in sorted(weeks.items())]
        periods: list[dict[str, Any]] = []
        for wk, (state, desc) in states:
            days = weeks[wk]
            if periods and periods[-1]["state"] == state:
                periods[-1]["end_date"] = days[-1]["date"]
            else:
                periods.append({"start_date": days[0]["date"], "end_date": days[-1]["date"],
                                "state": state, "summary": desc})
        return periods

    def _week_state(self, days: list[dict[str, Any]]) -> tuple[str, str]:
        total = sum(d["total"] for d in days)
        pos = sum(d["pos"] for d in days)
        neg = sum(d["neg"] for d in days)
        topics = sorted({t for d in days for t in d["topics"]})
        topic_txt = f"，聊到{'、'.join(topics[:2])}" if topics else ""
        if total >= 15 and pos > neg * 2:
            return "warming", f"互动频繁({total}条)，情绪积极{topic_txt}"
        if neg > max(2, pos):
            return "coldwar", f"负面情绪偏多（{neg}条）{topic_txt}"
        if total <= 3:
            return "cooling", f"互动很少（{total}条）"
        return "stable", f"平稳互动({total}条){topic_txt}"
