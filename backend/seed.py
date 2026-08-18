# -*- coding: utf-8 -*-
"""演示数据播种：清空并重建 3 位不同状态的相亲对象 + 用户画像。

运行：python seed.py  （会先删除 heartmind.db 并重建）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal, init_db, engine, Base  # noqa: E402
from app import models  # noqa: E402
from app.services import orchestrator as orch  # noqa: E402
from app.services import ingestion_service as ing  # noqa: E402
from app.services import profile_service as ps  # noqa: E402
from app.routers.api import _import, _generate_advice, get_default_user  # noqa: E402


def build(db, name, desc, chat_lines):
    person = orch.get_or_create_person(db, name)
    user = get_default_user(db)
    rel = orch.get_or_create_relationship(db, user.id, person.id)
    # 描述 → 画像
    facts = orch.person_facts(db, person.id)
    for fname, payload in ing.rule_engine.extract_from_text(desc).items():
        facts, _ = ps.set_field(facts, fname, payload["value"], "user", 0.9, "confirmed", rel.stage, payload.get("evidence"))
    orch.save_person_facts(db, person.id, facts)
    # 聊天导入
    events = ing.parse_text("\n".join(chat_lines), name)
    _import(db, name, events, "text")
    print(f"✓ {name}: {len(events)} 条消息")


def main():
    init_db()
    # 清空所有表（不删文件，避免占用冲突）
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    db = SessionLocal()
    try:
        # 用户画像
        user = get_default_user(db)
        uf = {}
        for k, v in [("city", "南通"), ("occupation", "工程师"), ("relationship_view", "重视稳定"),
                     ("hobbies", ["旅行", "阅读", "摄影"]), ("future_city", "江苏")]:
            uf, _ = ps.set_field(uf, k, v, "user", 0.95, "confirmed", "STAGE_3", ["用户自述"])
        orch.save_user_facts(db, user.id, uf)

        build(db, "林小雨", "27岁，在上海做产品经理，喜欢旅游摄影咖啡，养了只猫，性格慢热", [
            "2026-06-01 10:00 我: 周末有空吗",
            "2026-06-01 10:05 林小雨: 有呀，最近准备去云南旅游",
            "2026-06-01 10:08 林小雨: 我喜欢摄影，想拍很多照片",
            "2026-06-02 09:00 林小雨: 我家猫今天好可爱",
            "2026-06-03 20:00 林小雨: 下次一起去看摄影展吧",
            "2026-06-05 11:00 我: 好呀，我很喜欢这个主意",
            "2026-06-05 11:02 林小雨: 太好了，期待",
        ])
        build(db, "王梓涵", "25岁，在深圳做设计师，喜欢健身和音乐，性格开朗", [
            "2026-05-10 14:00 我: 你好",
            "2026-05-10 14:20 王梓涵: 你好呀",
            "2026-05-12 19:00 王梓涵: 我刚健完身",
            "2026-05-15 20:00 我: 最近听什么歌",
            "2026-05-15 20:30 王梓涵: 周杰伦",
        ])
        build(db, "李梦琪", "28岁，在北京做投行分析师，喜欢红酒和话剧，最近工作很忙", [
            "2026-04-01 21:00 我: 最近怎么样",
            "2026-04-02 08:00 李梦琪: 有点忙",
            "2026-04-10 22:00 我: 周末出来吗",
            "2026-04-12 09:00 李梦琪: 最近压力大，想休息",
            "2026-04-20 23:00 李梦琪: 烦，工作好累",
        ])
        print("\n播种完成：3 位对象 + 用户画像")
    finally:
        db.close()


if __name__ == "__main__":
    main()
