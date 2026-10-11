from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.board import Board, Column
from app.schemas.board import BoardCreate, BoardUpdate, ColumnCreate, ColumnUpdate
from app.services.project_service import assert_member, assert_admin


def _get_board_or_404(db: Session, board_id: int) -> Board:
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


def _get_column_or_404(db: Session, column_id: int) -> Column:
    col = db.query(Column).filter(Column.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    return col


def get_boards(db: Session, project_id: int, user_id: int) -> list[Board]:
    assert_member(db, project_id, user_id)
    return db.query(Board).filter(Board.project_id == project_id).all()


def create_board(db: Session, project_id: int, data: BoardCreate, user_id: int) -> Board:
    assert_member(db, project_id, user_id)
    board = Board(project_id=project_id, **data.model_dump())
    db.add(board)
    db.flush()
    # Add default columns
    for i, col_name in enumerate(["To Do", "In Progress", "Done"]):
        db.add(Column(board_id=board.id, name=col_name, position=i))
    db.commit()
    db.refresh(board)
    return board


def update_board(db: Session, board_id: int, data: BoardUpdate, user_id: int) -> Board:
    board = _get_board_or_404(db, board_id)
    assert_admin(db, board.project_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(board, field, value)
    db.commit()
    db.refresh(board)
    return board


def delete_board(db: Session, board_id: int, user_id: int) -> None:
    board = _get_board_or_404(db, board_id)
    assert_admin(db, board.project_id, user_id)
    db.delete(board)
    db.commit()


def create_column(db: Session, board_id: int, data: ColumnCreate, user_id: int) -> Column:
    board = _get_board_or_404(db, board_id)
    assert_member(db, board.project_id, user_id)
    col = Column(board_id=board_id, **data.model_dump())
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


def update_column(db: Session, column_id: int, data: ColumnUpdate, user_id: int) -> Column:
    col = _get_column_or_404(db, column_id)
    board = _get_board_or_404(db, col.board_id)
    assert_member(db, board.project_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(col, field, value)
    db.commit()
    db.refresh(col)
    return col


def delete_column(db: Session, column_id: int, user_id: int) -> None:
    col = _get_column_or_404(db, column_id)
    board = _get_board_or_404(db, col.board_id)
    assert_admin(db, board.project_id, user_id)
    db.delete(col)
    db.commit()
