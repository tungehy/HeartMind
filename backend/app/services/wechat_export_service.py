"""微信聊天记录自动导出服务（对接 WeChatDataAnalysis 项目）。

对应 .cursor/skills/wechat-export/SKILL.md：
- 联系人列表：GET  {WECHAT_EXPORT_URL}/api/chat/exports/targets
- 创建导出任务：POST {WECHAT_EXPORT_URL}/api/chat/exports
- 轮询状态：    GET  {WECHAT_EXPORT_URL}/api/chat/exports/{id}
- 下载产物：    GET  {WECHAT_EXPORT_URL}/api/chat/exports/{id}/download → ZIP
- ZIP 内 messages.json 结构见 wechat_decrypt_tool/chat_export_service.py L3611+
"""
from __future__ import annotations

import io
import json
import time
import zipfile
from typing import Any

import httpx

from ..config import get_settings

# ponytail: 简单常数即可；导出上千条消息通常几秒内完成
_POLL_INTERVAL = 1.0
_POLL_TIMEOUT = 120.0
_HTTP_TIMEOUT = 15.0


class WechatExportError(RuntimeError):
    """微信导出链路出错（服务不可达/任务失败/产物异常），message 面向用户可读。"""


def _base_url() -> str:
    return get_settings().wechat_export_url.rstrip("/")


def service_configured() -> bool:
    return bool(_base_url())


def check_reachable() -> bool:
    if not service_configured():
        return False
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{_base_url()}/api/chat/exports")
            return r.status_code == 200
    except httpx.HTTPError:
        return False


def list_targets(account: str | None = None) -> dict[str, Any]:
    """列出可导出的会话（含显示名，用于按称呼选择联系人）。"""
    if not service_configured():
        raise WechatExportError("未配置 WECHAT_EXPORT_URL，请在 backend/.env 中设置微信导出服务地址")
    params = {"source": "auto"}
    if account:
        params["account"] = account
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            r = client.get(f"{_base_url()}/api/chat/exports/targets", params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        raise WechatExportError(f"微信导出服务不可达（{e}），请确认 WeChatDataAnalysis 已启动") from e
    except ValueError as e:
        raise WechatExportError(f"微信导出服务返回异常：{e}") from e
    if data.get("status") != "success":
        raise WechatExportError(str(data.get("detail") or "获取联系人列表失败"))
    return data


def export_contact_messages(
    username: str,
    account: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """导出指定会话的聊天记录，返回 (原始消息列表, 会话显示名)。"""
    if not service_configured():
        raise WechatExportError("未配置 WECHAT_EXPORT_URL，请在 backend/.env 中设置微信导出服务地址")
    with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
        job = _create_job(client, username, account, start_time, end_time)
        job_id = str(job.get("exportId") or "")
        _wait_job(client, job_id)
        zip_bytes = _download(client, job_id)
    return _parse_zip(zip_bytes)


def _create_job(client: httpx.Client, username: str, account: str | None,
                start_time: int | None, end_time: int | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "scope": "selected",
        "usernames": [username],
        "format": "json",
        "source": "auto",
        "include_media": False,  # 只要文本，媒体解析是后续扩展
    }
    if account:
        payload["account"] = account
    if start_time:
        payload["start_time"] = start_time
    if end_time:
        payload["end_time"] = end_time
    try:
        r = client.post(f"{_base_url()}/api/chat/exports", json=payload)
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:200] if e.response is not None else str(e)
        raise WechatExportError(f"创建导出任务失败：{detail}") from e
    except httpx.HTTPError as e:
        raise WechatExportError(f"微信导出服务不可达（{e}）") from e
    job = data.get("job") or {}
    if not job.get("exportId"):
        raise WechatExportError("导出服务未返回任务 ID")
    return job


def _wait_job(client: httpx.Client, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + _POLL_TIMEOUT
    while time.monotonic() < deadline:
        try:
            r = client.get(f"{_base_url()}/api/chat/exports/{job_id}")
            r.raise_for_status()
            job = (r.json() or {}).get("job") or {}
        except httpx.HTTPError as e:
            raise WechatExportError(f"查询导出任务失败：{e}") from e
        status = str(job.get("status") or "").lower()
        if status == "done" or job.get("zipReady"):
            return job
        if status in ("error", "cancelled"):
            raise WechatExportError(f"导出任务失败：{job.get('error') or status}")
        time.sleep(_POLL_INTERVAL)
    raise WechatExportError(f"导出超时（{_POLL_TIMEOUT:.0f}s），请稍后重试")


def _download(client: httpx.Client, job_id: str) -> bytes:
    try:
        r = client.get(f"{_base_url()}/api/chat/exports/{job_id}/download", timeout=60.0)
        r.raise_for_status()
        return r.content
    except httpx.HTTPError as e:
        raise WechatExportError(f"下载导出文件失败：{e}") from e


def _parse_zip(zip_bytes: bytes) -> tuple[list[dict[str, Any]], str]:
    """从导出 ZIP 中读取第一个会话的 messages.json。"""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as e:
        raise WechatExportError("导出产物不是有效的 ZIP 文件") from e
    json_names = [n for n in zf.namelist() if n.endswith("messages.json")]
    if not json_names:
        raise WechatExportError("导出 ZIP 中未找到 messages.json")
    try:
        payload = json.loads(zf.read(json_names[0]).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise WechatExportError(f"messages.json 解析失败：{e}") from e
    messages = payload.get("messages") or []
    display = str((payload.get("conversation") or {}).get("displayName") or "").strip()
    if not messages:
        raise WechatExportError("该会话没有可导出的消息")
    return messages, display
