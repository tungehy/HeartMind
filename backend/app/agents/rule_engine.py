"""确定性规则分析引擎（LLM 降级实现）。

无 API Key 时，HeartMind 仍能从聊天/描述中抽取画像、记忆、阶段、情绪等。
所有方法为纯函数，便于测试。当配置了 LLM 时，Agent 优先调用 LLM 再回退到这里。
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

# 关键词词表
HOBBY_WORDS = ["旅游", "旅行", "摄影", "音乐", "电影", "读书", "阅读", "健身", "运动",
               "跑步", "瑜伽", "羽毛球", "篮球", "游泳", "露营", "咖啡", "美食", "烘焙",
               "游戏", "动漫", "猫", "狗", "宠物", "画画", "手工", "做饭", "徒步", "骑行"]
CITY_WORDS = ["北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "苏州", "南通",
              "武汉", "西安", "重庆", "天津", "长沙", "青岛", "厦门", "宁波", "无锡"]
OCC_WORDS = ["老师", "教师", "医生", "护士", "工程师", "程序员", "设计师", "产品",
             "会计", "律师", "销售", "运营", "公务员", "金融", "分析师", "外贸"]
POS_EMO = ["开心", "哈哈", "喜欢", "棒", "好呀", "期待", "谢谢", "太好了", "😊", "😄", "❤", "🥰"]
NEG_EMO = ["忙", "累", "烦", "压力", "难过", "生气", "失望", "算了", "😔", "😤", "无语"]
COMMIT_WORDS = ["一起", "下次", "约", "见面", "带你", "陪", "答应"]


def extract_from_text(text: str) -> dict[str, Any]:
    """从自然语言描述中抽取基础画像字段。返回 {field: {value, evidence}}。"""
    found: dict[str, Any] = {}
    m = re.search(r"(\d{2})\s*岁", text)
    if m:
        found["age"] = {"value": int(m.group(1)), "evidence": [text[:60]]}
    for w in CITY_WORDS:
        if w in text:
            found["city"] = {"value": w, "evidence": [text[:60]]}
            break
    for w in OCC_WORDS:
        if w in text:
            found["occupation"] = {"value": w, "evidence": [text[:60]]}
            break
    hobbies = [w for w in HOBBY_WORDS if w in text]
    if hobbies:
        found["hobbies"] = {"value": hobbies, "evidence": [text[:60]]}
    if any(k in text for k in ["慢热", "内向", "文静"]):
        found["personality"] = {"value": "慢热偏内向", "evidence": [text[:60]]}
    elif any(k in text for k in ["开朗", "外向", "活泼"]):
        found["personality"] = {"value": "开朗外向", "evidence": [text[:60]]}
    return found


def analyze_messages(messages: list[dict]) -> dict[str, Any]:
    """从结构化消息中抽取画像/记忆/情绪/主动性指标。"""
    person_msgs = [m for m in messages if m.get("sender") == "person"]
    user_msgs = [m for m in messages if m.get("sender") == "user"]
    all_text = " ".join(m.get("content", "") for m in person_msgs)

    facts: dict[str, Any] = {}
    hobbies = sorted({w for w in HOBBY_WORDS if w in all_text})
    if hobbies:
        facts["hobbies"] = {"value": hobbies, "evidence": _sample(person_msgs, hobbies)}
    for w in CITY_WORDS:
        if w in all_text:
            facts["city"] = {"value": w, "evidence": _sample(person_msgs, [w])}
            break
    for w in OCC_WORDS:
        if w in all_text:
            facts["occupation"] = {"value": w, "evidence": _sample(person_msgs, [w])}
            break

    memories = extract_memories(messages)
    metrics = interaction_metrics(messages)
    topics = extract_topics(messages)
    emotion = emotion_trend(messages)
    return {"facts": facts, "memories": memories, "metrics": metrics,
            "topics": topics, "emotion": emotion}


def extract_memories(messages: list[dict]) -> list[dict[str, Any]]:
    """抽取长期记忆：包含偏好/承诺/重要事实的句子。"""
    mems = []
    for m in messages:
        if m.get("sender") != "person":
            continue
        c = m.get("content", "")
        if not c or len(c) < 4:
            continue
        if any(k in c for k in ["我喜欢", "我爱", "我家", "我最近", "我准备", "我打算", "我想"]):
            mems.append({"content": c[:80], "category": "preference", "importance": 0.7,
                         "time": m.get("timestamp")})
        elif any(k in c for k in COMMIT_WORDS):
            mems.append({"content": c[:80], "category": "promise", "importance": 0.8,
                         "time": m.get("timestamp")})
    return mems[:20]


def extract_topics(messages: list[dict]) -> list[str]:
    cnt = Counter()
    for w in HOBBY_WORDS + ["工作", "旅游", "美食", "电影", "音乐", "家庭", "未来", "城市"]:
        n = sum(1 for m in messages if w in m.get("content", ""))
        if n:
            cnt[w] += n
    return [w for w, _ in cnt.most_common(6)]


def emotion_trend(messages: list[dict]) -> str:
    pos = sum(1 for m in messages if any(k in m.get("content", "") for k in POS_EMO))
    neg = sum(1 for m in messages if any(k in m.get("content", "") for k in NEG_EMO))
    if pos > neg * 1.5:
        return "positive"
    if neg > pos * 1.5:
        return "negative"
    return "neutral"


def interaction_metrics(messages: list[dict]) -> dict[str, Any]:
    """互动指标：双方消息数、主动性、平均长度。"""
    pm = [m for m in messages if m.get("sender") == "person"]
    um = [m for m in messages if m.get("sender") == "user"]
    total = max(1, len(pm) + len(um))
    avg_len = (sum(len(m.get("content", "")) for m in pm) / len(pm)) if pm else 0
    return {
        "person_msgs": len(pm),
        "user_msgs": len(um),
        "person_ratio": round(len(pm) / total, 3),
        "person_avg_len": round(avg_len, 1),
        "sample_count": len(messages),
    }


def infer_stage(metrics: dict[str, Any], msg_count: int, has_date: bool,
                emotion: str) -> tuple[str, float, list[str]]:
    """根据互动指标推断关系阶段（规则降级）。"""
    evidence = []
    stage = "STAGE_1"
    conf = 0.5
    if msg_count == 0:
        return "STAGE_1", 0.3, ["尚无聊天记录"]
    if msg_count < 15:
        stage, conf = "STAGE_1", 0.6
        evidence.append("消息量较少，处于刚认识阶段")
    elif msg_count < 60:
        stage, conf = "STAGE_3", 0.65
        evidence.append("已持续互动一段时间")
    else:
        stage, conf = "STAGE_4", 0.6
        evidence.append("互动频繁")
    if metrics.get("person_ratio", 0) > 0.45 and metrics.get("person_avg_len", 0) > 8:
        evidence.append("对方回复积极、内容较长")
        if stage in ("STAGE_3", "STAGE_4"):
            stage = "STAGE_4"
            conf += 0.1
    if has_date:
        stage = "STAGE_5" if stage in ("STAGE_4",) else "STAGE_3"
        evidence.append("已有线下见面")
        conf += 0.05
    if emotion == "negative":
        stage = "STAGE_8"
        evidence.append("近期情绪偏负面")
        conf = 0.55
    return stage, round(min(conf, 0.95), 2), evidence


def stage_to_state(stage: str, emotion: str) -> str:
    """阶段 → 甘特图状态色。"""
    if stage == "STAGE_9":
        return "ended"
    if stage == "STAGE_8":
        return "cooling"
    if stage in ("STAGE_4", "STAGE_5"):
        return "warming"
    if emotion == "negative":
        return "coldwar"
    return "stable"


def _sample(messages: list[dict], words: list[str], n: int = 2) -> list[str]:
    out = []
    for m in messages:
        c = m.get("content", "")
        if any(w in c for w in words) and c not in out:
            out.append(c[:60])
        if len(out) >= n:
            break
    return out
