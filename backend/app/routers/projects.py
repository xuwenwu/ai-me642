from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import current_user, ensure_owner_or_staff
from ..models import Course, ProjectSpecification, User
from ..schemas import ProjectSpecIn, ProjectSpecOut


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSpecOut])
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[ProjectSpecification]:
    query = db.query(ProjectSpecification)
    if user.role not in {"instructor", "ta"}:
        query = query.filter_by(user_id=user.id)
    return query.order_by(ProjectSpecification.created_at.desc()).all()


@router.post("", response_model=ProjectSpecOut)
def create_project(
    payload: ProjectSpecIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ProjectSpecification:
    course = db.query(Course).filter_by(code="ME642").first()
    if not course:
        raise HTTPException(status_code=500, detail="ME642 course seed data is missing")
    project = ProjectSpecification(**payload.model_dump(), user_id=user.id, course_id=course.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectSpecOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ProjectSpecification:
    project = db.get(ProjectSpecification, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_owner_or_staff(project.user_id, user)
    return project

