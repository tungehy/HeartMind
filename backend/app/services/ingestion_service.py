"""聊天导入服务（V2 第十六节）：多源输入 → 统一 Conversation Event。

支持：wechat(经 WeChatDataAnalysis 导出的 JSON/ZIP) / text / json / csv / markdown。
图片/语音/视频为后续扩展（OCR/Whisper/ASR），此处预留入口。
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..agents import rule_engine


def parse_text(content: str, person_name: str, user_name: str = "我") -> list[dict[str, Any]]:
    """解析纯文本聊天记录。支持常见格式：
    [2026-07-01 12:30] 林小雨: 内容
    2026-07-01 12:30 林小雨: 内容
    林小雨: 内容
    """
    msgs = []
    pattern = re.compile(
        r"(?:\[?(?P<ts>\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)\]?)?\s*"
        r"(?P<sender>[^:\[\]\n]{1,20}?)\s*[:：]\s*(?P<content>.+)"
    )
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if not m:
            continue
        sender_raw = m.group("sender").strip()
        sender = "person" if person_name in sender_raw else "user" if (user_name in sender_raw or sender_raw in ("我", "me")) else "person"
        ts = _parse_ts(m.group("ts"))
        msgs.append(_make_event(sender, m.group("content").strip(), ts))
    return msgs


def parse_json_records(records: list[dict], person_name: str) -> list[dict[str, Any]]:
    """解析 JSON 记录（含 WeChat 导出的 messages.json 结构）。"""
    msgs = []
    for r in records:
        content = r.get("content") or r.get("text") or ""
        if not isinstance(content, str) or not content.strip():
            continue
        is_sent = r.get("isSent") if "isSent" in r else (r.get("sender") in ("我", "user", "self"))
        sender = "user" if is_sent else "person"
        ts = r.get("createTime") or r.get("timestamp")
        msgs.append(_make_event(sender, content.strip(), _parse_ts(ts)))
    return msgs


def _make_event(sender: str, content: str, ts: datetime | None) -> dict[str, Any]:
    """生成 Conversation Event，并做轻量结构化标注（topic/emotion/importance）。"""
    topics = [w for w in rule_engine.HOBBY_WORDS + ["工作", "未来", "家庭"] if w in content]
    pos = any(k in content for k in rule_engine.POS_EMO)
    neg = any(k in content for k in rule_engine.NEG_EMO)
    emotion = "positive" if pos else "negative" if neg else "neutral"
    importance = 0.8 if any(k in content for k in rule_engine.COMMIT_WORDS + ["我喜欢", "我打算"]) else 0.4
    return {
        "sender": sender,
        "receiver": "",
        "timestamp": (ts or datetime.now(timezone.utc)).isoformat(),
        "message_type": "text",
        "content": content,
        "topics": topics,
        "emotion": emotion,
        "intent": "",
        "entities": [],
        "importance": importance,
    }


def _parse_ts(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):  # Unix 秒
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        except Exception:
            return None
    s = str(raw).replace("/", "-")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
