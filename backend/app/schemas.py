from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str


class LoginIn(BaseModel):
    email: str
    password: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RubricCriterionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    max_points: float
    sort_order: int


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    assignment_type: str
    due_date: str | None
    total_points: float
    status: str
    criteria: list[RubricCriterionOut] = []


class ProjectSpecIn(BaseModel):
    title: str
    material_system: str = ""
    research_question: str = ""
    physical_property: str = ""
    atomistic_model: str = ""
    interatomic_potential: str = ""
    potential_type: str = ""
    ensemble: str = ""
    boundary_conditions: str = ""
    temperature_pressure_conditions: str = ""
    expected_outputs: str = ""
    validation_strategy: str = ""
    computational_resources: str = ""
    risks_limitations: str = ""


class ProjectSpecOut(ProjectSpecIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: str
    created_at: datetime
    updated_at: datetime


class PromptLogIn(BaseModel):
    title: str
    project_id: int | None = None
    assignment_id: int | None = None
    ai_tool_name: str = ""
    task_type: str = "lammps_script"
    prompt_text: str = ""
    ai_output_summary: str = ""
    accepted_parts: str = ""
    rejected_parts: str = ""
    manual_edits: str = ""
    validation_performed: str = ""
    remaining_concerns: str = ""


class PromptLogOut(PromptLogIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime


class SubmissionCreate(BaseModel):
    assignment_id: int
    project_id: int | None = None
    title: str


class InterpretationIn(BaseModel):
    student_interpretation: str = Field(min_length=1)


class FileArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_type: str
    mime_type: str
    size_bytes: int
    uploaded_at: datetime


class ValidationCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    check_type: str
    status: str
    severity: str
    message: str
    evidence: str
    created_at: datetime


class ThermoSeriesOut(BaseModel):
    source: str
    x_field: str
    columns: list[str]
    points: list[dict[str, float]]


class InterpretationNoteOut(BaseModel):
    topic: str
    status: str
    message: str
    evidence: str = ""


class ValidationReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    summary: str
    created_at: datetime
    checks: list[ValidationCheckOut] = []
    thermo_series: list[ThermoSeriesOut] = []
    interpretation_notes: list[InterpretationNoteOut] = []


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    user_id: int
    project_id: int | None
    title: str
    status: str
    student_interpretation: str
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    files: list[FileArtifactOut] = []
    validation_reports: list[ValidationReportOut] = []


class CriterionScoreIn(BaseModel):
    criterion_id: int
    score: float
    comment: str = ""


class GradeIn(BaseModel):
    submission_id: int
    criterion_scores: list[CriterionScoreIn]
    late_penalty: float = 0
    feedback: str = ""


class CriterionScoreOut(CriterionScoreIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    grader_id: int
    rubric_score: float
    late_penalty: float
    final_score: float
    feedback: str
    graded_at: datetime
    criterion_scores: list[CriterionScoreOut] = []
