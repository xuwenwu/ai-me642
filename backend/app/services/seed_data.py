from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy.orm import Session
from ..auth import hash_password
from ..models import Assignment, Course, Rubric, RubricCriterion, User


USERS = [
    ("student@example.edu", "Ada Student", "student"),
    ("student2@example.edu", "Grace Student", "student"),
    ("ta@example.edu", "Teaching Assistant", "ta"),
    ("instructor@example.edu", "Dr. Instructor", "instructor"),
]

CRITERIA = [
    ("Conceptual correctness", 20, "Materials-modeling assumptions, ensemble choice, and scientific framing are correct."),
    ("Script/workflow correctness", 20, "LAMMPS/OVITO/Python workflow is coherent and reproducible."),
    ("Simulation validation", 25, "Validation evidence is complete, physically reasonable, and interpreted accurately."),
    ("Interpretation and communication", 20, "Student explains findings, limitations, and uncertainty clearly."),
    ("Reproducibility and AI disclosure", 15, "Artifacts, README, prompt logs, manual edits, and concerns are documented."),
]


def seed(db: Session) -> None:
    for email, full_name, role in USERS:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(email=email, full_name=full_name, role=role, hashed_password=hash_password("password123")))

    course = db.query(Course).filter_by(code="ME642").first()
    if not course:
        course = Course(
            code="ME642",
            title="Materials Modeling",
            term="Spring 2026",
            description="Graduate materials modeling course using LAMMPS, OVITO, Python, HPC workflows, and responsible AI assistance.",
        )
        db.add(course)
        db.flush()

    title = "Lab 3: NVE Energy Conservation and Timestep Stability"
    assignment = db.query(Assignment).filter_by(title=title).first()
    if not assignment:
        assignment = Assignment(
            course_id=course.id,
            title=title,
            description=(
                "Run and interpret NVE molecular dynamics simulations, compare timestep choices, "
                "inspect total-energy drift, and disclose AI-assisted workflow decisions."
            ),
            assignment_type="lab",
            due_date=str(date(2026, 1, 20) + timedelta(days=42)),
            total_points=100,
            status="published",
        )
        db.add(assignment)
        db.flush()
        rubric = Rubric(assignment_id=assignment.id, title=f"{title} Rubric")
        db.add(rubric)
        db.flush()
        for order, (name, points, description) in enumerate(CRITERIA, 1):
            db.add(
                RubricCriterion(
                    rubric_id=rubric.id,
                    name=name,
                    description=description,
                    max_points=points,
                    sort_order=order,
                )
            )

    db.commit()

