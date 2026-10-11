from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import Token, TokenRefresh, LoginRequest
from app.schemas.user import UserCreate, UserOut, PasswordResetRequest, PasswordReset
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    user = user_service.create_user(db, data)
    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = user_service.authenticate_user(db, data.email, data.password)
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=Token)
def refresh_token(data: TokenRefresh, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    user = user_service.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/password-reset/request")
def request_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    token = user_service.request_password_reset(db, data.email)
    # In production, email the token. Return it here for demo/dev purposes.
    return {"message": "Reset token generated", "reset_token": token}


@router.post("/password-reset/confirm")
def confirm_reset(data: PasswordReset, db: Session = Depends(get_db)):
    user_service.reset_password(db, data.token, data.new_password)
    return {"message": "Password reset successful"}
