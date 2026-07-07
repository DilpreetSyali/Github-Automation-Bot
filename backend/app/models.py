import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    github_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    # NOTE: in a real prod system encrypt this at rest (e.g. via KMS/Fernet).
    # Kept as-is here for exercise scope, but never logged and never sent to the client.
    access_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    repos = relationship("Repo", back_populates="owner_user", cascade="all, delete-orphan")
    slack_connections = relationship("SlackConnection", back_populates="user", cascade="all, delete-orphan")


class Repo(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    github_repo_id = Column(String, nullable=False, index=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    webhook_id = Column(String, nullable=True)
    connected_at = Column(DateTime, default=dt.datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "github_repo_id", name="uq_user_repo"),)

    owner_user = relationship("User", back_populates="repos")
    events = relationship("Event", back_populates="repo", cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="repo", cascade="all, delete-orphan")


class Event(Base):
    """One row per GitHub webhook delivery. delivery_id is unique so a
    redelivered webhook (GitHub retries on timeout/5xx) can never be
    processed twice — the DB unique constraint is the source of truth,
    not an in-memory check."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    delivery_id = Column(String, unique=True, nullable=False, index=True)
    event_type = Column(String, nullable=False)   # e.g. "issues", "pull_request", "push"
    action = Column(String, nullable=True)          # e.g. "opened", "closed"
    payload = Column(Text, nullable=False)          # raw JSON, for audit/debugging
    status = Column(String, default="received")     # received | processed | failed
    error = Column(Text, nullable=True)
    received_at = Column(DateTime, default=dt.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    repo = relationship("Repo", back_populates="events")
    actions = relationship("ActionLog", back_populates="event", cascade="all, delete-orphan")


class ActionLog(Base):
    """Every outbound action the bot took (or tried to take) for an event —
    GitHub label/comment, Slack message. Kept separately from Event so one
    event that triggers 2 actions (label + Slack) shows both, and so retries
    of a single failed action don't require reprocessing the whole event."""

    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    action_type = Column(String, nullable=False)   # github_label | github_comment | slack_notify
    status = Column(String, nullable=False)        # success | failed
    detail = Column(Text, nullable=True)
    attempt = Column(Integer, default=1)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    event = relationship("Event", back_populates="actions")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)     # issues | pull_request
    match_field = Column(String, nullable=False)     # title | body | author
    match_type = Column(String, default="contains")  # contains | equals
    match_value = Column(String, nullable=False)
    add_label = Column(String, nullable=True)
    post_comment = Column(Text, nullable=True)
    slack_notify = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    repo = relationship("Repo", back_populates="rules")


class SlackConnection(Base):
    __tablename__ = "slack_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    access_token = Column(Text, nullable=True)
    team_id = Column(String, nullable=True)
    team_name = Column(String, nullable=True)
    channel_id = Column(String, nullable=True)
    channel_name = Column(String, nullable=True)
    webhook_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    user = relationship("User", back_populates="slack_connections")
