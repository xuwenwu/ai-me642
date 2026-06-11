from __future__ import annotations
from datetime import date, timedelta
import json
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

ASSIGNMENTS = [
    {
        "title": "Lab 1: LAMMPS Setup and Equilibration",
        "description": (
            "Prepare a reproducible LAMMPS setup, run an initial equilibration, inspect basic log health, "
            "and document AI-assisted workflow decisions."
        ),
        "assignment_type": "lab",
        "due_offset_days": 14,
        "validation_profile": "lammps_basic_health",
        "required_file_types": ["lammps_input", "lammps_log"],
        "optional_file_types": ["readme", "prompt_log", "figure", "data"],
        "validation_settings": {},
        "interpretation_prompts": [
            "What physical system and assumptions does your setup represent?",
            "What evidence shows the run completed without fatal LAMMPS errors?",
            "What AI assistance did you accept, reject, or manually revise?",
            "What limitations remain before using this setup for production analysis?",
        ],
    },
    {
        "title": "Lab 2: NVT Temperature Control",
        "description": (
            "Run and interpret NVT molecular dynamics simulations, inspect temperature control behavior, "
            "and connect thermostat evidence to scientific conclusions."
        ),
        "assignment_type": "lab",
        "due_offset_days": 28,
        "validation_profile": "nvt_temperature_control",
        "required_file_types": ["lammps_input", "lammps_log"],
        "optional_file_types": ["readme", "prompt_log", "figure", "python_analysis", "data"],
        "validation_settings": {"target_temperature": 300, "temperature_tolerance": 75},
        "interpretation_prompts": [
            "What target temperature did you intend to control around, and why?",
            "What does the thermo trace suggest about temperature equilibration and stability?",
            "How did you distinguish thermostat behavior from physical conclusions?",
            "What validation or AI-assisted advice did you use, and what did you verify manually?",
        ],
    },
    {
        "title": "Lab 3: NVE Energy Conservation and Timestep Stability",
        "description": (
            "Run and interpret NVE molecular dynamics simulations, compare timestep choices, "
            "inspect total-energy drift, and disclose AI-assisted workflow decisions."
        ),
        "assignment_type": "lab",
        "due_offset_days": 42,
        "validation_profile": "nve_energy_conservation",
        "required_file_types": ["lammps_input", "lammps_log"],
        "optional_file_types": ["readme", "prompt_log", "python_analysis", "ovito_script", "figure", "data"],
        "validation_settings": {"energy_drift_warning_threshold": 0.05},
        "interpretation_prompts": [
            "What does the total-energy drift suggest about timestep stability?",
            "How do pressure and temperature fluctuations affect your interpretation?",
            "Which validation checks support your conclusion, and which require caution?",
            "What AI assistance did you use, and how did validation change your final answer?",
        ],
    },
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

    for item in ASSIGNMENTS:
        assignment = db.query(Assignment).filter_by(title=item["title"]).first()
        if not assignment:
            assignment = Assignment(course_id=course.id, title=item["title"], description=item["description"], assignment_type=item["assignment_type"])
            db.add(assignment)
            db.flush()

        assignment.course_id = course.id
        assignment.description = item["description"]
        assignment.assignment_type = item["assignment_type"]
        assignment.due_date = str(date(2026, 1, 20) + timedelta(days=item["due_offset_days"]))
        assignment.total_points = 100
        assignment.status = "published"
        assignment.validation_profile = item["validation_profile"]
        assignment.required_file_types_json = json.dumps(item["required_file_types"])
        assignment.optional_file_types_json = json.dumps(item["optional_file_types"])
        assignment.validation_settings_json = json.dumps(item["validation_settings"])
        assignment.interpretation_prompts_json = json.dumps(item["interpretation_prompts"])

        rubric = assignment.rubric or db.query(Rubric).filter_by(assignment_id=assignment.id).first()
        if not rubric:
            rubric = Rubric(assignment_id=assignment.id, title=f"{item['title']} Rubric")
            db.add(rubric)
            db.flush()
        rubric.title = f"{item['title']} Rubric"

        if not rubric.criteria:
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
