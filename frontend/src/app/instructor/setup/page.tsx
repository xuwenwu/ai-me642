'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { fileTypeLabels } from '@/components/ValidationSummary';
import { api } from '@/lib/api';
import type { Assignment, AssignmentManageInput, RosterImportResult, RosterStudent } from '@/lib/types';

const fileTypes = ['lammps_input', 'lammps_log', 'readme', 'prompt_log', 'python_analysis', 'ovito_script', 'figure', 'data', 'other'];
const validationProfiles = ['lammps_basic_health', 'nvt_temperature_control', 'nve_energy_conservation'];

const emptyAssignment: AssignmentManageInput = {
  title: '',
  description: '',
  assignment_type: 'lab',
  due_date: '',
  total_points: 100,
  status: 'published',
  validation_profile: 'lammps_basic_health',
  required_file_types: ['lammps_input', 'lammps_log'],
  optional_file_types: ['readme', 'prompt_log'],
  validation_settings: {},
  interpretation_prompts: [],
};

function assignmentForm(assignment: Assignment | undefined): AssignmentManageInput {
  if (!assignment) return emptyAssignment;
  return {
    title: assignment.title,
    description: assignment.description,
    assignment_type: assignment.assignment_type,
    due_date: assignment.due_date || '',
    total_points: assignment.total_points,
    status: assignment.status,
    validation_profile: assignment.validation_profile,
    required_file_types: assignment.required_file_types,
    optional_file_types: assignment.optional_file_types,
    validation_settings: assignment.validation_settings,
    interpretation_prompts: assignment.interpretation_prompts,
  };
}

