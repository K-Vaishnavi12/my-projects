from pydantic import BaseModel
from datetime import datetime, date
from app.models.task import Priority
from .user import UserPublic


class LabelCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class LabelOut(BaseModel):
    id: int
    name: str
    color: str

    model_config = {"from_attributes": True}


class AttachmentCreate(BaseModel):
    filename: str
    url: str


class AttachmentOut(BaseModel):
    id: int
    filename: str
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    content: str
    author: UserPublic
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    priority: Priority = Priority.medium
    labels: list[LabelCreate] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    priority: Priority | None = None
    column_id: int | None = None
    position: int | None = None


class TaskMoveRequest(BaseModel):
    column_id: int
    position: int


class TaskOut(BaseModel):
    id: int
    column_id: int
    title: str
    description: str | None
    assignee: UserPublic | None
    due_date: date | None
    priority: Priority
    position: int
    created_at: datetime
    updated_at: datetime
    labels: list[LabelOut] = []
    attachments: list[AttachmentOut] = []
    comments: list[CommentOut] = []

    model_config = {"from_attributes": True}


class TaskSummary(BaseModel):
    id: int
    column_id: int
    title: str
    priority: Priority
    due_date: date | None
    position: int
    assignee: UserPublic | None
    labels: list[LabelOut] = []

    model_config = {"from_attributes": True}
