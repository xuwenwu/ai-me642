from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import current_user, ensure_owner_or_staff
from ..models import Submission, User
from ..schemas import ValidationReportOut
from ..services.validation_engine import validate_submission


router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/submissions/{submission_id}", response_model=ValidationReportOut)
def run_validation(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    submission = db.get(Submission, submission_id)
    if not submission:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Submission not found")
    ensure_owner_or_staff(submission.user_id, user)
    return validate_submission(db, submission)

