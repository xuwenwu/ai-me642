from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import current_user
from ..models import Assignment, User
from ..schemas import AssignmentOut, RubricCriterionOut


router = APIRouter(prefix="/assignments", tags=["assignments"])


def _assignment_out(assignment: Assignment) -> AssignmentOut:
    criteria = assignment.rubric.criteria if assignment.rubric else []
    return AssignmentOut(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        assignment_type=assignment.assignment_type,
        due_date=assignment.due_date,
        total_points=assignment.total_points,
        status=assignment.status,
        criteria=[RubricCriterionOut.model_validate(c) for c in criteria],
    )


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> list[AssignmentOut]:
    assignments = db.query(Assignment).filter_by(status="published").order_by(Assignment.id).all()
    return [_assignment_out(a) for a in assignments]


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> AssignmentOut:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Assignment not found")
    return _assignment_out(assignment)

