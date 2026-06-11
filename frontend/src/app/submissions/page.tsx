'use client';

import { useEffect, useMemo, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { ApiError, api, download } from '@/lib/api';
import type { Assignment, FileArtifact, ProjectSpec, Submission, ValidationReport } from '@/lib/types';

const fileTypes = [
  'lammps_input',
  'lammps_log',
  'readme',
  'prompt_log',
  'python_analysis',
  'ovito_script',
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
  const [createForm, setCreateForm] = useState({ assignment_id: '', project_id: '', title: 'Lab 3 NVE validation package' });
  const [fileType, setFileType] = useState('lammps_log');
  const [file, setFile] = useState<File | null>(null);
  const [interpretation, setInterpretation] = useState('');

  const selected = useMemo(() => submissions.find((submission) => submission.id === selectedId) || submissions[0], [submissions, selectedId]);

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
  }, [selected?.id]);

  async function createSubmission(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');
    const assignmentId = Number(createForm.assignment_id);
    const existing = submissions.find((submission) => submission.assignment_id === assignmentId);
    if (existing) {
      setSelectedId(existing.id);
      setMessage(`Submission #${existing.id} already exists for this assignment. Continue with the selected submission below.`);
      return;
    }
    try {
      const created = await api<Submission>('/submissions', {
        method: 'POST',
        body: JSON.stringify({
          assignment_id: assignmentId,
          project_id: createForm.project_id ? Number(createForm.project_id) : null,
          title: createForm.title,
        }),
      });
      await load();
      setSelectedId(created.id);
      setMessage(`Created submission #${created.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const latest = await load();
        const match = latest.find((submission) => submission.assignment_id === assignmentId);
        if (match) {
          setSelectedId(match.id);
          setMessage(`Submission #${match.id} already exists for this assignment. Continue with the selected submission below.`);
          return;
        }
      }
      setError(err instanceof Error ? err.message : 'Failed to create submission');
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
    try {
      await api<Submission>(`/submissions/${selected.id}/interpretation`, {
        method: 'PATCH',
        body: JSON.stringify({ student_interpretation: interpretation }),
      });
      await load();
      setMessage('Saved interpretation');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save interpretation');
    }
  }

  async function submitAssignment() {
    if (!selected) return;
    setError('');
    setMessage('');
    try {
      await api<Submission>(`/submissions/${selected.id}/submit`, { method: 'POST' });
      await load();
      setMessage('Submission marked as submitted');
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
            <label>Assignment<select value={createForm.assignment_id} onChange={(e) => setCreateForm({ ...createForm, assignment_id: e.target.value })} required>
              <option value="">Select assignment</option>
              {assignments.map((assignment) => <option key={assignment.id} value={assignment.id}>{assignment.title}</option>)}
            </select></label>
            <label>Project<select value={createForm.project_id} onChange={(e) => setCreateForm({ ...createForm, project_id: e.target.value })}>
              <option value="">Optional project</option>
              {projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
            </select></label>
            <label>Title<input value={createForm.title} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} /></label>
            <button>Create submission</button>
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
              <p>Files: {selected.files.length}</p>
              <p>Latest validation: {selected.validation_reports[0]?.status || 'not run'}</p>
            </div>
          ) : <p className="muted">Create a submission to begin.</p>}
        </section>
      </div>
      {selected ? (
        <>
          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Upload Artifacts</h2>
            <form className="form" onSubmit={uploadArtifact}>
              <label>File type<select value={fileType} onChange={(e) => setFileType(e.target.value)}>
                {fileTypes.map((type) => <option key={type} value={type}>{type}</option>)}
              </select></label>
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <button disabled={!file}>Upload</button>
            </form>
            <table>
              <thead><tr><th>Type</th><th>Name</th><th>Size</th></tr></thead>
              <tbody>{selected.files.map((artifact) => <tr key={artifact.id}><td>{artifact.file_type}</td><td>{artifact.original_filename}</td><td>{artifact.size_bytes}</td></tr>)}</tbody>
            </table>
          </section>
          <section className="card" style={{ marginTop: '1rem' }}>
            <div className="row">
              <h2>Validation</h2>
              <button onClick={runValidation}>Run validation</button>
            </div>
            {selected.validation_reports[0] ? (
              <>
                <p><span className={`status ${selected.validation_reports[0].status}`}>{selected.validation_reports[0].status}</span> {selected.validation_reports[0].summary}</p>
                <table>
                  <thead><tr><th>Check</th><th>Status</th><th>Message</th><th>Evidence</th></tr></thead>
                  <tbody>
                    {selected.validation_reports[0].checks.map((check) => (
                      <tr key={check.id}>
                        <td>{check.check_type}</td>
                        <td><span className={`status ${check.status}`}>{check.status}</span></td>
                        <td>{check.message}</td>
                        <td>{check.evidence}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            ) : <p className="muted">No validation report yet.</p>}
          </section>
          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Student Interpretation</h2>
            <textarea value={interpretation} onChange={(e) => setInterpretation(e.target.value)} />
            <div className="row" style={{ marginTop: '0.75rem' }}>
              <button onClick={saveInterpretation}>Save interpretation</button>
              <button className="secondary" onClick={() => download(`/submissions/${selected.id}/package`, `submission_${selected.id}_package.zip`)}>Download ZIP</button>
              <button onClick={submitAssignment}>Submit assignment</button>
            </div>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
