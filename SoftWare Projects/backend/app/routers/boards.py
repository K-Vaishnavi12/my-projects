from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.board import BoardCreate, BoardUpdate, BoardOut, ColumnCreate, ColumnUpdate, ColumnOut
from app.services import board_service
from .deps import get_current_user

router = APIRouter(tags=["boards"])


@router.get("/projects/{project_id}/boards", response_model=list[BoardOut])
def list_boards(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return board_service.get_boards(db, project_id, current_user.id)


@router.post("/projects/{project_id}/boards", response_model=BoardOut, status_code=201)
def create_board(
    project_id: int,
    data: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return board_service.create_board(db, project_id, data, current_user.id)


@router.patch("/boards/{board_id}", response_model=BoardOut)
def update_board(
    board_id: int,
    data: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return board_service.update_board(db, board_id, data, current_user.id)


@router.delete("/boards/{board_id}", status_code=204)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board_service.delete_board(db, board_id, current_user.id)


@router.post("/boards/{board_id}/columns", response_model=ColumnOut, status_code=201)
def create_column(
    board_id: int,
    data: ColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return board_service.create_column(db, board_id, data, current_user.id)


@router.patch("/columns/{column_id}", response_model=ColumnOut)
def update_column(
    column_id: int,
    data: ColumnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return board_service.update_column(db, column_id, data, current_user.id)


@router.delete("/columns/{column_id}", status_code=204)
def delete_column(
    column_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board_service.delete_column(db, column_id, current_user.id)
