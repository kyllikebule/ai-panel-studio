"""SQLAlchemy ORM 模型 —— 6 实体映射。"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, ForeignKey, CheckConstraint,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Host(Base):
    __tablename__ = "host"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    discussions = relationship("Discussion", back_populates="host", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="host")


class Discussion(Base):
    __tablename__ = "discussion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    max_rounds = Column(Integer, nullable=False, default=5)
    current_round = Column(Integer, nullable=False, default=0)
    host_id = Column(Integer, ForeignKey("host.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        CheckConstraint("status IN ('pending','active','paused','completed')", name="ck_discussion_status"),
    )

    host = relationship("Host", back_populates="discussions")
    discussion_guests = relationship("DiscussionGuest", back_populates="discussion", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="discussion", cascade="all, delete-orphan")


class Guest(Base):
    __tablename__ = "guest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    avatar = Column(String)
    persona = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    speak_style = Column(String)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    discussion_guests = relationship("DiscussionGuest", back_populates="guest", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="guest")


class DiscussionGuest(Base):
    __tablename__ = "discussion_guest"

    discussion_id = Column(Integer, ForeignKey("discussion.id", ondelete="CASCADE"), primary_key=True)
    guest_id = Column(Integer, ForeignKey("guest.id", ondelete="CASCADE"), primary_key=True)
    stance_override = Column(Text)
    is_active = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("discussion_id", "guest_id", name="uq_discussion_guest"),
    )

    discussion = relationship("Discussion", back_populates="discussion_guests")
    guest = relationship("Guest", back_populates="discussion_guests")


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discussion_id = Column(Integer, ForeignKey("discussion.id", ondelete="CASCADE"), nullable=False)
    host_id = Column(Integer, ForeignKey("host.id", ondelete="SET NULL"))
    guest_id = Column(Integer, ForeignKey("guest.id", ondelete="SET NULL"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    seq_num = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        CheckConstraint("role IN ('host','guest','system')", name="ck_message_role"),
        CheckConstraint(
            "host_id IS NOT NULL OR guest_id IS NOT NULL",
            name="ck_message_sender"
        ),
        Index("idx_message_discussion_seq", "discussion_id", "seq_num"),
    )

    discussion = relationship("Discussion", back_populates="messages")
    host = relationship("Host", back_populates="messages")
    guest = relationship("Guest", back_populates="messages")
    opinion = relationship("Opinion", back_populates="message", uselist=False, cascade="all, delete-orphan")


class Opinion(Base):
    __tablename__ = "opinion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("message.id", ondelete="CASCADE"), nullable=False, unique=True)
    stance_summary = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    confidence = Column(Float)
    evidence = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        CheckConstraint(
            "category IN ('consensus','disagreement','neutral')",
            name="ck_opinion_category"
        ),
        Index("idx_opinion_message", "message_id"),
    )

    message = relationship("Message", back_populates="opinion")