function toggleValue(values: string[], value: string) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export default function InstructorSetupPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [roster, setRoster] = useState<RosterStudent[]>([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>('new');
  const [assignmentFormState, setAssignmentFormState] = useState<AssignmentManageInput>(emptyAssignment);
  const [settingsText, setSettingsText] = useState('{}');
  const [promptsText, setPromptsText] = useState('');
  const [studentForm, setStudentForm] = useState({ full_name: '', email: '', section: 'Pilot Section A', password: 'password123' });
  const [csvText, setCsvText] = useState('full_name,email,section\n');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [importResult, setImportResult] = useState<RosterImportResult | null>(null);

  const selectedAssignment = useMemo(
    () => assignments.find((assignment) => assignment.id === Number(selectedAssignmentId)),
    [assignments, selectedAssignmentId],
  );

  async function load() {
    const [a, r] = await Promise.all([api<Assignment[]>('/instructor/assignments'), api<RosterStudent[]>('/instructor/roster')]);
    setAssignments(a);
    setRoster(r);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load course setup'));
  }, []);

  useEffect(() => {
    const next = assignmentForm(selectedAssignment);
    setAssignmentFormState(next);
    setSettingsText(JSON.stringify(next.validation_settings, null, 2));
    setPromptsText(next.interpretation_prompts.join('\n'));
  }, [selectedAssignment]);

  async function saveAssignment(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      const validation_settings = JSON.parse(settingsText || '{}') as Record<string, unknown>;
      const payload = {
        ...assignmentFormState,
        title: assignmentFormState.title.trim(),
        due_date: assignmentFormState.due_date || null,
        validation_settings,
        interpretation_prompts: promptsText.split('\n').map((line) => line.trim()).filter(Boolean),
      };
      const path = selectedAssignment ? `/instructor/assignments/${selectedAssignment.id}` : '/instructor/assignments';
      const method = selectedAssignment ? 'PATCH' : 'POST';
      const saved = await api<Assignment>(path, { method, body: JSON.stringify(payload) });
      await load();
      setSelectedAssignmentId(String(saved.id));
      setMessage(`Saved assignment: ${saved.title}`);
    } catch (err) {
      setError(err instanceof SyntaxError ? 'Validation settings must be valid JSON.' : err instanceof Error ? err.message : 'Failed to save assignment');
    }
  }

  async function addStudent(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      const student = await api<RosterStudent>('/instructor/roster/students', { method: 'POST', body: JSON.stringify(studentForm) });
      await load();
      setStudentForm({ full_name: '', email: '', section: student.section || 'Pilot Section A', password: 'password123' });
      setMessage(`Saved student: ${student.full_name}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save student');
    }
  }

  async function importRoster(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');
    setImportResult(null);
    try {
      const result = await api<RosterImportResult>('/instructor/roster/import', {
        method: 'POST',
        body: JSON.stringify({ csv_text: csvText, default_section: 'Pilot Section A' }),
      });
      await load();
      setImportResult(result);
      setMessage(`Roster import complete: ${result.created_count} created, ${result.updated_count} updated.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import roster');
    }
  }

  return (
    <AppShell>
      <div className="section-header">
        <h1>Course Setup</h1>
        <div className="row">
          <Link href="/instructor">Instructor overview</Link>
          <Link href="/instructor/submissions">Review queue</Link>
        </div>
      </div>
      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}
      <div className="grid two">
        <section className="card">
          <h2>Assignment Authoring</h2>
          <label>Assignment<select value={selectedAssignmentId} onChange={(e) => setSelectedAssignmentId(e.target.value)}>
            <option value="new">New assignment</option>
            {assignments.map((assignment) => <option key={assignment.id} value={assignment.id}>{assignment.title}</option>)}
          </select></label>
          <form className="form" onSubmit={saveAssignment} style={{ marginTop: '0.85rem' }}>
            <label>Title<input value={assignmentFormState.title} onChange={(e) => setAssignmentFormState({ ...assignmentFormState, title: e.target.value })} required /></label>
            <label>Description<textarea value={assignmentFormState.description} onChange={(e) => setAssignmentFormState({ ...assignmentFormState, description: e.target.value })} /></label>
            <div className="filter-grid">
              <label>Due date<input value={assignmentFormState.due_date || ''} onChange={(e) => setAssignmentFormState({ ...assignmentFormState, due_date: e.target.value })} placeholder="YYYY-MM-DD" /></label>
              <label>Points<input type="number" min="0" step="1" value={assignmentFormState.total_points} onChange={(e) => setAssignmentFormState({ ...assignmentFormState, total_points: Number(e.target.value) })} /></label>
              <label>Status<select value={assignmentFormState.status} onChange={(e) => setAssignmentFormState({ ...assignmentFormState, status: e.target.value })}>
                <option value="published">Published</option>
                <option value="draft">Draft</option>
                <option value="archived">Archived</option>
              </select></label>
              <label>Validation profile<select value={assignmentFormState.validation_profile} onChange={(e) => setAssignmentFormState({ ...assignmentFormState, validation_profile: e.target.value })}>
                {validationProfiles.map((profile) => <option key={profile} value={profile}>{profile}</option>)}
              </select></label>
            </div>
            <fieldset className="check-panel">
              <legend>Required Evidence</legend>
              {fileTypes.map((type) => (
                <label key={type}><input type="checkbox" checked={assignmentFormState.required_file_types.includes(type)} onChange={() => setAssignmentFormState({ ...assignmentFormState, required_file_types: toggleValue(assignmentFormState.required_file_types, type) })} /> {fileTypeLabels[type] ?? type}</label>
              ))}
            </fieldset>
            <fieldset className="check-panel">
              <legend>Optional Evidence</legend>
              {fileTypes.map((type) => (
                <label key={type}><input type="checkbox" checked={assignmentFormState.optional_file_types.includes(type)} onChange={() => setAssignmentFormState({ ...assignmentFormState, optional_file_types: toggleValue(assignmentFormState.optional_file_types, type) })} /> {fileTypeLabels[type] ?? type}</label>
              ))}
            </fieldset>
            <label>Validation settings JSON<textarea value={settingsText} onChange={(e) => setSettingsText(e.target.value)} /></label>
            <label>Reflection prompts<textarea value={promptsText} onChange={(e) => setPromptsText(e.target.value)} placeholder="One prompt per line" /></label>
            <button>{selectedAssignment ? 'Save assignment' : 'Create assignment'}</button>
          </form>
        </section>

        <section className="card">
          <h2>Roster Setup</h2>
          <form className="form" onSubmit={addStudent}>
            <label>Full name<input value={studentForm.full_name} onChange={(e) => setStudentForm({ ...studentForm, full_name: e.target.value })} required /></label>
            <label>Email<input value={studentForm.email} onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })} required /></label>
            <label>Section<input value={studentForm.section} onChange={(e) => setStudentForm({ ...studentForm, section: e.target.value })} /></label>
            <label>Initial password<input value={studentForm.password} onChange={(e) => setStudentForm({ ...studentForm, password: e.target.value })} /></label>
            <button>Add or update student</button>
          </form>
          <form className="form" onSubmit={importRoster} style={{ marginTop: '1rem' }}>
            <label>CSV import<textarea value={csvText} onChange={(e) => setCsvText(e.target.value)} /></label>
            <button className="secondary">Import roster CSV</button>
          </form>
          {importResult ? (
            <div className="assignment-context" style={{ marginTop: '0.85rem' }}>
              <strong>Import result</strong>
              <p>{importResult.created_count} created, {importResult.updated_count} updated, {importResult.skipped_count} skipped.</p>
              {importResult.errors.map((item) => <p key={item} className="muted">{item}</p>)}
            </div>
          ) : null}
        </section>
      </div>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>Current Roster</h2>
        {roster.length ? (
          <table>
            <thead><tr><th>Student</th><th>Section</th><th>Submissions</th><th>Submitted</th><th>Warnings</th><th>Graded</th><th>Missing</th></tr></thead>
            <tbody>
              {roster.map((student) => (
                <tr key={student.student_id}>
                  <td>{student.full_name}<div className="muted">{student.email}</div></td>
                  <td>{student.section}</td>
                  <td>{student.submissions_count}/{student.total_assignments}</td>
                  <td>{student.submitted_count}</td>
                  <td>{student.warning_count}</td>
                  <td>{student.graded_count}</td>
                  <td>{student.missing_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="muted">No active students found.</p>}
      </section>
    </AppShell>
  );
}
