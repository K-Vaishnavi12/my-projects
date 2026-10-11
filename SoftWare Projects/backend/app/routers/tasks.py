from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.models.user import User
from app.models.task import Priority
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskMoveRequest, TaskOut, TaskSummary,
    CommentCreate, CommentUpdate, CommentOut,
    AttachmentCreate, AttachmentOut,
)
from app.services import task_service
from .deps import get_current_user

router = APIRouter(tags=["tasks"])


@router.get("/columns/{column_id}/tasks", response_model=list[TaskSummary])
def list_tasks(
    column_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.get_tasks_by_column(db, column_id, current_user.id)


@router.post("/columns/{column_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(
    column_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.create_task(db, column_id, data, current_user.id)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.get_task(db, task_id, current_user.id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.update_task(db, task_id, data, current_user.id)


@router.post("/tasks/{task_id}/move", response_model=TaskOut)
def move_task(
    task_id: int,
    req: TaskMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.move_task(db, task_id, req, current_user.id)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_task(db, task_id, current_user.id)


@router.get("/projects/{project_id}/tasks/search", response_model=list[TaskSummary])
def search_tasks(
    project_id: int,
    q: str | None = Query(None),
    assignee_id: int | None = Query(None),
    priority: Priority | None = Query(None),
    label: str | None = Query(None),
    due_before: date | None = Query(None),
    due_after: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.search_tasks(
        db, project_id, current_user.id, q, assignee_id, priority, label, due_before, due_after
    )


# --- Comments ---

@router.post("/tasks/{task_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    task_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.add_comment(db, task_id, data, current_user.id)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.update_comment(db, comment_id, data, current_user.id)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_comment(db, comment_id, current_user.id)


# --- Attachments ---

@router.post("/tasks/{task_id}/attachments", response_model=AttachmentOut, status_code=201)
def add_attachment(
    task_id: int,
    data: AttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.add_attachment(db, task_id, data, current_user.id)


@router.delete("/attachments/{attachment_id}", status_code=204)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_attachment(db, attachment_id, current_user.id)
