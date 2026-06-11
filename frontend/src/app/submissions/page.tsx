'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { InterpretationNotes } from '@/components/InterpretationNotes';
import { ThermoPlots } from '@/components/ThermoPlots';
import { EvidenceChecklist, ValidationSummary, fileTypeLabels, nextSubmissionAction } from '@/components/ValidationSummary';
import { ApiError, api, download } from '@/lib/api';
import type { Assignment, FileArtifact, ProjectSpec, Submission, ValidationReport } from '@/lib/types';

const fileTypes = [
  'lammps_input',
  'lammps_log',
  'readme',
  'prompt_log',
  'python_analysis',
  'ovito_script',
  'slurm_script',
  'figure',
  'data',
  'other',
];

export default function SubmissionsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [projects, setProjects] = useState<ProjectSpec[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [createMessage, setCreateMessage] = useState('');
  const [isCreatingSubmission, setIsCreatingSubmission] = useState(false);
  const [createForm, setCreateForm] = useState({ assignment_id: '', project_id: '', title: '' });
  const [fileType, setFileType] = useState('lammps_log');
  const [file, setFile] = useState<File | null>(null);
  const [interpretation, setInterpretation] = useState('');
  const [interpretationMessage, setInterpretationMessage] = useState('');

  const selected = useMemo(() => submissions.find((submission) => submission.id === selectedId) || submissions[0], [submissions, selectedId]);
  const selectedAssignment = useMemo(() => assignments.find((assignment) => assignment.id === selected?.assignment_id), [assignments, selected]);
  const draftAssignment = useMemo(() => assignments.find((assignment) => assignment.id === Number(createForm.assignment_id)), [assignments, createForm.assignment_id]);
  const existingDraftSubmission = useMemo(
    () => submissions.find((submission) => submission.assignment_id === Number(createForm.assignment_id)),
    [submissions, createForm.assignment_id],
  );
  const latestReport = selected?.validation_reports[0];
  const aiDisclosureCheck = latestReport?.checks.find((check) => check.check_type === 'ai_disclosure');
  const aiDisclosureNote = latestReport?.interpretation_notes.find((note) => note.topic === 'AI disclosure');
  const nextAction = nextSubmissionAction(selected, selectedAssignment);

  async function load() {
    const [a, p, s] = await Promise.all([api<Assignment[]>('/assignments'), api<ProjectSpec[]>('/projects'), api<Submission[]>('/submissions')]);
    setAssignments(a);
    setProjects(p);
    setSubmissions(s);
    if (!selectedId && s[0]) setSelectedId(s[0].id);
    return s;
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load submissions'));
  }, []);

  useEffect(() => {
    setInterpretation(selected?.student_interpretation || '');
    setInterpretationMessage('');
  }, [selected?.id]);

  async function createSubmission(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');
    setCreateMessage('');
    const assignmentId = Number(createForm.assignment_id);
    const assignment = assignments.find((item) => item.id === assignmentId);
    if (!assignment) {
      setCreateMessage('Choose an assignment before creating a submission.');
      return;
    }
    const existing = submissions.find((submission) => submission.assignment_id === assignmentId);
    if (existing) {
      setSelectedId(existing.id);
      const nextMessage = `Submission #${existing.id} already exists for this assignment and is now selected below.`;
      setMessage(nextMessage);
      setCreateMessage(nextMessage);
      return;
    }
    setIsCreatingSubmission(true);
    try {
      const title = createForm.title.trim() || `${assignment.title} package`;
      const created = await api<Submission>('/submissions', {
        method: 'POST',
        body: JSON.stringify({
          assignment_id: assignmentId,
          project_id: createForm.project_id ? Number(createForm.project_id) : null,
          title,
        }),
      });
      await load();
      setSelectedId(created.id);
      const nextMessage = `Created submission #${created.id}. It is now selected below.`;
      setMessage(nextMessage);
      setCreateMessage(nextMessage);
      setCreateForm({ ...createForm, title });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const latest = await load();
        const match = latest.find((submission) => submission.assignment_id === assignmentId);
        if (match) {
          setSelectedId(match.id);
          const nextMessage = `Submission #${match.id} already exists for this assignment and is now selected below.`;
          setMessage(nextMessage);
          setCreateMessage(nextMessage);
          return;
        }
      }
      const nextError = err instanceof Error ? err.message : 'Failed to create submission';
      setError(nextError);
      setCreateMessage(nextError);
    } finally {
      setIsCreatingSubmission(false);
    }
  }

  async function uploadArtifact(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || !file) return;
    setError('');
    setMessage('');
    try {
      const form = new FormData();
      form.append('upload', file);
      await api<FileArtifact>(`/submissions/${selected.id}/files?file_type=${encodeURIComponent(fileType)}`, { method: 'POST', body: form });
      await load();
      setFile(null);
      setMessage('Uploaded artifact');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  }

  async function runValidation() {
    if (!selected) return;
    setError('');
    setMessage('');
    try {
      const report = await api<ValidationReport>(`/validation/submissions/${selected.id}`, { method: 'POST' });
      await load();
      setMessage(`Validation completed with status: ${report.status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    }
  }

  async function saveInterpretation() {
    if (!selected) return;
    setError('');
    setMessage('');
    setInterpretationMessage('');
    try {
      await api<Submission>(`/submissions/${selected.id}/interpretation`, {
        method: 'PATCH',
        body: JSON.stringify({ student_interpretation: interpretation }),
      });
      await load();
      setMessage('Saved interpretation');
      setInterpretationMessage('Interpretation saved. You can still revise it before submitting.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save interpretation');
    }
  }

  async function submitAssignment() {
    if (!selected) return;
    setError('');
    setMessage('');
    setInterpretationMessage('');
    try {
      await api<Submission>(`/submissions/${selected.id}/submit`, { method: 'POST' });
      await load();
      setMessage('Submission marked as submitted');
      setInterpretationMessage('Assignment submitted. The dashboard and instructor view will now show this package as submitted.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit');
    }
  }

  return (
    <AppShell>
      <h1>Submission Workflow</h1>
      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}
      <div className="grid two">
        <section className="card">
          <h2>Create Submission</h2>
          <form className="form" onSubmit={createSubmission}>
            <label>Assignment<select value={createForm.assignment_id} onChange={(e) => {
              const nextAssignment = assignments.find((assignment) => assignment.id === Number(e.target.value));
              const currentAssignment = assignments.find((assignment) => assignment.id === Number(createForm.assignment_id));
              const currentAutoTitle = currentAssignment ? `${currentAssignment.title} package` : '';
              setCreateForm({
                ...createForm,
                assignment_id: e.target.value,
                title: !createForm.title || createForm.title === currentAutoTitle ? (nextAssignment ? `${nextAssignment.title} package` : '') : createForm.title,
              });
              setCreateMessage('');
            }} required>
              <option value="">Select assignment</option>
              {assignments.map((assignment) => <option key={assignment.id} value={assignment.id}>{assignment.title}</option>)}
            </select></label>
            {draftAssignment ? (
              <div className="assignment-context">
                <strong>{draftAssignment.validation_profile}</strong>
                <p>{draftAssignment.description}</p>
                <p className="muted">Due: {draftAssignment.due_date || 'not set'} - {draftAssignment.total_points} pts</p>
                {existingDraftSubmission ? <p className="muted">Existing submission #{existingDraftSubmission.id} will be selected instead of creating a duplicate.</p> : null}
              </div>
            ) : null}
            <label>Project<select value={createForm.project_id} onChange={(e) => setCreateForm({ ...createForm, project_id: e.target.value })}>
              <option value="">Optional project</option>
              {projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
            </select></label>
            <label>Title<input value={createForm.title} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} /></label>
            {createMessage ? <div className={createMessage.includes('Failed') || createMessage.includes('Choose') ? 'error' : 'inline-success'} role="status">{createMessage}</div> : null}
            <button disabled={!createForm.assignment_id || isCreatingSubmission}>
              {isCreatingSubmission ? 'Creating...' : existingDraftSubmission ? 'Open existing submission' : 'Create submission'}
            </button>
          </form>
        </section>
        <section className="card">
          <h2>Select Submission</h2>
          <select value={selected?.id || ''} onChange={(e) => setSelectedId(Number(e.target.value))}>
            {submissions.map((submission) => <option key={submission.id} value={submission.id}>#{submission.id} {submission.title}</option>)}
          </select>
          {selected ? (
            <div>
              <p>Status: <strong>{selected.status}</strong></p>
              <p>Next: <strong>{nextAction}</strong></p>
              <p>Assignment: {selectedAssignment?.title || selected.assignment_id}</p>
              <p>Latest validation: {latestReport?.status || 'not run'}</p>
              <p className="muted">Profile: {latestReport?.validation_profile || selectedAssignment?.validation_profile || 'not set'}</p>
            </div>
          ) : <p className="muted">Create a submission to begin.</p>}
        </section>
      </div>
      {selected ? (
        <>
          <section className="card" style={{ marginTop: '1rem' }}>
            <div className="section-header">
              <h2>Evidence Status</h2>
              <span className="status warning">{nextAction}</span>
            </div>
            {selectedAssignment ? (
              <p className="muted">{selectedAssignment.title} - {selectedAssignment.validation_profile}</p>
            ) : null}
            <ValidationSummary submission={selected} report={latestReport} />
            <EvidenceChecklist submission={selected} assignment={selectedAssignment} />
            <div className="assignment-context" style={{ marginTop: '0.85rem' }}>
              <div className="section-header">
                <strong>AI Disclosure</strong>
                <Link href="/prompt-logs">Open prompt logs</Link>
              </div>
              {aiDisclosureCheck ? (
                <p>
                  <span className={`status ${aiDisclosureCheck.status}`}>{aiDisclosureCheck.status}</span> {aiDisclosureCheck.message}
                </p>
              ) : <p className="muted">Run validation to check whether prompt-log evidence is attached.</p>}
              {aiDisclosureNote ? <p className="muted">{aiDisclosureNote.message}</p> : null}
            </div>
          </section>
          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Upload Artifacts</h2>
            <form className="form" onSubmit={uploadArtifact}>
              <label>File type<select value={fileType} onChange={(e) => setFileType(e.target.value)}>
                {fileTypes.map((type) => <option key={type} value={type}>{fileTypeLabels[type] ?? type}</option>)}
              </select></label>
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <button disabled={!file}>Upload</button>
            </form>
            <details className="details-panel" open={selected.files.length > 0}>
              <summary>Uploaded files ({selected.files.length})</summary>
              <table>
                <thead><tr><th>Type</th><th>Name</th><th>Size</th></tr></thead>
                <tbody>{selected.files.map((artifact) => <tr key={artifact.id}><td>{artifact.file_type}</td><td>{artifact.original_filename}</td><td>{artifact.size_bytes}</td></tr>)}</tbody>
              </table>
            </details>
          </section>
          <section className="card" style={{ marginTop: '1rem' }}>
            <div className="row">
              <h2>Validation</h2>
              <button onClick={runValidation}>Run validation</button>
            </div>
            {latestReport ? (
              <>
                <p><span className={`status ${latestReport.status}`}>{latestReport.status}</span> {latestReport.summary}</p>
                <ValidationSummary submission={selected} report={latestReport} />
                <ThermoPlots series={latestReport.thermo_series} />
                <InterpretationNotes notes={latestReport.interpretation_notes} />
                <details className="details-panel">
                  <summary>Detailed validation checks ({latestReport.checks.length})</summary>
                  <table>
                    <thead><tr><th>Check</th><th>Status</th><th>Message</th><th>Evidence</th></tr></thead>
                    <tbody>
                      {latestReport.checks.map((check) => (
                        <tr key={check.id}>
                          <td>{check.check_type}</td>
                          <td><span className={`status ${check.status}`}>{check.status}</span></td>
                          <td>{check.message}</td>
                          <td>{check.evidence}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              </>
            ) : <p className="muted">No validation report yet.</p>}
          </section>
          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Student Interpretation</h2>
            {selectedAssignment?.interpretation_prompts.length ? (
              <div className="prompt-cues">
                {selectedAssignment.interpretation_prompts.map((prompt) => <p key={prompt}>{prompt}</p>)}
              </div>
            ) : null}
            <textarea value={interpretation} onChange={(e) => setInterpretation(e.target.value)} />
            {interpretationMessage ? <div className="inline-success" role="status">{interpretationMessage}</div> : null}
            {selected.status === 'submitted' ? <div className="inline-success" role="status">This assignment is submitted.</div> : null}
            <div className="row" style={{ marginTop: '0.75rem' }}>
              <button onClick={saveInterpretation}>Save interpretation</button>
              <button className="secondary" onClick={() => download(`/submissions/${selected.id}/package`, `submission_${selected.id}_package.zip`)}>Download ZIP</button>
              <button onClick={submitAssignment} disabled={selected.status === 'submitted'}>{selected.status === 'submitted' ? 'Submitted' : 'Submit assignment'}</button>
            </div>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
