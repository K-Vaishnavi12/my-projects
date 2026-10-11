from pydantic import BaseModel
from datetime import datetime
from app.models.project import MemberRole
from .user import UserPublic


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    color: str = "#6366f1"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class ProjectMemberOut(BaseModel):
    id: int
    user: UserPublic
    role: MemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    color: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    members: list[ProjectMemberOut] = []

    model_config = {"from_attributes": True}


class AddMember(BaseModel):
    user_id: int
    role: MemberRole = MemberRole.member
