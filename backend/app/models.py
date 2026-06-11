from __future__ import annotations
from datetime import UTC, datetime
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    course = relationship("Course")
    rubric = relationship("Rubric", back_populates="assignment", uselist=False, cascade="all, delete-orphan")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    checks = relationship("ValidationCheck", cascade="all, delete-orphan")


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
