from __future__ import annotations
from datetime import UTC, datetime
import json
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    term: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    name: Mapped[str] = mapped_column(String(128))
    term: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    course = relationship("Course")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_enrollment_course_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(32), default="student")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    course = relationship("Course")
    section = relationship("Section")
    user = relationship("User")


class AIPolicy(Base):
    __tablename__ = "ai_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), unique=True)
    title: Mapped[str] = mapped_column(String(255), default="Responsible AI Use Policy")
    body: Mapped[str] = mapped_column(Text, default="")
    allowed_tools_json: Mapped[str] = mapped_column(Text, default="[]")
    disclosure_requirements_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    course = relationship("Course")

    @property
    def allowed_tools(self) -> list[str]:
        return _json_list(self.allowed_tools_json, [])

    @property
    def disclosure_requirements(self) -> list[str]:
        return _json_list(self.disclosure_requirements_json, [])


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[str] = mapped_column(String(64), default="lammps_debugging")
    prompt_text: Mapped[str] = mapped_column(Text, default="")
    checklist_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    course = relationship("Course")

    @property
    def checklist(self) -> list[str]:
        return _json_list(self.checklist_json, [])


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    assignment_type: Mapped[str] = mapped_column(String(64))
    due_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_points: Mapped[float] = mapped_column(Float, default=100)
    status: Mapped[str] = mapped_column(String(32), default="published")
    validation_profile: Mapped[str] = mapped_column(String(64), default="lammps_basic_health")
    required_file_types_json: Mapped[str] = mapped_column(Text, default='["lammps_input", "lammps_log"]')
    optional_file_types_json: Mapped[str] = mapped_column(Text, default='["readme", "prompt_log", "python_analysis", "ovito_script", "slurm_script", "figure"]')
    validation_settings_json: Mapped[str] = mapped_column(Text, default="{}")
    interpretation_prompts_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    course = relationship("Course")
    rubric = relationship("Rubric", back_populates="assignment", uselist=False, cascade="all, delete-orphan")

    @property
    def required_file_types(self) -> list[str]:
        return _json_list(self.required_file_types_json, ["lammps_input", "lammps_log"])

    @property
    def optional_file_types(self) -> list[str]:
        return _json_list(self.optional_file_types_json, ["readme", "prompt_log", "python_analysis", "ovito_script", "slurm_script", "figure"])

    @property
    def validation_settings(self) -> dict:
        return _json_dict(self.validation_settings_json)

    @property
    def interpretation_prompts(self) -> list[str]:
        return _json_list(self.interpretation_prompts_json, [])


class Rubric(Base):
    __tablename__ = "rubrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), unique=True)
    title: Mapped[str] = mapped_column(String(255))

    assignment = relationship("Assignment", back_populates="rubric")
    criteria = relationship("RubricCriterion", order_by="RubricCriterion.sort_order", cascade="all, delete-orphan")


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    max_points: Mapped[float] = mapped_column(Float)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProjectSpecification(Base):
    __tablename__ = "project_specifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    material_system: Mapped[str] = mapped_column(Text, default="")
    research_question: Mapped[str] = mapped_column(Text, default="")
    physical_property: Mapped[str] = mapped_column(Text, default="")
    atomistic_model: Mapped[str] = mapped_column(Text, default="")
    interatomic_potential: Mapped[str] = mapped_column(Text, default="")
    potential_type: Mapped[str] = mapped_column(String(128), default="")
    ensemble: Mapped[str] = mapped_column(String(128), default="")
    boundary_conditions: Mapped[str] = mapped_column(Text, default="")
    temperature_pressure_conditions: Mapped[str] = mapped_column(Text, default="")
    expected_outputs: Mapped[str] = mapped_column(Text, default="")
    validation_strategy: Mapped[str] = mapped_column(Text, default="")
    computational_resources: Mapped[str] = mapped_column(Text, default="")
    risks_limitations: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    user = relationship("User")
    course = relationship("Course")


class PromptLogEntry(Base):
    __tablename__ = "prompt_log_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project_specifications.id"), nullable=True)
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    ai_tool_name: Mapped[str] = mapped_column(String(255), default="")
    task_type: Mapped[str] = mapped_column(String(64), default="lammps_script")
    prompt_text: Mapped[str] = mapped_column(Text, default="")
    ai_output_summary: Mapped[str] = mapped_column(Text, default="")
    accepted_parts: Mapped[str] = mapped_column(Text, default="")
    rejected_parts: Mapped[str] = mapped_column(Text, default="")
    manual_edits: Mapped[str] = mapped_column(Text, default="")
    validation_performed: Mapped[str] = mapped_column(Text, default="")
    remaining_concerns: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    user = relationship("User")
    project = relationship("ProjectSpecification")
    assignment = relationship("Assignment")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "user_id", name="uq_submission_assignment_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project_specifications.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    student_interpretation: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    assignment = relationship("Assignment")
    user = relationship("User")
    project = relationship("ProjectSpecification")
    files = relationship("FileArtifact", cascade="all, delete-orphan")
    validation_reports = relationship("ValidationReport", cascade="all, delete-orphan", order_by="desc(ValidationReport.created_at)")
    grade = relationship("Grade", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class FileArtifact(Base):
    __tablename__ = "file_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    file_type: Mapped[str] = mapped_column(String(64))
    mime_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    status: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text)
    validation_profile: Mapped[str] = mapped_column(String(64), default="lammps_basic_health")
    thermo_json: Mapped[str] = mapped_column(Text, default="[]")
    interpretation_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    checks = relationship("ValidationCheck", cascade="all, delete-orphan")

    @property
    def thermo_series(self) -> list[dict]:
        try:
            parsed = json.loads(self.thermo_json or "[]")
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []

    @property
    def interpretation_notes(self) -> list[dict]:
        try:
            parsed = json.loads(self.interpretation_json or "[]")
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []


def _json_list(raw: str, fallback: list[str]) -> list[str]:
    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return fallback
    return [str(item) for item in parsed] if isinstance(parsed, list) else fallback


def _json_dict(raw: str) -> dict:
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


class ValidationCheck(Base):
    __tablename__ = "validation_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    validation_report_id: Mapped[int] = mapped_column(ForeignKey("validation_reports.id"))
    check_type: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    grader_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rubric_score: Mapped[float] = mapped_column(Float, default=0)
    late_penalty: Mapped[float] = mapped_column(Float, default=0)
    final_score: Mapped[float] = mapped_column(Float, default=0)
    feedback: Mapped[str] = mapped_column(Text, default="")
    graded_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    submission = relationship("Submission", back_populates="grade")
    criterion_scores = relationship("CriterionScore", cascade="all, delete-orphan")
    grader = relationship("User")


class CriterionScore(Base):
    __tablename__ = "criterion_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"))
    criterion_id: Mapped[int] = mapped_column(ForeignKey("rubric_criteria.id"))
    score: Mapped[float] = mapped_column(Float, default=0)
    comment: Mapped[str] = mapped_column(Text, default="")

    criterion = relationship("RubricCriterion")
