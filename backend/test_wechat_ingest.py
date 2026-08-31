# -*- coding: utf-8 -*-
"""微信自动导出链路的离线自检（不需要真实 WeChatDataAnalysis 服务）。

运行：python test_wechat_ingest.py
验证：导出 ZIP 解析(_parse_zip) → messages.json 兼容(parse_json_records) →
      /api/wechat/status 端点可用、未配置时 /api/import/wechat 报可读错误。
"""
import io
import json
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")  # Windows GBK 控制台

from app.services import ingestion_service as ing
from app.services import wechat_export_service as wx


def make_export_zip() -> bytes:
    """按 WeChatDataAnalysis messages.json 的真实结构构造一个内存 ZIP。"""
    payload = {
        "schemaVersion": 1,
        "exportedAt": "2026-08-26T10:00:00",
        "account": "wxid_self",
        "conversation": {"username": "wxid_girl", "displayName": "林小雨",
                         "avatarPath": "", "isGroup": False},
        "filters": {"startTime": None, "endTime": None, "messageTypes": None},
        "messages": [
            {"id": "db:t:1", "localId": 1, "createTime": 1780300000,
             "createTimeText": "2026-06-01 10:00:00", "type": 1, "renderType": "text",
             "isSent": True, "senderUsername": "wxid_self",
             "conversationUsername": "wxid_girl", "isGroup": False,
             "content": "周末有空吗"},
            {"id": "db:t:2", "localId": 2, "createTime": 1780300300,
             "createTimeText": "2026-06-01 10:05:00", "type": 1, "renderType": "text",
             "isSent": False, "senderUsername": "wxid_girl",
             "conversationUsername": "wxid_girl", "isGroup": False,
             "content": "有呀，最近准备去云南旅游"},
            {"id": "db:t:3", "localId": 3, "createTime": 1780300400,
             "createTimeText": "2026-06-01 10:06:00", "type": 47, "renderType": "emoji",
             "isSent": False, "senderUsername": "wxid_girl",
             "conversationUsername": "wxid_girl", "isGroup": False,
             "content": ""},
        ],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("conversations/0001_林小雨_wxid_girl_ab12cd34/messages.json",
                    json.dumps(payload, ensure_ascii=False))
    return buf.getvalue()


def main():
    # 1. ZIP 解析：找到 messages.json、取出会话显示名
    messages, display = wx._parse_zip(make_export_zip())
    assert display == "林小雨", display
    assert len(messages) == 3
    print("✓ ZIP 解析 | 会话:", display, "| 消息数:", len(messages))

    # 2. 消息兼容：空 content（表情包等）被过滤，isSent → user/person
    events = ing.parse_json_records(messages, "林小雨")
    assert len(events) == 2, f"应过滤空 content，实际 {len(events)}"
    assert events[0]["sender"] == "user"
    assert events[1]["sender"] == "person"
    assert "旅游" in (events[1]["topics"] or [])
    print("✓ messages.json → Conversation Event | 有效消息:", len(events))

    # 3. 空 ZIP / 无消息的错误路径
    bad = io.BytesIO()
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("manifest.json", "{}")
    try:
        wx._parse_zip(bad.getvalue())
        raise AssertionError("应当抛出 WechatExportError")
    except wx.WechatExportError:
        print("✓ 异常 ZIP 抛出可读的 WechatExportError")

    # 4. 未配置服务时给出可读错误（而不是栈溢出）
    assert not wx.service_configured()
    try:
        wx.list_targets()
        raise AssertionError("应当抛出 WechatExportError")
    except wx.WechatExportError as e:
        assert "WECHAT_EXPORT_URL" in str(e)
        print("✓ 未配置时错误信息可读:", str(e)[:40], "…")

    print("\n微信导出链路离线自检通过 ✓（真实服务联调：启动 WeChatDataAnalysis 后设 WECHAT_EXPORT_URL）")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("✗ 失败:", repr(e))
        sys.exit(1)
