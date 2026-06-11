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

export type ValidationReport = {
  id: number;
  status: string;
  summary: string;
  checks: ValidationCheck[];
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
};

