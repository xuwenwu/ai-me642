from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..auth import create_access_token, hash_password, verify_password
from ..database import get_db
from ..deps import current_user
from ..models import User
from ..schemas import AuthOut, ChangePasswordIn, LoginIn, UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> AuthOut:
    user = db.query(User).filter_by(email=payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive. Contact your instructor.")
    return AuthOut(access_token=create_access_token(user.email), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.post("/change-password", response_model=UserOut)
def change_password(payload: ChangePasswordIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")
    user.hashed_password = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(user)
    return user
