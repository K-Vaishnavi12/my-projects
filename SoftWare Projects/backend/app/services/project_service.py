from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project import Project, ProjectMember, MemberRole
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, AddMember


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def assert_member(db: Session, project_id: int, user_id: int) -> ProjectMember:
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    return member


def assert_admin(db: Session, project_id: int, user_id: int) -> None:
    member = assert_member(db, project_id, user_id)
    if member.role not in (MemberRole.owner, MemberRole.admin):
        raise HTTPException(status_code=403, detail="Admin access required")


def get_user_projects(db: Session, user_id: int) -> list[Project]:
    memberships = db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
    project_ids = [m.project_id for m in memberships]
    return db.query(Project).filter(Project.id.in_(project_ids)).all()


def create_project(db: Session, data: ProjectCreate, owner_id: int) -> Project:
    project = Project(**data.model_dump(), owner_id=owner_id)
    db.add(project)
    db.flush()
    # Auto-add owner as member
    member = ProjectMember(project_id=project.id, user_id=owner_id, role=MemberRole.owner)
    db.add(member)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: int, data: ProjectUpdate, user_id: int) -> Project:
    project = _get_project_or_404(db, project_id)
    assert_admin(db, project_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    project = _get_project_or_404(db, project_id)
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only project owner can delete")
    db.delete(project)
    db.commit()


def add_member(db: Session, project_id: int, data: AddMember, current_user_id: int) -> ProjectMember:
    assert_admin(db, project_id, current_user_id)
    _get_project_or_404(db, project_id)
    existing = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == data.user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member")
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    member = ProjectMember(project_id=project_id, user_id=data.user_id, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, project_id: int, user_id: int, current_user_id: int) -> None:
    project = _get_project_or_404(db, project_id)
    if project.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove project owner")
    assert_admin(db, project_id, current_user_id)
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
