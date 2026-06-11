from __future__ import annotations
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from .auth import verify_access_token
from .database import get_db
from .models import User


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    email = verify_access_token(authorization.split(" ", 1)[1])
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def staff_user(user: User = Depends(current_user)) -> User:
    if user.role not in {"instructor", "ta"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor/TA role required")
    return user


def ensure_owner_or_staff(resource_user_id: int, user: User) -> None:
    if user.role in {"instructor", "ta"}:
        return
    if resource_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this resource")

