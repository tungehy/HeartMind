"""Relationship Orchestrator（V2 第二十九节多 Agent 架构的入口）。

协调各 Agent：导入聊天后 → Stage 判断 → Profile 抽取 → Memory 抽取 →
Score 计算 → Timeline 事件 → 写 AgentRun 追溯。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .. import models
from ..agents import rule_engine
from ..agents.profile_builder import ProfileBuilderAgent
from ..agents.relationship_agents import (
    StageAgent, ScoreAgent, TurningPointAgent, MatchAgent, AdviceAgent,
)
from ..services import profile_service as ps


def _log_run(db: Session, agent: str, input_ref: dict, output: dict,
             confidence: float = 0.5, model: str = ""):
    db.add(models.AgentRun(agent=agent, model=model, input_reference=input_ref,
                           output=output, confidence=confidence))
    db.commit()


def get_or_create_person(db: Session, name: str) -> models.Person:
    person = db.query(models.Person).filter(models.Person.name == name).first()
    if person:
        return person
    person = models.Person(name=name)
    db.add(person)
    db.commit()
    db.refresh(person)
    db.add(models.PersonProfile(person_id=person.id, facts={}))
    db.commit()
    return person


def get_or_create_relationship(db: Session, user_id: int, person_id: int) -> models.Relationship:
    rel = db.query(models.Relationship).filter(models.Relationship.person_id == person_id).first()
    if rel:
        return rel
    rel = models.Relationship(user_id=user_id, person_id=person_id, stage="STAGE_1", state="stable")
    db.add(rel)
    db.commit()
    db.refresh(rel)
    db.add(models.RelationshipEvent(
        relationship_id=rel.id, event_type="met", summary="建立关系档案",
        stage="STAGE_1", confidence=0.9))
    db.commit()
    return rel


def person_facts(db: Session, person_id: int) -> dict:
    prof = db.query(models.PersonProfile).filter_by(person_id=person_id).first()
    return dict(prof.facts) if prof and prof.facts else {}


def user_facts(db: Session, user_id: int) -> dict:
    prof = db.query(models.UserProfile).filter_by(user_id=user_id).first()
    return dict(prof.facts) if prof and prof.facts else {}


def save_person_facts(db: Session, person_id: int, facts: dict):
    prof = db.query(models.PersonProfile).filter_by(person_id=person_id).first()
    if not prof:
        prof = models.PersonProfile(person_id=person_id)
        db.add(prof)
    prof.facts = facts
    prof.updated_at = datetime.now(timezone.utc)
    db.commit()


def save_user_facts(db: Session, user_id: int, facts: dict):
    prof = db.query(models.UserProfile).filter_by(user_id=user_id).first()
    if not prof:
        prof = models.UserProfile(user_id=user_id)
        db.add(prof)
    prof.facts = facts
    prof.updated_at = datetime.now(timezone.utc)
    db.commit()


def relationship_messages(db: Session, relationship_id: int) -> list[dict]:
    msgs = db.query(models.Message).filter_by(relationship_id=relationship_id)\
        .order_by(models.Message.timestamp).all()
    return [{"sender": m.sender, "content": m.content, "timestamp": m.timestamp.isoformat() if m.timestamp else None}
            for m in msgs]


def refresh_relationship(db: Session, rel: models.Relationship) -> models.Relationship:
    """重算阶段/状态/评分/画像完整度，并记录 AgentRun。"""
    person = rel.person
    facts = person_facts(db, person.id)
    messages = relationship_messages(db, rel.id)
    has_date = db.query(models.DateRecord).filter_by(relationship_id=rel.id).count() > 0

    # Stage
    stage_out = StageAgent().judge(messages, has_date)
    stage = stage_out.get("stage", rel.stage)
    state = stage_out.get("state", rel.state)
    if stage != rel.stage:
        db.add(models.RelationshipStage(relationship_id=rel.id, stage=stage,
                                        confidence=stage_out.get("confidence", 0.5),
                                        evidence=stage_out.get("evidence", [])))
    rel.stage = stage
    rel.state = state

    # Profile completeness
    comp = ps.completeness(facts, stage)
    prof = db.query(models.PersonProfile).filter_by(person_id=person.id).first()
    if prof:
        prof.completeness = comp
        prof.summary = _summary_text(facts, stage)

    # Score
    score_out = ScoreAgent().score(messages, facts, has_date, comp)
    prev = rel.score or 50.0
    rel.score = score_out["overall"]
    db.add(models.RelationshipMetric(
        relationship_id=rel.id, dimensions=score_out["dimensions"],
        overall=score_out["overall"], delta=round(score_out["overall"] - prev, 1),
        trend=score_out["trend"], plus_factors=score_out["plus_factors"],
        minus_factors=score_out["minus_factors"],
        data_completeness=comp, confidence=score_out["confidence"]))

    db.commit()
    _log_run(db, "StageAgent", {"rel": rel.id}, stage_out, stage_out.get("confidence", 0.5))
    _log_run(db, "ScoreAgent", {"rel": rel.id}, score_out, score_out["confidence"])
    db.refresh(rel)
    return rel


def _summary_text(facts: dict, stage: str) -> str:
    s = ps.summarize(facts, stage)
    confirmed = "、".join(f"{c['label']}" for c in s["confirmed"]) or "暂无"
    return f"已确认：{confirmed}；完整度 {int(s['completeness']*100)}%"


def person_to_card(db: Session, rel: models.Relationship) -> dict[str, Any]:
    """组装前端对象卡片所需数据。"""
    person = rel.person
    facts = person_facts(db, person.id)
    messages = relationship_messages(db, rel.id)
    mems = db.query(models.Memory).filter_by(relationship_id=rel.id)\
        .order_by(models.Memory.created_at.desc()).limit(3).all()
    latest_metric = db.query(models.RelationshipMetric)\
        .filter_by(relationship_id=rel.id).order_by(models.RelationshipMetric.created_at.desc()).first()
    advice = db.query(models.Advice).filter_by(relationship_id=rel.id)\
        .order_by(models.Advice.created_at.desc()).first()
    hobbies = facts.get("hobbies", {}).get("value", []) or []
    last_ts = messages[-1]["timestamp"] if messages else None

    # 雷达六维（从评分维度映射）
    radar = []
    if latest_metric:
        d = latest_metric.dimensions
        radar = [d.get("沟通质量", 50), d.get("兴趣匹配", 50), d.get("价值观匹配", 50),
                 d.get("情绪连接", 50), d.get("未来规划匹配", 50), d.get("主动程度", 50)]

    return {
        "id": person.id, "relationship_id": rel.id, "name": person.name,
        "age": facts.get("age", {}).get("value"),
        "city": facts.get("city", {}).get("value"),
        "occupation": facts.get("occupation", {}).get("value"),
        "score": rel.score, "state": rel.state, "stage": rel.stage,
        "radar": radar, "tags": hobbies,
        "memories": [m.content for m in mems],
        "last_chat": last_ts,
        "suggestion": advice.suggestion if advice else "暂无建议，先完善画像",
        "completeness": rel.person.profile.completeness if rel.person.profile else 0.0,
    }
