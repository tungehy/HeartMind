"""Persona / Self Skill 蒸馏服务。

参考 love-skill（对方）与 yourself-skill（自己），改造为 HeartMind 的
Persona Skill Schema，并接入版本化（SkillVersion）与证据/置信度追踪。
LLM 可用时用 LLM 蒸馏，否则用规则引擎产出骨架。
"""
from __future__ import annotations

from typing import Any

from ..llm import get_llm
from ..agents import rule_engine

PERSONA_LAYERS = ["identity", "style", "emotion", "values", "potential"]


def distill_person(name: str, facts: dict, memories: list[dict],
                   messages: list[dict]) -> dict[str, Any]:
    """蒸馏相亲对象 → Persona Skill 结构。"""
    llm = get_llm()
    if llm.available and (messages or facts):
        sample = "\n".join(f"{m.get('sender')}: {m.get('content')}" for m in messages[-60:])
        data = llm.complete_json(
            f"基于以下材料，为「{name}」蒸馏一份人物 Persona（5层：identity/style/emotion/values/potential）。"
            "无证据的字段标注 unknown，不要编造；区分事实与推断。"
            '输出 JSON：{"identity":{...},"style":{...},"emotion":{...},"values":{...},"potential":{...},'
            '"one_liner":"一句话画像","tags":["..."]}。\n\n'
            f"已知字段：{list(facts.keys())}\n聊天样本：\n{sample}",
            system="你是人物画像蒸馏助手，只输出JSON。",
        )
        if data:
            data["_engine"] = "llm"
            return data

    # 规则降级骨架
    hobbies = facts.get("hobbies", {}).get("value", []) or []
    metrics = rule_engine.interaction_metrics(messages)
    emotion = rule_engine.emotion_trend(messages)
    return {
        "_engine": "rule",
        "identity": {
            "name": name,
            "age": facts.get("age", {}).get("value"),
            "city": facts.get("city", {}).get("value"),
            "occupation": facts.get("occupation", {}).get("value"),
            "personality": facts.get("personality", {}).get("value", "unknown"),
        },
        "style": {
            "initiative": "较高" if metrics.get("person_ratio", 0) > 0.45 else "中等",
            "msg_length": "偏长" if metrics.get("person_avg_len", 0) > 8 else "偏短",
            "topics": rule_engine.extract_topics(messages),
        },
        "emotion": {"trend": emotion, "attachment": "unknown", "love_languages": {}},
        "values": {"hobbies": hobbies,
                   "relationship_view": facts.get("relationship_view", {}).get("value", "unknown"),
                   "future_city": facts.get("future_city", {}).get("value", "unknown")},
        "potential": {"strengths": [], "challenges": [], "growth": "unknown"},
        "one_liner": _one_liner(name, facts, hobbies),
        "tags": hobbies[:5],
    }


def distill_user(facts: dict) -> dict[str, Any]:
    """蒸馏用户自己 → Self Skill（Part A Self Memory + Part B Persona）。"""
    llm = get_llm()
    if llm.available and facts:
        data = llm.complete_json(
            "基于以下用户画像字段，蒸馏一份 Self Skill。"
            '输出 JSON：{"self_memory":{...},"persona":{...},"mate_criteria":{...},'
            '"boundaries":["..."],"one_liner":"..."}。无证据标注 unknown。\n\n'
            f"字段：{ {k: v.get('value') for k, v in facts.items() if isinstance(v, dict)} }",
            system="你是用户自我画像蒸馏助手，只输出JSON。",
        )
        if data:
            data["_engine"] = "llm"
            return data
    return {
        "_engine": "rule",
        "self_memory": {
            "identity": {k: facts.get(k, {}).get("value") for k in ("age", "city", "occupation")},
            "values": {"relationship_view": facts.get("relationship_view", {}).get("value", "unknown"),
                       "future_city": facts.get("future_city", {}).get("value", "unknown")},
            "lifestyle": facts.get("lifestyle", {}).get("value", "unknown"),
        },
        "persona": {"communication": facts.get("chat_style", {}).get("value", "unknown"),
                    "emotion_pattern": "unknown", "social": "unknown"},
        "mate_criteria": {"dealbreakers": [], "plus": [],
                          "preference": facts.get("mate_preference", {}).get("value", "unknown")},
        "boundaries": [],
        "one_liner": "用户画像构建中",
    }


def _one_liner(name: str, facts: dict, hobbies: list) -> str:
    age = facts.get("age", {}).get("value")
    city = facts.get("city", {}).get("value")
    occ = facts.get("occupation", {}).get("value")
    parts = [p for p in [f"{age}岁" if age else "", city, occ] if p]
    hobby = f"，喜欢{'、'.join(hobbies[:3])}" if hobbies else ""
    base = "、".join(parts) if parts else "信息有限"
    return f"{name}：{base}{hobby}。"
