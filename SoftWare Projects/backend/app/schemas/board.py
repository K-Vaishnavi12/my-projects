from pydantic import BaseModel
from datetime import datetime


class BoardCreate(BaseModel):
    name: str
    description: str | None = None


class BoardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ColumnCreate(BaseModel):
    name: str
    color: str = "#e2e8f0"
    position: int = 0


class ColumnUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    position: int | None = None


class ColumnOut(BaseModel):
    id: int
    board_id: int
    name: str
    position: int
    color: str

    model_config = {"from_attributes": True}


class BoardOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: str | None
    created_at: datetime
    columns: list[ColumnOut] = []

    model_config = {"from_attributes": True}
