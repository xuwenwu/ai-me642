from __future__ import annotations
from datetime import date, timedelta
import json
from sqlalchemy.orm import Session
from ..auth import hash_password
from ..models import AIPolicy, Assignment, Course, Enrollment, PromptTemplate, Rubric, RubricCriterion, Section, User


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
        "optional_file_types": ["readme", "prompt_log", "figure", "data", "slurm_script"],
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
        "optional_file_types": ["readme", "prompt_log", "figure", "python_analysis", "data", "slurm_script"],
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
        "optional_file_types": ["readme", "prompt_log", "python_analysis", "ovito_script", "slurm_script", "figure", "data"],
        "validation_settings": {"energy_drift_warning_threshold": 0.05},
        "interpretation_prompts": [
            "What does the total-energy drift suggest about timestep stability?",
            "How do pressure and temperature fluctuations affect your interpretation?",
            "Which validation checks support your conclusion, and which require caution?",
            "What AI assistance did you use, and how did validation change your final answer?",
        ],
    },
]

AI_POLICY = {
    "title": "ME642 Responsible AI Use Policy",
    "body": (
        "AI tools may support brainstorming, debugging, code explanation, and reflection on validation evidence. "
        "Students remain responsible for every scientific claim, parameter choice, file submitted, and interpretation. "
        "Do not use AI to fabricate simulation output, hide uncertainty, or replace validation. If AI assistance shaped "
        "the work, record what was accepted, rejected, manually revised, and checked against evidence."
    ),
    "allowed_tools": ["ChatGPT", "GitHub Copilot", "Claude", "Gemini"],
    "disclosure_requirements": [
        "Record the AI tool, task purpose, and prompt or prompt summary.",
        "Summarize the AI output in your own words.",
        "Identify accepted and rejected suggestions.",
        "Describe manual edits and validation performed after AI assistance.",
        "State remaining concerns or uncertainties before submission.",
    ],
    "assistant_enabled": False,
    "assistant_provider": "offline",
    "assistant_model": "",
    "assistant_system_prompt": (
        "You are a cautious ME642 course assistant. Help students plan checks, debug reasoning, and "
        "interpret validation evidence. Do not fabricate simulation outputs, grades, or final scientific claims."
    ),
    "assistant_retention_days": 180,
}

PROMPT_TEMPLATES = [
    {
        "title": "LAMMPS debugging check",
        "task_type": "lammps_debugging",
        "prompt_text": (
            "Help me inspect this LAMMPS input/log for errors, warnings, thermo columns, physical assumptions, "
            "and missing validation evidence. Do not claim the simulation is scientifically valid unless the "
            "evidence supports it."
        ),
        "checklist": [
            "Check for fatal LAMMPS errors and warnings.",
            "Identify required thermo columns and missing outputs.",
            "Separate syntax or workflow advice from scientific conclusions.",
            "List validation steps I should perform manually.",
        ],
    },
    {
        "title": "Script generation guardrails",
        "task_type": "lammps_script",
        "prompt_text": (
            "Draft or revise a LAMMPS script for the stated material model. Include comments for assumptions, "
            "units, ensemble, timestep, boundary conditions, and outputs I must validate before submission."
        ),
        "checklist": [
            "Verify units, potential style, and atom definitions.",
            "Confirm ensemble and thermostat/barostat choices.",
            "Add reproducible thermo and dump outputs.",
            "Run a short test and inspect validation results.",
        ],
    },
    {
        "title": "Data analysis interpretation",
        "task_type": "data_analysis",
        "prompt_text": (
            "Help design an analysis plan for these MD outputs. Suggest plots, sanity checks, and caveats, "
            "but keep conclusions conditional on the actual validation evidence."
        ),
        "checklist": [
            "Choose plots that match the physical question.",
            "Check trends against expected units and ranges.",
            "Flag uncertainty, sampling limits, and equilibration concerns.",
            "Connect any conclusion to specific evidence.",
        ],
    },
    {
        "title": "Concept explanation",
        "task_type": "concept_explanation",
        "prompt_text": (
            "Explain this materials-modeling concept for ME642. Include assumptions, common mistakes, and "
            "questions I should answer before applying it to my simulation."
        ),
        "checklist": [
            "Identify assumptions and limits.",
            "Translate the concept to the assignment context.",
            "List checks that would confirm the idea in data.",
            "Note where instructor or source verification is needed.",
        ],
    },
]


def seed(db: Session) -> None:
    users_by_email: dict[str, User] = {}
    for email, full_name, role in USERS:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email, full_name=full_name, role=role, hashed_password=hash_password("password123"))
            db.add(user)
            db.flush()
        users_by_email[email] = user

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

    policy = db.query(AIPolicy).filter_by(course_id=course.id).first()
    if not policy:
        policy = AIPolicy(course_id=course.id)
        db.add(policy)
        db.flush()
    policy.title = AI_POLICY["title"]
    policy.body = AI_POLICY["body"]
    policy.allowed_tools_json = json.dumps(AI_POLICY["allowed_tools"])
    policy.disclosure_requirements_json = json.dumps(AI_POLICY["disclosure_requirements"])
    policy.assistant_enabled = AI_POLICY["assistant_enabled"]
    policy.assistant_provider = AI_POLICY["assistant_provider"]
    policy.assistant_model = AI_POLICY["assistant_model"]
    policy.assistant_system_prompt = AI_POLICY["assistant_system_prompt"]
    policy.assistant_retention_days = AI_POLICY["assistant_retention_days"]

    for item in PROMPT_TEMPLATES:
        template = db.query(PromptTemplate).filter_by(course_id=course.id, title=item["title"]).first()
        if not template:
            template = PromptTemplate(course_id=course.id, title=item["title"])
            db.add(template)
            db.flush()
        template.task_type = item["task_type"]
        template.prompt_text = item["prompt_text"]
        template.checklist_json = json.dumps(item["checklist"])
        template.status = "active"

    section = db.query(Section).filter_by(course_id=course.id, name="Pilot Section A").first()
    if not section:
        section = Section(course_id=course.id, name="Pilot Section A", term=course.term)
        db.add(section)
        db.flush()

    for email, _, role in USERS:
        user = users_by_email[email]
        enrollment = db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first()
        if not enrollment:
            enrollment = Enrollment(course_id=course.id, user_id=user.id)
            db.add(enrollment)
        enrollment.section_id = section.id
        enrollment.role = role
        enrollment.status = "active"

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
