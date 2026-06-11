export type User = {
  id: number;
  email: string;
  full_name: string;
  role: 'student' | 'ta' | 'instructor';
};

export type Criterion = {
  id: number;
  name: string;
  description: string;
  max_points: number;
  sort_order: number;
};

export type Assignment = {
  id: number;
  title: string;
  description: string;
  assignment_type: string;
  due_date: string | null;
  total_points: number;
  status: string;
  validation_profile: string;
  required_file_types: string[];
  optional_file_types: string[];
  validation_settings: Record<string, unknown>;
  interpretation_prompts: string[];
  criteria: Criterion[];
};

export type ProjectSpec = {
  id: number;
  title: string;
  material_system: string;
  research_question: string;
  physical_property: string;
  atomistic_model: string;
  interatomic_potential: string;
  ensemble: string;
  status: string;
};

export type PromptLog = {
  id: number;
  title: string;
  ai_tool_name: string;
  task_type: string;
  prompt_text: string;
  validation_performed: string;
  remaining_concerns: string;
};

export type FileArtifact = {
  id: number;
  original_filename: string;
  file_type: string;
  size_bytes: number;
};

export type ValidationCheck = {
  id: number;
  check_type: string;
  status: string;
  severity: string;
  message: string;
  evidence: string;
};

export type ThermoSeries = {
  source: string;
  x_field: string;
  columns: string[];
  points: Array<Record<string, number>>;
};

export type InterpretationNote = {
  topic: string;
  status: 'supported' | 'needs_review' | 'needs_context' | 'concern' | string;
  message: string;
  evidence: string;
};

export type ValidationReport = {
  id: number;
  status: string;
  summary: string;
  validation_profile: string;
  checks: ValidationCheck[];
  thermo_series: ThermoSeries[];
  interpretation_notes: InterpretationNote[];
};

export type GradeSummary = {
  id: number;
  rubric_score: number;
  late_penalty: number;
  final_score: number;
  feedback: string;
  graded_at: string;
};

export type Submission = {
  id: number;
  assignment_id: number;
  user_id: number;
  project_id: number | null;
  title: string;
  status: string;
  student_interpretation: string;
  files: FileArtifact[];
  validation_reports: ValidationReport[];
  grade: GradeSummary | null;
};

export type AssignmentAnalytics = {
  assignment_id: number;
  title: string;
  due_date: string | null;
  total_students: number;
  missing_count: number;
  draft_count: number;
  submitted_count: number;
  validation_not_run_count: number;
  validation_warning_count: number;
  validation_failed_count: number;
  graded_count: number;
  ungraded_submitted_count: number;
  needs_attention_count: number;
};

export type NeedsAttention = {
  submission_id: number;
  student_id: number;
  student_name: string;
  student_email: string;
  assignment_id: number;
  assignment_title: string;
  status: string;
  validation_status: string;
  grade_state: string;
  reasons: string[];
  updated_at: string;
};

export type InstructorAnalytics = {
  total_students: number;
  total_assignments: number;
  total_submissions: number;
  submitted_count: number;
  graded_count: number;
  needs_attention_count: number;
  assignments: AssignmentAnalytics[];
  needs_attention: NeedsAttention[];
};

export type RosterStudent = {
  student_id: number;
  full_name: string;
  email: string;
  section: string;
  total_assignments: number;
  submissions_count: number;
  submitted_count: number;
  graded_count: number;
  warning_count: number;
  missing_count: number;
};
