"""HeartMind API 路由。

覆盖 MVP 闭环：创建对象 → Profile Builder Loop → 导入聊天 → 自动分析 →
Timeline/Score/Match/Advice → Date Review → Persona Skill → 模拟对话 → Dashboard。
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db, SessionLocal
from .. import models
from ..schemas import (
    PersonCreate, IngestText, IngestJson, ProfileAnswerIn, UserProfileIn,
    DateCreate, SimulateIn, WechatExportIn,
)
from ..services import orchestrator as orch
from ..services import ingestion_service as ing
from ..services import wechat_export_service as wx
from ..services import distill_service
from ..services import profile_service as ps
from ..agents.profile_builder import ProfileBuilderAgent
from ..agents.memory_agent import MemoryAgent
from ..agents.period_agent import PeriodAgent
from ..agents.relationship_agents import MatchAgent, AdviceAgent, DateReviewAgent, TurningPointAgent
from ..domain.stages import STAGE_LABELS, STATE_LABELS, STATE_COLORS

router = APIRouter(prefix="/api")

DEFAULT_USER_ID = 1


def get_default_user(db: Session) -> models.User:
    user = db.query(models.User).filter_by(id=DEFAULT_USER_ID).first()
    if not user:
        user = models.User(id=DEFAULT_USER_ID, name="我")
        db.add(user)
        db.commit()
        db.add(models.UserProfile(user_id=user.id, facts={}))
        db.commit()
        db.refresh(user)
    return user


def _get_rel(db: Session, person_id: int) -> models.Relationship:
    rel = db.query(models.Relationship).filter_by(person_id=person_id).first()
    if not rel:
        raise HTTPException(404, "关系不存在")
    return rel


# ================= 对象管理 =================
@router.post("/persons")
def create_person(payload: PersonCreate, db: Session = Depends(get_db)):
    """创建相亲对象；若提供描述则立即建立初步画像并返回首轮问题。"""
    user = get_default_user(db)
    person = orch.get_or_create_person(db, payload.name)
    rel = orch.get_or_create_relationship(db, user.id, person.id)

    result = {"person_id": person.id, "relationship_id": rel.id, "name": person.name}
    if payload.description.strip():
        agent = ProfileBuilderAgent("person")
        facts = orch.person_facts(db, person.id)
        out = agent.ingest_text(facts, payload.description, rel.stage, source="user")
        orch.save_person_facts(db, person.id, out["facts"])
        rel = orch.refresh_relationship(db, rel)
        nq = agent.next_questions(orch.person_facts(db, person.id), rel.stage)
        result.update({"extracted": out["extracted"], "conflicts": out["conflicts"],
                       "profile_loop": nq})
    return result


@router.delete("/persons/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db)):
    """删除相亲对象及其在本系统的全部数据（聊天记录/画像/记忆/时间轴/评分等）。
    只操作 HeartMind 数据库，不触碰微信原始数据。"""
    person = db.query(models.Person).filter_by(id=person_id).first()
    if not person:
        raise HTTPException(404, "对象不存在")
    rel = db.query(models.Relationship).filter_by(person_id=person_id).first()
    name = person.name
    if rel:
        db.delete(rel)  # 级联全部子表（含 turning_points/stages/reports）
    db.delete(person)  # 级联 profile / relationship / persona skills
    db.commit()
    return {"deleted": True, "person_id": person_id, "name": name}


@router.get("/persons")
def list_persons(db: Session = Depends(get_db)):
    rels = db.query(models.Relationship).all()
    cards = [orch.person_to_card(db, r) for r in rels]
    cards.sort(key=lambda c: c["score"], reverse=True)
    return cards


@router.get("/persons/{person_id}")
def person_detail(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    person = rel.person
    facts = orch.person_facts(db, person.id)
    stage = rel.stage
    summary = ps.summarize(facts, stage)
    metric = db.query(models.RelationshipMetric).filter_by(relationship_id=rel.id)\
        .order_by(models.RelationshipMetric.created_at.desc()).first()
    memories = db.query(models.Memory).filter_by(relationship_id=rel.id)\
        .order_by(models.Memory.importance.desc(), models.Memory.created_at.desc()).all()
    events = db.query(models.RelationshipEvent).filter_by(relationship_id=rel.id)\
        .order_by(models.RelationshipEvent.time).all()
    advice = db.query(models.Advice).filter_by(relationship_id=rel.id)\
        .order_by(models.Advice.created_at.desc()).first()
    skill = db.query(models.PersonaSkill).filter_by(person_id=person_id).first()
    skill_versions = []
    if skill:
        skill_versions = [{"version": v.version, "created_at": v.created_at.isoformat(),
                           "confidence": v.confidence, "content": v.content}
                          for v in sorted(skill.versions, key=lambda x: x.version)]

    return {
        "id": person.id, "name": person.name, "relationship_id": rel.id,
        "stage": rel.stage, "stage_label": STAGE_LABELS.get(rel.stage, rel.stage),
        "state": rel.state, "state_label": STATE_LABELS.get(rel.state, rel.state),
        "state_color": STATE_COLORS.get(rel.state), "score": rel.score,
        "facts": facts, "profile_summary": summary,
        "metric": {"dimensions": metric.dimensions, "overall": metric.overall,
                   "delta": metric.delta, "trend": metric.trend,
                   "plus": metric.plus_factors, "minus": metric.minus_factors,
                   "confidence": metric.confidence} if metric else None,
        "memories": [{"content": m.content, "category": m.category,
                      "time": m.created_at.isoformat()} for m in memories],
        "timeline": [{"time": e.time.isoformat(), "type": e.event_type,
                      "summary": e.summary, "stage": e.stage,
                      "is_turning_point": e.is_turning_point} for e in events],
        "advice": {"current_state": advice.current_state, "finding": advice.finding,
                   "suggestion": advice.suggestion, "timing": advice.timing,
                   "method": advice.method, "risk": advice.risk} if advice else None,
        "skill_versions": skill_versions,
    }


# ================= Profile Builder Loop =================
@router.get("/persons/{person_id}/profile-loop")
def profile_loop(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    agent = ProfileBuilderAgent("person")
    facts = orch.person_facts(db, person_id)
    return agent.next_questions(facts, rel.stage)


@router.post("/persons/{person_id}/profile-loop/answer")
def profile_answer(person_id: int, payload: ProfileAnswerIn, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    agent = ProfileBuilderAgent("person")
    facts = orch.person_facts(db, person_id)
    out = agent.answer(facts, payload.field, payload.answer, rel.stage)
    orch.save_person_facts(db, person_id, out["facts"])
    rel = orch.refresh_relationship(db, rel)
    nq = agent.next_questions(orch.person_facts(db, person_id), rel.stage)
    return {"recorded": out.get("recorded"), "conflict": out.get("conflict", False),
            "profile_loop": nq}


@router.get("/persons/{person_id}/profile-summary")
def profile_summary(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    facts = orch.person_facts(db, person_id)
    return ps.summarize(facts, rel.stage)


# ================= 关系时期分析 =================
def _run_period_analysis(db: Session, rel: models.Relationship):
    """LLM/规则划分关系时期并入库（先清旧段）。"""
    messages = orch.relationship_messages(db, rel.id)
    periods, engine = PeriodAgent().analyze(messages)
    db.query(models.RelationshipPeriod).filter_by(relationship_id=rel.id).delete()
    for p in periods:
        db.add(models.RelationshipPeriod(relationship_id=rel.id, engine=engine, **p))
    db.commit()
    return periods, engine


def _rebuild_memories(db: Session, rel: models.Relationship) -> tuple[int, str]:
    """删旧记忆，用 MemoryAgent（LLM 优先）重抽取。"""
    messages = orch.relationship_messages(db, rel.id)
    mems, engine = MemoryAgent().analyze(messages)
    db.query(models.Memory).filter_by(relationship_id=rel.id).delete()
    for m in mems:
        db.add(models.Memory(relationship_id=rel.id, content=m["content"],
                             category=m["category"], source="ai",
                             importance=m.get("importance", 0.7)))
    db.commit()
    return len(mems), engine


def _post_import_bg(relationship_id: int):
    """后台任务：导入聊天后异步跑 LLM 分析（记忆重抽取 + 时期分段），不阻塞导入响应。"""
    db = SessionLocal()
    try:
        rel = db.query(models.Relationship).filter_by(id=relationship_id).first()
        if rel:
            _rebuild_memories(db, rel)
            _run_period_analysis(db, rel)
    finally:
        db.close()


@router.post("/persons/{person_id}/analyze-periods")
def analyze_periods(person_id: int, db: Session = Depends(get_db)):
    """重新分析该对象的聊天时期分段（同步，供手动刷新）。"""
    rel = _get_rel(db, person_id)
    periods, engine = _run_period_analysis(db, rel)
    return {"engine": engine, "segments": [
        {"start": p["start_date"], "end": p["end_date"], "state": p["state"],
         "summary": p["summary"]} for p in periods]}


# ================= 聊天导入 =================
def _import(db: Session, person_name: str, events: list[dict], source: str,
            background_tasks: BackgroundTasks | None = None):
    user = get_default_user(db)
    person = orch.get_or_create_person(db, person_name)
    rel = orch.get_or_create_relationship(db, user.id, person.id)

    conv = models.Conversation(relationship_id=rel.id, source=source)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    for e in events:
        db.add(models.Message(
            conversation_id=conv.id, relationship_id=rel.id,
            sender=e["sender"], receiver=e.get("receiver", ""),
            timestamp=datetime.fromisoformat(e["timestamp"]) if isinstance(e.get("timestamp"), str) else datetime.now(timezone.utc),
            message_type=e.get("message_type", "text"), content=e.get("content", ""),
            topics=e.get("topics", []), emotion=e.get("emotion", ""),
            intent=e.get("intent", ""), entities=e.get("entities", []),
            importance=e.get("importance", 0.0), source=source))

    # Memory 抽取改由后台任务（MemoryAgent：LLM 优先）统一重抽取，避免规则噪音先入库
    mems: list[dict] = []

    # Profile 自动抽取
    agent = ProfileBuilderAgent("person")
    facts = orch.person_facts(db, person.id)
    analysis = ing.rule_engine.analyze_messages(events)
    for name, payload in analysis["facts"].items():
        facts, _ = ps.set_field(facts, name, payload["value"], source="conversation",
                                confidence=0.75, status="inferred", stage=rel.stage,
                                evidence=payload.get("evidence", []))
    orch.save_person_facts(db, person.id, facts)

    # Timeline 事件
    if events:
        db.add(models.RelationshipEvent(
            relationship_id=rel.id, event_type="chat_import",
            summary=f"导入 {len(events)} 条聊天记录（{source}）", stage=rel.stage,
            confidence=0.9))
    db.commit()

    rel = orch.refresh_relationship(db, rel)

    # Turning Point 检测
    tps = TurningPointAgent().detect(events)
    for tp in tps:
        db.add(models.TurningPoint(relationship_id=rel.id, title=tp["title"],
                                   what=tp["what"], why=tp["why"], before=tp["before"],
                                   after=tp["after"], possible_causes=tp["possible_causes"],
                                   suggestion=tp["suggestion"], evidence=tp["evidence"],
                                   confidence=tp["confidence"]))
        db.add(models.RelationshipEvent(relationship_id=rel.id, event_type="turning_point",
                                        summary=tp["title"], stage=rel.stage,
                                        is_turning_point=True, confidence=tp["confidence"]))
    db.commit()

    # Advice 生成
    _generate_advice(db, rel)
    if background_tasks is not None:
        background_tasks.add_task(_post_import_bg, rel.id)
    return {"person_id": person.id, "relationship_id": rel.id,
            "imported": len(events), "memories": len(mems),
            "turning_points": len(tps), "score": rel.score, "state": rel.state}


def _generate_advice(db: Session, rel: models.Relationship):
    facts = orch.person_facts(db, rel.person_id)
    ufacts = orch.user_facts(db, rel.user_id)
    match = MatchAgent().analyze(ufacts, facts)
    messages = orch.relationship_messages(db, rel.id)
    metrics = ing.rule_engine.interaction_metrics(messages)
    adv = AdviceAgent().advise(rel.stage, rel.state, facts, match, metrics)
    db.add(models.Advice(relationship_id=rel.id, current_state=adv["current_state"],
                         finding=adv["finding"], evidence=adv["evidence"], risk=adv["risk"],
                         opportunity=adv["opportunity"], suggestion=adv["suggestion"],
                         timing=adv["timing"], method=adv["method"]))
    db.commit()


@router.post("/import/text")
def import_text(payload: IngestText, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db)):
    events = ing.parse_text(payload.text, payload.person_name)
    if not events:
        raise HTTPException(400, "未能解析出任何消息，请检查格式")
    return _import(db, payload.person_name, events, payload.source, background_tasks)


@router.post("/import/json")
def import_json(payload: IngestJson, background_tasks: BackgroundTasks,
                db: Session = Depends(get_db)):
    events = ing.parse_json_records(payload.records, payload.person_name)
    if not events:
        raise HTTPException(400, "未能解析出任何消息")
    return _import(db, payload.person_name, events, payload.source, background_tasks)


# ================= 微信自动导出（对接 WeChatDataAnalysis） =================
@router.get("/wechat/status")
def wechat_status():
    """微信导出服务是否已配置且可达，前端据此显示「自动导出」入口。"""
    return {"configured": wx.service_configured(), "reachable": wx.check_reachable()}


@router.get("/wechat/targets")
def wechat_targets(account: str | None = None):
    """列出微信会话联系人（显示名 + username），供用户选择要导入的对象。"""
    try:
        data = wx.list_targets(account)
    except wx.WechatExportError as e:
        raise HTTPException(502, str(e))
    targets = [{"username": t.get("username"), "name": t.get("name"),
                "display_name": t.get("displayName"), "is_group": t.get("isGroup", False)}
               for t in data.get("targets", []) if not t.get("isGroup")]
    return {"account": data.get("account"), "source": data.get("source"),
            "targets": targets, "total": len(targets)}


@router.post("/import/wechat")
def import_wechat(payload: WechatExportIn, background_tasks: BackgroundTasks,
                  db: Session = Depends(get_db)):
    """自动导出指定微信联系人的聊天记录并导入分析。"""
    if not payload.username:
        raise HTTPException(400, "请先选择微信联系人（username 为空）")
    try:
        raw_messages, display_name = wx.export_contact_messages(
            payload.username, payload.account, payload.start_time, payload.end_time)
    except wx.WechatExportError as e:
        raise HTTPException(502, str(e))
    events = ing.parse_json_records(raw_messages, payload.person_name)
    if not events:
        raise HTTPException(400, "导出的消息中没有可解析的文本内容")
    return _import(db, payload.person_name, events, "wechat", background_tasks)


# ================= 时间轴 / 评分 / 匹配 =================
@router.get("/persons/{person_id}/timeline")
def timeline(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    events = db.query(models.RelationshipEvent).filter_by(relationship_id=rel.id)\
        .order_by(models.RelationshipEvent.time).all()
    tps = db.query(models.TurningPoint).filter_by(relationship_id=rel.id).all()
    return {
        "events": [{"time": e.time.isoformat(), "type": e.event_type, "summary": e.summary,
                    "stage": e.stage, "score_delta": e.score_delta,
                    "is_turning_point": e.is_turning_point} for e in events],
        "turning_points": [{"title": t.title, "what": t.what, "why": t.why,
                            "before": t.before, "after": t.after,
                            "possible_causes": t.possible_causes,
                            "suggestion": t.suggestion, "confidence": t.confidence} for t in tps],
    }


@router.get("/persons/{person_id}/score")
def score(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    m = db.query(models.RelationshipMetric).filter_by(relationship_id=rel.id)\
        .order_by(models.RelationshipMetric.created_at.desc()).first()
    if not m:
        raise HTTPException(404, "暂无评分")
    return {"overall": m.overall, "dimensions": m.dimensions, "delta": m.delta,
            "trend": m.trend, "plus_factors": m.plus_factors,
            "minus_factors": m.minus_factors, "data_completeness": m.data_completeness,
            "confidence": m.confidence}


@router.get("/persons/{person_id}/match")
def match(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    facts = orch.person_facts(db, person_id)
    ufacts = orch.user_facts(db, rel.user_id)
    result = MatchAgent().analyze(ufacts, facts)
    db.add(models.CompatibilityMetric(relationship_id=rel.id, overall=result["overall"],
                                      dimensions=result["dimensions"], confirmed=result["confirmed"],
                                      unknown=result["unknown"], conflicts=result["conflicts"],
                                      inferred=result["inferred"], confidence=result["confidence"]))
    db.commit()
    return result


# ================= 约会复盘 Loop =================
@router.post("/persons/{person_id}/dates")
def create_date(person_id: int, payload: DateCreate, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    agent = DateReviewAgent()
    extracted = agent.analyze(payload.description)
    record = models.DateRecord(relationship_id=rel.id, raw_description=payload.description,
                               extracted=extracted, status="collecting")
    db.add(record)

    # 新增人物信息 → 更新 Profile
    facts = orch.person_facts(db, person_id)
    for name, value in (extracted.get("new_facts") or {}).items():
        facts, _ = ps.set_field(facts, name, value, source="date_review",
                                confidence=0.8, status="confirmed", stage=rel.stage,
                                evidence=[payload.description[:60]])
    orch.save_person_facts(db, person_id, facts)

    # Timeline 事件
    db.add(models.RelationshipEvent(relationship_id=rel.id, event_type="date",
                                    summary=f"约会：{extracted.get('relation_change', '平稳')}",
                                    stage=rel.stage, confidence=0.85))
    db.commit()
    db.refresh(record)
    rel = orch.refresh_relationship(db, rel)
    _generate_advice(db, rel)

    questions = agent.followup_questions(extracted, orch.person_facts(db, person_id))
    return {"date_id": record.id, "extracted": extracted, "followup_questions": questions}


@router.post("/persons/{person_id}/dates/{date_id}/complete")
def complete_date(person_id: int, date_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    record = db.query(models.DateRecord).filter_by(id=date_id, relationship_id=rel.id).first()
    if not record:
        raise HTTPException(404, "约会记录不存在")
    agent = DateReviewAgent()
    review = agent.summarize(record.extracted)
    record.review = review
    record.status = "completed"
    db.commit()
    return {"date_id": date_id, "review": review}


# ================= Persona Skill =================
@router.post("/persons/{person_id}/skill/distill")
def distill_person_skill(person_id: int, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    person = rel.person
    facts = orch.person_facts(db, person_id)
    messages = orch.relationship_messages(db, rel.id)
    mems = [{"content": m.content} for m in db.query(models.Memory).filter_by(relationship_id=rel.id).all()]
    content = distill_service.distill_person(person.name, facts, mems, messages)

    skill = db.query(models.PersonaSkill).filter_by(person_id=person_id, owner_type="person").first()
    if not skill:
        skill = models.PersonaSkill(person_id=person_id, owner_type="person", current_version=0)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    version = skill.current_version + 1
    db.add(models.SkillVersion(skill_id=skill.id, version=version, content=content,
                               confidence=0.6 if content.get("_engine") == "rule" else 0.8))
    skill.current_version = version
    db.commit()
    return {"person_id": person_id, "version": version, "skill": content}


@router.get("/persons/{person_id}/skill")
def get_person_skill(person_id: int, db: Session = Depends(get_db)):
    skill = db.query(models.PersonaSkill).filter_by(person_id=person_id, owner_type="person").first()
    if not skill or not skill.versions:
        raise HTTPException(404, "尚未蒸馏，请先调用 distill")
    latest = max(skill.versions, key=lambda v: v.version)
    return {"person_id": person_id, "version": latest.version, "skill": latest.content,
            "total_versions": len(skill.versions)}


# ================= 用户画像 / Self Skill =================
@router.get("/user/profile")
def get_user_profile(db: Session = Depends(get_db)):
    user = get_default_user(db)
    facts = orch.user_facts(db, user.id)
    return {"user_id": user.id, "facts": facts,
            "summary": ps.summarize(facts, "STAGE_3")}


@router.post("/user/profile/answer")
def answer_user_profile(payload: UserProfileIn, db: Session = Depends(get_db)):
    user = get_default_user(db)
    agent = ProfileBuilderAgent("user")
    facts = orch.user_facts(db, user.id)
    out = agent.answer(facts, payload.field, payload.answer, "STAGE_3")
    orch.save_user_facts(db, user.id, out["facts"])
    return {"recorded": out.get("recorded"), "facts": orch.user_facts(db, user.id)}


@router.get("/user/profile-loop")
def user_profile_loop(db: Session = Depends(get_db)):
    user = get_default_user(db)
    agent = ProfileBuilderAgent("user")
    facts = orch.user_facts(db, user.id)
    return agent.next_questions(facts, "STAGE_3")


@router.post("/user/skill/distill")
def distill_user_skill(db: Session = Depends(get_db)):
    user = get_default_user(db)
    facts = orch.user_facts(db, user.id)
    content = distill_service.distill_user(facts)
    return {"user_id": user.id, "skill": content}


# ================= 模拟对话 =================
@router.post("/persons/{person_id}/simulate")
def simulate(person_id: int, payload: SimulateIn, db: Session = Depends(get_db)):
    rel = _get_rel(db, person_id)
    person = rel.person
    facts = orch.person_facts(db, person_id)
    from ..llm import get_llm
    llm = get_llm()
    reply = None
    engine = "rule"
    if llm.available:
        skill = db.query(models.PersonaSkill).filter_by(person_id=person_id).first()
        persona = ""
        if skill and skill.versions:
            persona = str(max(skill.versions, key=lambda v: v.version).content)
        system = f"你正在扮演{person.name}，基于以下画像与用户对话，用她的口吻回复。\n{persona}"
        reply = llm.complete(payload.message, system=system)
        engine = "llm" if reply else "rule"
    if not reply:
        hobbies = facts.get("hobbies", {}).get("value", []) or []
        hook = f"说到{hobbies[0]}，我最近正好有研究呢。" if hobbies else "嗯，我在听。"
        reply = f"{hook}（{person.name}的模拟回复，配置 LLM 后更真实）"
    out = {"reply": reply, "mode": payload.mode, "engine": engine}
    if payload.mode == "training":
        out["coach"] = _coach(payload.message)
    return out


def _coach(message: str) -> dict:
    q_count = message.count("？") + message.count("?")
    tips = []
    if q_count >= 3:
        tips.append("你连续追问了多个问题，建议先回应她当前的表达，再继续提问。")
    if len(message) > 120:
        tips.append("这条消息偏长，可适当拆分，给对方回应空间。")
    if not tips:
        tips.append("表达自然，节奏良好。")
    return {"tips": tips}


# ================= Dashboard =================
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    rels = db.query(models.Relationship).all()
    cards = [orch.person_to_card(db, r) for r in rels]
    cards.sort(key=lambda c: c["score"], reverse=True)
    gantt = []
    for r in rels:
        events = db.query(models.RelationshipEvent).filter_by(relationship_id=r.id)\
            .order_by(models.RelationshipEvent.time).all()
        # 消息真实时间跨度：甘特条应以聊天内容时间为准，而非导入时刻
        ts = db.query(func.min(models.Message.timestamp), func.max(models.Message.timestamp),
                      func.count(models.Message.id))\
            .filter(models.Message.relationship_id == r.id).first()
        first_msg, last_msg, msg_count = (ts[0], ts[1], ts[2]) if ts else (None, None, 0)
        # AI 时期分段（导入聊天后由 PeriodAgent 生成，LLM 优先/规则降级）
        periods = db.query(models.RelationshipPeriod).filter_by(relationship_id=r.id)\
            .order_by(models.RelationshipPeriod.start_date).all()
        gantt.append({
            "person_id": r.person_id, "name": r.person.name, "state": r.state,
            "state_color": STATE_COLORS.get(r.state), "score": r.score,
            "stage_label": STAGE_LABELS.get(r.stage, r.stage),
            "first_message": first_msg.isoformat() if first_msg else None,
            "last_message": last_msg.isoformat() if last_msg else None,
            "message_count": msg_count or 0,
            "segments": [{"start": p.start_date, "end": p.end_date, "state": p.state,
                          "summary": p.summary, "engine": p.engine} for p in periods],
            "events": [{"time": e.time.isoformat(), "type": e.event_type,
                        "summary": e.summary, "is_turning_point": e.is_turning_point}
                       for e in events],
        })
    return {"cards": cards, "gantt": gantt, "total": len(cards)}


@router.get("/health")
def health():
    from ..llm import get_llm
    return {"status": "ok", "llm": get_llm().provider, "llm_available": get_llm().available}
