from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import current_user, ensure_owner_or_staff
from ..models import PromptLogEntry, User
from ..schemas import PromptLogIn, PromptLogOut


router = APIRouter(prefix="/prompt-logs", tags=["prompt-logs"])


@router.get("", response_model=list[PromptLogOut])
def list_prompt_logs(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[PromptLogEntry]:
    query = db.query(PromptLogEntry)
    if user.role not in {"instructor", "ta"}:
        query = query.filter_by(user_id=user.id)
    return query.order_by(PromptLogEntry.created_at.desc()).all()


@router.post("", response_model=PromptLogOut)
def create_prompt_log(
    payload: PromptLogIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PromptLogEntry:
    prompt = PromptLogEntry(**payload.model_dump(), user_id=user.id)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptLogOut)
def get_prompt_log(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PromptLogEntry:
    prompt = db.get(PromptLogEntry, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt log not found")
    ensure_owner_or_staff(prompt.user_id, user)
    return prompt

