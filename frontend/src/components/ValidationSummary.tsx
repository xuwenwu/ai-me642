import type { Assignment, Submission, ValidationReport } from '@/lib/types';

export const fileTypeLabels: Record<string, string> = {
  lammps_input: 'LAMMPS input',
  lammps_log: 'LAMMPS log',
  readme: 'README',
  prompt_log: 'Prompt upload',
  python_analysis: 'Analysis script',
  ovito_script: 'OVITO script',
  figure: 'Figure',
  data: 'Data file',
  other: 'Other',
};

const defaultRequiredFiles = ['lammps_input', 'lammps_log'];
const defaultOptionalEvidence = ['readme', 'python_analysis', 'ovito_script', 'figure', 'prompt_log'];

function evidenceItems(assignment: Assignment | undefined) {
  const required = assignment?.required_file_types?.length ? assignment.required_file_types : defaultRequiredFiles;
  const optional = assignment?.optional_file_types?.length ? assignment.optional_file_types : defaultOptionalEvidence;
  return {
    required: required.map((type) => ({ type, label: fileTypeLabels[type] ?? type })),
    optional: optional.map((type) => ({ type, label: fileTypeLabels[type] ?? type })),
  };
}

function countChecks(report: ValidationReport | undefined, status: string) {
  return report?.checks.filter((check) => check.status === status).length ?? 0;
}

export function nextSubmissionAction(submission: Submission | undefined, assignment?: Assignment) {
  if (!submission) return 'Create a submission';
  const fileTypes = new Set(submission.files.map((file) => file.file_type));
  const { required } = evidenceItems(assignment);
  const missingRequired = required.filter((file) => !fileTypes.has(file.type));
  if (missingRequired.length) return `Upload ${missingRequired.map((file) => file.label).join(' and ')}`;
  if (!submission.validation_reports[0]) return 'Run validation';
  if (!submission.student_interpretation.trim()) return 'Write interpretation';
  if (submission.status !== 'submitted') return 'Submit package';
  return 'Submitted';
}

export function EvidenceChecklist({ submission, assignment }: { submission: Submission; assignment?: Assignment }) {
  const fileTypes = new Set(submission.files.map((file) => file.file_type));
  const { required, optional } = evidenceItems(assignment);

  return (
    <div className="evidence-list">
      {required.map((item) => {
        const present = fileTypes.has(item.type);
        return (
          <span key={item.type} className={`evidence-pill ${present ? 'present' : 'missing'}`}>
            {item.label}: {present ? 'present' : 'required'}
          </span>
        );
      })}
      {optional.map((item) => {
        const present = fileTypes.has(item.type);
        return (
          <span key={item.type} className={`evidence-pill ${present ? 'present' : 'missing'}`}>
            {item.label}: {present ? 'present' : 'optional'}
          </span>
        );
      })}
    </div>
  );
}

export function ValidationSummary({ submission, report }: { submission: Submission; report?: ValidationReport }) {
  const cueCounts = report?.interpretation_notes.reduce<Record<string, number>>((acc, note) => {
    acc[note.status] = (acc[note.status] ?? 0) + 1;
    return acc;
  }, {}) ?? {};

  return (
    <div className="summary-strip">
      <div className="summary-item">
        <span>Submission</span>
        <strong>{submission.status}</strong>
      </div>
      <div className="summary-item">
        <span>Files</span>
        <strong>{submission.files.length}</strong>
      </div>
      <div className="summary-item">
        <span>Validation</span>
        <strong>{report?.status ?? 'not run'}</strong>
      </div>
      <div className="summary-item">
        <span>Passed</span>
        <strong>{countChecks(report, 'passed')}</strong>
      </div>
      <div className="summary-item">
        <span>Warnings</span>
        <strong>{countChecks(report, 'warning') + countChecks(report, 'needs_review')}</strong>
      </div>
      <div className="summary-item">
        <span>Failed</span>
        <strong>{countChecks(report, 'failed')}</strong>
      </div>
      <div className="summary-item">
        <span>Cues</span>
        <strong>{report ? `${cueCounts.supported ?? 0}/${report.interpretation_notes.length}` : '0'}</strong>
      </div>
    </div>
  );
}
