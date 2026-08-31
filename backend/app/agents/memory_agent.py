"""MemoryAgent：从聊天中抽取值得长期记住的信息。LLM 优先，规则降级。

旧规则版问题：关键词（"我最近""约"）命中大量闲聊，且 importance 写死。
LLM 版只保留对「了解这个人 / 推进关系」有真实价值的信息，宁缺毋滥。
"""
from __future__ import annotations

from typing import Any

from . import rule_engine
from ..llm import get_llm

CATEGORIES = ("preference", "promise", "fact", "boundary", "plan")
_MAX_CHARS = 12000  # 控制 LLM 输入规模

_SYSTEM = """你在分析用户与相亲对象的微信聊天记录。请只从【对方的消息】中抽取值得长期记住的信息。

只抽取对「了解这个人」或「推进关系」有真实价值的：
- preference：明确的喜好/厌恶（"我最讨厌香菜"，而非"我最近在追剧"这类随口一提）
- fact：个人事实（家庭成员、工作变动、健康、住处、宠物、重要经历）
- promise：承诺与约定（确定要做的具体事，而非"一起"这种虚词）
- plan：未来计划（旅行、考试、跳槽等有明确意向的）
- boundary：边界与雷区（明确表达过介意/不接受的事）

不要抽取：寒暄、表情包回复、无信息量的闲聊、单纯附和。
content 用原文精炼（≤50字），importance 按信息量打 0.6~1.0，低于 0.6 的不要输出，最多 15 条。
输出严格 JSON：{"memories":[{"content":"...","category":"...","importance":0.8}]}"""


class MemoryAgent:
    def analyze(self, messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        person_msgs = [m for m in messages
                       if m.get("sender") == "person" and (m.get("content") or "").strip()]
        if not person_msgs:
            return [], "rule"
        llm = get_llm()
        if llm.available:
            out = llm.complete_json(
                "对方的聊天消息（按时间顺序）：\n" + self._pack(person_msgs), system=_SYSTEM)
            mems = self._normalize(out)
            if mems is not None:  # 空列表也是合法结果：确实没有重要信息
                return mems, "llm"
        return rule_engine.extract_memories(messages), "rule"

    def _pack(self, msgs: list[dict[str, Any]]) -> str:
        lines, total = [], 0
        for m in msgs:
            ts = str(m.get("timestamp") or "")[:16]
            line = f"{ts} {(m.get('content') or '')[:80]}"
            if total + len(line) > _MAX_CHARS:
                break  # ponytail: 超长截断（早期消息价值通常低于近期）；如需全覆盖再做抽样
            lines.append(line)
            total += len(line)
        return "\n".join(lines)

    def _normalize(self, out: Any) -> list[dict[str, Any]] | None:
        if not isinstance(out, dict) or not isinstance(out.get("memories"), list):
            return None
        seen: set[str] = set()
        mems = []
        for m in out["memories"]:
            try:
                content = str(m["content"]).strip()[:60]
                category = str(m["category"])
                importance = float(m.get("importance", 0.7))
            except (KeyError, TypeError, ValueError):
                continue
            if len(content) < 4 or category not in CATEGORIES or content in seen:
                continue
            seen.add(content)
            mems.append({"content": content, "category": category,
                         "importance": max(0.0, min(1.0, importance))})
        mems.sort(key=lambda x: x["importance"], reverse=True)
        return mems[:15]
