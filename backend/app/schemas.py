"""API 请求/响应模型。"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class PersonCreate(BaseModel):
    name: str
    description: str = ""          # 用户自然语言描述（可选）


class IngestText(BaseModel):
    person_name: str
    text: str
    source: str = "text"           # text / wechat / markdown / csv


class IngestJson(BaseModel):
    person_name: str
    records: list[dict[str, Any]]
    source: str = "json"


class ProfileAnswerIn(BaseModel):
    field: str
    answer: Any                    # 值 或 "不知道"/"以后再说"/"跳过"


class UserProfileIn(BaseModel):
    field: str
    answer: Any


class DateCreate(BaseModel):
    description: str


class SimulateIn(BaseModel):
    message: str
    mode: str = "real"             # real / training / stress / rehearsal


class WechatExportIn(BaseModel):
    person_name: str
    account: Optional[str] = None
    username: Optional[str] = None  # 会话 username；为空则需先解析
    start_time: Optional[int] = None
    end_time: Optional[int] = None
