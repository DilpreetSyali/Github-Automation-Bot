import datetime as dt
from typing import Optional

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class RepoOut(BaseModel):
    id: int
    owner: str
    name: str
    connected_at: dt.datetime

    class Config:
        from_attributes = True


class ConnectRepoIn(BaseModel):
    owner: str
    name: str


class RuleIn(BaseModel):
    name: str
    event_type: str
    match_field: str
    match_type: str = "contains"
    match_value: str
    add_label: Optional[str] = None
    post_comment: Optional[str] = None
    slack_notify: bool = True
    enabled: bool = True


class RuleOut(RuleIn):
    id: int
    repo_id: int

    class Config:
        from_attributes = True


class ActionLogOut(BaseModel):
    id: int
    action_type: str
    status: str
    detail: Optional[str] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True


class EventOut(BaseModel):
    id: int
    event_type: str
    action: Optional[str] = None
    status: str
    error: Optional[str] = None
    received_at: dt.datetime
    actions: list[ActionLogOut] = []

    class Config:
        from_attributes = True
