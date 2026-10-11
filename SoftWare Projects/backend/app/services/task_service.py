from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from fastapi import HTTPException
from datetime import date

from app.models.task import Task, TaskLabel, TaskAttachment, TaskComment, Priority
from app.models.board import Column
from app.schemas.task import TaskCreate, TaskUpdate, TaskMoveRequest, CommentCreate, CommentUpdate, AttachmentCreate
from app.services.project_service import assert_member


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _get_column_project_id(db: Session, column_id: int) -> int:
    col = db.query(Column).filter(Column.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    return col.board.project_id


def get_tasks_by_column(db: Session, column_id: int, user_id: int) -> list[Task]:
    project_id = _get_column_project_id(db, column_id)
    assert_member(db, project_id, user_id)
    return (
        db.query(Task)
        .options(joinedload(Task.assignee), joinedload(Task.labels))
        .filter(Task.column_id == column_id)
        .order_by(Task.position)
        .all()
    )


def get_task(db: Session, task_id: int, user_id: int) -> Task:
    task = (
        db.query(Task)
        .options(
            joinedload(Task.assignee),
            joinedload(Task.labels),
            joinedload(Task.attachments),
            joinedload(Task.comments).joinedload(TaskComment.author),
        )
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    project_id = _get_column_project_id(db, task.column_id)
    assert_member(db, project_id, user_id)
    return task


def create_task(db: Session, column_id: int, data: TaskCreate, user_id: int) -> Task:
    project_id = _get_column_project_id(db, column_id)
    assert_member(db, project_id, user_id)

    # Assign next position
    max_pos = db.query(Task).filter(Task.column_id == column_id).count()
    task = Task(
        column_id=column_id,
        title=data.title,
        description=data.description,
        assignee_id=data.assignee_id,
        due_date=data.due_date,
        priority=data.priority,
        position=max_pos,
        created_by=user_id,
    )
    db.add(task)
    db.flush()
    for label in data.labels:
        db.add(TaskLabel(task_id=task.id, **label.model_dump()))
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate, user_id: int) -> Task:
    task = _get_task_or_404(db, task_id)
    project_id = _get_column_project_id(db, task.column_id)
    assert_member(db, project_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def move_task(db: Session, task_id: int, req: TaskMoveRequest, user_id: int) -> Task:
    task = _get_task_or_404(db, task_id)
    source_project = _get_column_project_id(db, task.column_id)
    target_project = _get_column_project_id(db, req.column_id)
    assert_member(db, source_project, user_id)

    # Shift positions in source column
    if task.column_id != req.column_id:
        db.query(Task).filter(
            Task.column_id == task.column_id, Task.position > task.position
        ).update({"position": Task.position - 1})

    # Make room in target column
    db.query(Task).filter(
        Task.column_id == req.column_id, Task.position >= req.position
    ).update({"position": Task.position + 1})

    task.column_id = req.column_id
    task.position = req.position
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, user_id: int) -> None:
    task = _get_task_or_404(db, task_id)
    project_id = _get_column_project_id(db, task.column_id)
    assert_member(db, project_id, user_id)
    db.delete(task)
    db.commit()


def search_tasks(
    db: Session,
    project_id: int,
    user_id: int,
    q: str | None = None,
    assignee_id: int | None = None,
    priority: Priority | None = None,
    label: str | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
) -> list[Task]:
    assert_member(db, project_id, user_id)
    # Get all column IDs for this project's boards
    from app.models.board import Board
    board_ids = [b.id for b in db.query(Board).filter(Board.project_id == project_id).all()]
    col_ids = [c.id for c in db.query(Column).filter(Column.board_id.in_(board_ids)).all()]

    query = db.query(Task).options(
        joinedload(Task.assignee), joinedload(Task.labels)
    ).filter(Task.column_id.in_(col_ids))

    if q:
        query = query.filter(or_(Task.title.ilike(f"%{q}%"), Task.description.ilike(f"%{q}%")))
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if priority:
        query = query.filter(Task.priority == priority)
    if label:
        query = query.join(TaskLabel).filter(TaskLabel.name.ilike(f"%{label}%"))
    if due_before:
        query = query.filter(Task.due_date <= due_before)
    if due_after:
        query = query.filter(Task.due_date >= due_after)

    return query.order_by(Task.due_date.asc().nullslast(), Task.priority.desc()).all()


# --- Comments ---

def add_comment(db: Session, task_id: int, data: CommentCreate, user_id: int) -> TaskComment:
    task = _get_task_or_404(db, task_id)
    project_id = _get_column_project_id(db, task.column_id)
    assert_member(db, project_id, user_id)
    comment = TaskComment(task_id=task_id, author_id=user_id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db: Session, comment_id: int, data: CommentUpdate, user_id: int) -> TaskComment:
    comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's comment")
    comment.content = data.content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int, user_id: int) -> None:
    comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's comment")
    db.delete(comment)
    db.commit()


# --- Attachments ---

def add_attachment(db: Session, task_id: int, data: AttachmentCreate, user_id: int) -> TaskAttachment:
    task = _get_task_or_404(db, task_id)
    project_id = _get_column_project_id(db, task.column_id)
    assert_member(db, project_id, user_id)
    att = TaskAttachment(task_id=task_id, uploaded_by=user_id, **data.model_dump())
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


def delete_attachment(db: Session, attachment_id: int, user_id: int) -> None:
    att = db.query(TaskAttachment).filter(TaskAttachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    db.delete(att)
    db.commit()
