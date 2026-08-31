"""HeartMind ?????V2 ?????????

?????
- Relationship ??????Chat/Message ????????
- ProfileField ?? value/source/evidence/confidence/status/timing/information_value?
  ???"???????""??????""?????????"?
- ???????? JSON ??SQLite / PostgreSQL ??????????
- ???? AI ???? AgentRun????????????

???????????? Relationship ????????? SQLAlchemy ?
relationship() ???ORM ???????? orm_rel?
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean,
)
from sqlalchemy.orm import relationship as orm_rel

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------- ?? ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), default="?")
    created_at = Column(DateTime, default=utcnow)

    profile = orm_rel("UserProfile", back_populates="user", uselist=False,
                      cascade="all, delete-orphan")
    relationships = orm_rel("Relationship", back_populates="user",
                            cascade="all, delete-orphan")


class UserProfile(Base):
    """?????User Digital Twin??facts ? ProfileField ??? JSON?"""
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    facts = Column(JSON, default=dict)          # {field_name: ProfileField-like dict}
    completeness = Column(Float, default=0.0)   # 0~1
    summary = Column(Text, default="")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = orm_rel("User", back_populates="profile")


# ---------- ???? ----------
class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    profile = orm_rel("PersonProfile", back_populates="person", uselist=False,
                      cascade="all, delete-orphan")
    relationship = orm_rel("Relationship", back_populates="person", uselist=False,
                           cascade="all, delete-orphan")
    skills = orm_rel("PersonaSkill", back_populates="person",
                     cascade="all, delete-orphan")


class PersonProfile(Base):
    __tablename__ = "person_profiles"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), unique=True)
    facts = Column(JSON, default=dict)
    completeness = Column(Float, default=0.0)
    summary = Column(Text, default="")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    person = orm_rel("Person", back_populates="profile")


# ---------- ???????? ----------
class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    person_id = Column(Integer, ForeignKey("persons.id"), unique=True)
    stage = Column(String(32), default="STAGE_1")     # RelationshipStage
    state = Column(String(32), default="stable")      # warming/stable/cooling/coldwar/ended
    score = Column(Float, default=50.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = orm_rel("User", back_populates="relationships")
    person = orm_rel("Person", back_populates="relationship")
    conversations = orm_rel("Conversation", back_populates="relationship",
                            cascade="all, delete-orphan")
    events = orm_rel("RelationshipEvent", back_populates="relationship",
                     cascade="all, delete-orphan")
    memories = orm_rel("Memory", back_populates="relationship",
                       cascade="all, delete-orphan")
    dates = orm_rel("DateRecord", back_populates="relationship",
                    cascade="all, delete-orphan")
    metrics = orm_rel("RelationshipMetric", back_populates="relationship",
                      cascade="all, delete-orphan")
    compatibility = orm_rel("CompatibilityMetric", back_populates="relationship",
                            cascade="all, delete-orphan")
    advices = orm_rel("Advice", back_populates="relationship",
                      cascade="all, delete-orphan")
    # 无外键级联声明的表也要纳入删除（SQLite 已开启 FK 约束）
    turning_points = orm_rel("TurningPoint", cascade="all, delete-orphan")
    stages = orm_rel("RelationshipStage", cascade="all, delete-orphan")
    reports = orm_rel("Report", cascade="all, delete-orphan")
    periods = orm_rel("RelationshipPeriod", cascade="all, delete-orphan")


class RelationshipStage(Base):
    """??????????????????????"""
    __tablename__ = "relationship_stages"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    stage = Column(String(32))
    confidence = Column(Float, default=0.5)
    evidence = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)


# ---------- ????? ----------
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    source = Column(String(32), default="text")   # wechat/text/json/csv/markdown
    imported_at = Column(DateTime, default=utcnow)

    relationship = orm_rel("Relationship", back_populates="conversations")
    messages = orm_rel("Message", back_populates="conversation",
                       cascade="all, delete-orphan")


class Message(Base):
    """Conversation Event Schema?V2 ??????"""
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    sender = Column(String(64))            # 'user' / 'person' / ???
    receiver = Column(String(64), default="")
    timestamp = Column(DateTime, default=utcnow)
    message_type = Column(String(32), default="text")
    content = Column(Text, default="")
    media_reference = Column(String(255), default="")
    reply_to = Column(Integer, nullable=True)
    source = Column(String(32), default="text")
    # AI ?????
    topics = Column(JSON, default=list)
    emotion = Column(String(32), default="")
    intent = Column(String(64), default="")
    entities = Column(JSON, default=list)
    importance = Column(Float, default=0.0)

    conversation = orm_rel("Conversation", back_populates="messages")


# ---------- ??? / ??? ----------
class RelationshipEvent(Base):
    """Timeline Event?V2 ??????"""
    __tablename__ = "relationship_events"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    time = Column(DateTime, default=utcnow)
    event_type = Column(String(32))        # met/chat_import/date/warming/cooling/conflict/gift/reconnect/end...
    summary = Column(Text, default="")
    stage = Column(String(32), default="")
    score_delta = Column(Float, default=0.0)
    ai_analysis = Column(Text, default="")
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)
    is_turning_point = Column(Boolean, default=False)

    relationship = orm_rel("Relationship", back_populates="events")


class RelationshipPeriod(Base):
    """AI 分析的关系时期分段：按聊天内容在趋势突变点切分。"""
    __tablename__ = "relationship_periods"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    start_date = Column(String(10))          # YYYY-MM-DD
    end_date = Column(String(10))
    state = Column(String(32), default="stable")  # warming/stable/cooling/coldwar/ended
    summary = Column(Text, default="")       # AI 对该时期的一句话解读
    msg_count = Column(Integer, default=0)
    engine = Column(String(16), default="rule")   # llm / rule
    created_at = Column(DateTime, default=utcnow)


class TurningPoint(Base):
    __tablename__ = "turning_points"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    event_id = Column(Integer, ForeignKey("relationship_events.id"), nullable=True)
    detected_at = Column(DateTime, default=utcnow)
    title = Column(String(128), default="")
    what = Column(Text, default="")
    why = Column(Text, default="")
    before = Column(Text, default="")
    after = Column(Text, default="")
    possible_causes = Column(JSON, default=list)
    suggestion = Column(Text, default="")
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)


# ---------- ?? ----------
class DateRecord(Base):
    __tablename__ = "date_records"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    occurred_at = Column(DateTime, default=utcnow)
    raw_description = Column(Text, default="")
    extracted = Column(JSON, default=dict)   # ??/??/??/??/????/??...
    review = Column(JSON, default=dict)      # ????
    status = Column(String(32), default="collecting")

    relationship = orm_rel("Relationship", back_populates="dates")


# ---------- ???? / ?? ----------
class ProfileFieldRecord(Base):
    """??????????????????????? Profile.facts JSON?"""
    __tablename__ = "profile_field_records"
    id = Column(Integer, primary_key=True)
    owner_type = Column(String(16))          # user / person
    owner_id = Column(Integer)
    field_name = Column(String(64))
    value = Column(JSON)
    value_type = Column(String(32), default="string")
    source = Column(String(32), default="user")
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)
    status = Column(String(32), default="unknown")   # confirmed/inferred/unknown/conflicting/outdated
    timing = Column(String(32), default="unknown")   # now/soon/later/not_relevant/unknown
    information_value = Column(Float, default=0.0)
    sensitivity = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=utcnow)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)


class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    content = Column(Text)
    category = Column(String(32), default="general")  # preference/fact/promise/event...
    source = Column(String(32), default="chat")
    confidence = Column(Float, default=0.5)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, default=utcnow)

    relationship = orm_rel("Relationship", back_populates="memories")


# ---------- ?? / ?? ----------
class RelationshipMetric(Base):
    __tablename__ = "relationship_metrics"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    dimensions = Column(JSON, default=dict)   # ????/?????/... ? 0~100
    overall = Column(Float, default=50.0)
    delta = Column(Float, default=0.0)
    trend = Column(String(16), default="stable")
    plus_factors = Column(JSON, default=list)
    minus_factors = Column(JSON, default=list)
    data_completeness = Column(Float, default=0.0)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=utcnow)

    relationship = orm_rel("Relationship", back_populates="metrics")


class CompatibilityMetric(Base):
    __tablename__ = "compatibility_metrics"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    overall = Column(Float, default=0.0)
    dimensions = Column(JSON, default=dict)   # ???/????/??/??/???/??/??/??
    confirmed = Column(JSON, default=list)
    unknown = Column(JSON, default=list)      # ??????? UI?
    conflicts = Column(JSON, default=list)
    inferred = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=utcnow)

    relationship = orm_rel("Relationship", back_populates="compatibility")


# ---------- Persona Skill ----------
class PersonaSkill(Base):
    __tablename__ = "persona_skills"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"))
    owner_type = Column(String(16), default="person")  # person / user
    current_version = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    person = orm_rel("Person", back_populates="skills")
    versions = orm_rel("SkillVersion", back_populates="skill",
                       cascade="all, delete-orphan")


class SkillVersion(Base):
    __tablename__ = "skill_versions"
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("persona_skills.id"))
    version = Column(Integer)
    content = Column(JSON, default=dict)      # ???? Persona Skill ??
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=utcnow)

    skill = orm_rel("PersonaSkill", back_populates="versions")


# ---------- ?? / ?? / ?? ----------
class Advice(Base):
    __tablename__ = "advices"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"))
    current_state = Column(Text, default="")
    finding = Column(Text, default="")
    evidence = Column(JSON, default=list)
    risk = Column(Text, default="")
    opportunity = Column(Text, default="")
    suggestion = Column(Text, default="")
    timing = Column(Text, default="")
    method = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    relationship = orm_rel("Relationship", back_populates="advices")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"), nullable=True)
    title = Column(String(128), default="")
    content = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)


class AgentRun(Base):
    """AI ??????V2 ???????"""
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True)
    agent = Column(String(64))
    model = Column(String(64), default="")
    prompt_version = Column(String(32), default="v1")
    input_reference = Column(JSON, default=dict)
    output = Column(JSON, default=dict)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=utcnow)
