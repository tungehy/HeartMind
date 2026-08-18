---
name: wechat-export
description: Export chat records for a specific WeChat contact from the WeChatDataAnalysis service. Use when the user wants to import or export one person's WeChat chat history into HeartMind, or mentions exporting WeChat messages by contact.
---

# WeChat Export（导出特定对象聊天记录）

将 WeChatDataAnalysis 项目「按联系人导出聊天记录」的能力抽象为可复用流程。

## 前置条件

- WeChatDataAnalysis 服务已启动（默认 `http://127.0.0.1:10392`）。
- 数据源就绪：已解密的 SQLite（`output/databases/{account}/`）或实时 WCDB。
- 配置 `WECHAT_EXPORT_URL` 环境变量指向该服务。

## 核心概念

- 按人过滤用的是**会话 `username`**（wxid 或 `xxx@chatroom`），不是备注名。
- 消息按联系人分表：`msg_{md5(username)}`。
- 导出产物是 **ZIP**，内含 `conversations/{idx}_{display}_{username}/messages.{json|txt|html|xlsx}`。

## 工作流程

1. **解析联系人**：显示名 → `username`。用 `remark`/`nick_name`/`alias` 精确且唯一匹配。
   （对应 WeChatDataAnalysis 的 `resolve_session` / `resolve_contact`。）
2. **创建导出任务**：`POST {WECHAT_EXPORT_URL}/api/chat/exports`
3. **轮询/下载**：`GET /api/chat/exports/{id}` → 完成后 `.../download` 取 ZIP。
4. **解析 ZIP**：读取 `messages.json`，转为 HeartMind `Conversation Event`。

## 最小请求体

```json
{
  "account": "wxid_self",
  "scope": "selected",
  "usernames": ["wxid_friend"],
  "format": "json",
  "source": "auto",
  "start_time": null,
  "end_time": null
}
```

## 最小输入

| 输入 | 必需 | 说明 |
|---|---|---|
| `usernames` | 是 | 会话 ID 列表，`scope` 固定 `selected` |
| `account` | 建议 | 多账号时必填 |
| `format` | 否 | 默认 `json` |
| `start_time`/`end_time` | 否 | Unix 秒 |

## 在 HeartMind 中

优先用 HTTP 调用上述服务；服务不可用时，回退到「文本/JSON 导入」路径
（`POST /api/import/text` 或 `/api/import/json`），接受已导出的聊天记录文本。

## 参考实现

- 导出 API：`WeChatDataAnalysis-main/src/wechat_decrypt_tool/routers/chat_export.py`
- 导出服务：`WeChatDataAnalysis-main/src/wechat_decrypt_tool/chat_export_service.py`
- 表名解析：`chat_helpers.py` 的 `_resolve_msg_table_name`
