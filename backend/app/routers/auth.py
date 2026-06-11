from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..auth import create_access_token, verify_password
from ..database import get_db
from ..deps import current_user
from ..models import User
from ..schemas import AuthOut, LoginIn, UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> AuthOut:
    user = db.query(User).filter_by(email=payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return AuthOut(access_token=create_access_token(user.email), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user

