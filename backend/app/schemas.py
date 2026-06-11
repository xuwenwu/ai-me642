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
    validation_profile: str
    required_file_types: list[str] = Field(default_factory=list)
    optional_file_types: list[str] = Field(default_factory=list)
    validation_settings: dict = Field(default_factory=dict)
    interpretation_prompts: list[str] = Field(default_factory=list)
    criteria: list[RubricCriterionOut] = Field(default_factory=list)


class AssignmentManageIn(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    assignment_type: str = "lab"
    due_date: str | None = None
    total_points: float = 100
    status: str = "published"
    validation_profile: str = "lammps_basic_health"
    required_file_types: list[str] = Field(default_factory=lambda: ["lammps_input", "lammps_log"])
    optional_file_types: list[str] = Field(default_factory=list)
    validation_settings: dict = Field(default_factory=dict)
    interpretation_prompts: list[str] = Field(default_factory=list)


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


class AIPolicyIn(BaseModel):
    title: str = Field(min_length=1)
    body: str = ""
    allowed_tools: list[str] = Field(default_factory=list)
    disclosure_requirements: list[str] = Field(default_factory=list)


class AIPolicyOut(AIPolicyIn):
    id: int
    course_id: int
    updated_at: datetime


class PromptTemplateIn(BaseModel):
    title: str = Field(min_length=1)
    task_type: str = "lammps_debugging"
    prompt_text: str = ""
    checklist: list[str] = Field(default_factory=list)
    status: str = "active"


class PromptTemplateOut(PromptTemplateIn):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime


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
    validation_profile: str
    created_at: datetime
    checks: list[ValidationCheckOut] = Field(default_factory=list)
    thermo_series: list[ThermoSeriesOut] = Field(default_factory=list)
    interpretation_notes: list[InterpretationNoteOut] = Field(default_factory=list)


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
    criterion_scores: list[CriterionScoreOut] = Field(default_factory=list)


class GradeSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rubric_score: float
    late_penalty: float
    final_score: float
    feedback: str
    graded_at: datetime


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
    files: list[FileArtifactOut] = Field(default_factory=list)
    validation_reports: list[ValidationReportOut] = Field(default_factory=list)
    grade: GradeSummaryOut | None = None


class AssignmentAnalyticsOut(BaseModel):
    assignment_id: int
    title: str
    due_date: str | None
    total_students: int
    missing_count: int
    draft_count: int
    submitted_count: int
    validation_not_run_count: int
    validation_warning_count: int
    validation_failed_count: int
    ai_disclosure_missing_count: int
    graded_count: int
    ungraded_submitted_count: int
    needs_attention_count: int


class NeedsAttentionOut(BaseModel):
    submission_id: int
    student_id: int
    student_name: str
    student_email: str
    assignment_id: int
    assignment_title: str
    status: str
    validation_status: str
    grade_state: str
    reasons: list[str] = Field(default_factory=list)
    updated_at: datetime


class InstructorAnalyticsOut(BaseModel):
    total_students: int
    total_assignments: int
    total_submissions: int
    submitted_count: int
    graded_count: int
    needs_attention_count: int
    ai_disclosure_missing_count: int
    assignments: list[AssignmentAnalyticsOut] = Field(default_factory=list)
    needs_attention: list[NeedsAttentionOut] = Field(default_factory=list)


class GradebookCellOut(BaseModel):
    assignment_id: int
    assignment_title: str
    total_points: float
    submission_id: int | None = None
    submission_status: str = "missing"
    validation_status: str = "missing"
    grade_state: str = "missing"
    final_score: float | None = None
    submitted_at: datetime | None = None
    updated_at: datetime | None = None


class GradebookStudentOut(BaseModel):
    student_id: int
    full_name: str
    email: str
    section: str
    submitted_count: int
    graded_count: int
    missing_count: int
    warning_count: int
    current_score: float
    possible_score: float
    assignments: list[GradebookCellOut] = Field(default_factory=list)


class GradebookAssignmentSummaryOut(BaseModel):
    assignment_id: int
    title: str
    due_date: str | None
    total_points: float
    submitted_count: int
    graded_count: int
    ungraded_count: int
    missing_count: int
    warning_count: int
    failed_count: int
    average_score: float | None = None


class GradebookOut(BaseModel):
    total_students: int
    total_assignments: int
    total_submitted: int
    total_graded: int
    total_missing: int
    current_average_score: float | None = None
    assignments: list[GradebookAssignmentSummaryOut] = Field(default_factory=list)
    students: list[GradebookStudentOut] = Field(default_factory=list)


class RosterStudentOut(BaseModel):
    student_id: int
    full_name: str
    email: str
    section: str
    total_assignments: int
    submissions_count: int
    submitted_count: int
    graded_count: int
    warning_count: int
    missing_count: int


class RosterStudentIn(BaseModel):
    full_name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    section: str = "Pilot Section A"
    password: str = "password123"


class RosterImportIn(BaseModel):
    csv_text: str = Field(min_length=1)
    default_section: str = "Pilot Section A"


class RosterImportOut(BaseModel):
    created_count: int
    updated_count: int
    skipped_count: int
    errors: list[str] = Field(default_factory=list)
