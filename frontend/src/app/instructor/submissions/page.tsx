'use client';

import { useEffect, useMemo, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { ThermoPlots } from '@/components/ThermoPlots';
import { api, download } from '@/lib/api';
import type { Assignment, Submission } from '@/lib/types';

export default function InstructorSubmissionsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [scores, setScores] = useState<Record<number, number>>({});
  const [comments, setComments] = useState<Record<number, string>>({});
  const [feedback, setFeedback] = useState('');
  const [latePenalty, setLatePenalty] = useState(0);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const selected = useMemo(() => submissions.find((submission) => submission.id === selectedId) || submissions[0], [submissions, selectedId]);
  const assignment = useMemo(() => assignments.find((item) => item.id === selected?.assignment_id), [assignments, selected]);

  async function load() {
    const [a, s] = await Promise.all([api<Assignment[]>('/assignments'), api<Submission[]>('/instructor/submissions')]);
    setAssignments(a);
    setSubmissions(s);
    if (!selectedId && s[0]) setSelectedId(s[0].id);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load instructor page'));
  }, []);

  async function saveGrade(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || !assignment) return;
    setError('');
    setMessage('');
    try {
      await api('/instructor/grades', {
        method: 'POST',
        body: JSON.stringify({
          submission_id: selected.id,
          late_penalty: latePenalty,
          feedback,
          criterion_scores: assignment.criteria.map((criterion) => ({
            criterion_id: criterion.id,
            score: scores[criterion.id] ?? 0,
            comment: comments[criterion.id] || '',
          })),
        }),
      });
      await load();
      setMessage('Grade saved');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save grade');
    }
  }

  return (
    <AppShell>
      <h1>Instructor Review</h1>
      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}
      <section className="card">
        <div className="row">
          <select value={selected?.id || ''} onChange={(e) => setSelectedId(Number(e.target.value))}>
            {submissions.map((submission) => <option key={submission.id} value={submission.id}>#{submission.id} {submission.title}</option>)}
          </select>
          <button className="secondary" onClick={() => download('/instructor/gradebook.csv', 'gradebook.csv')}>Download gradebook</button>
        </div>
      </section>
      {selected ? (
        <div className="grid two" style={{ marginTop: '1rem' }}>
          <section className="card">
            <h2>Submission Evidence</h2>
            <p><strong>{selected.title}</strong></p>
            <p>Status: {selected.status}</p>
            <p>Validation: {selected.validation_reports[0]?.status || 'not run'}</p>
            {selected.validation_reports[0] ? <ThermoPlots series={selected.validation_reports[0].thermo_series} /> : null}
            <h3>Files</h3>
            {selected.files.map((file) => <p key={file.id}>{file.file_type}: {file.original_filename}</p>)}
            <h3>Student Interpretation</h3>
            <p>{selected.student_interpretation || 'No interpretation recorded.'}</p>
          </section>
          <section className="card">
            <h2>Rubric Grade</h2>
            <form className="form" onSubmit={saveGrade}>
              {assignment?.criteria.map((criterion) => (
                <div key={criterion.id}>
                  <label>{criterion.name} ({criterion.max_points} pts)<input type="number" min="0" max={criterion.max_points} step="0.5" value={scores[criterion.id] ?? 0} onChange={(e) => setScores({ ...scores, [criterion.id]: Number(e.target.value) })} /></label>
                  <textarea placeholder="Criterion comment" value={comments[criterion.id] || ''} onChange={(e) => setComments({ ...comments, [criterion.id]: e.target.value })} />
                </div>
              ))}
              <label>Late penalty<input type="number" min="0" step="0.5" value={latePenalty} onChange={(e) => setLatePenalty(Number(e.target.value))} /></label>
              <label>Overall feedback<textarea value={feedback} onChange={(e) => setFeedback(e.target.value)} /></label>
              <button>Save grade</button>
            </form>
          </section>
        </div>
      ) : <p className="muted">No submissions to review yet.</p>}
    </AppShell>
  );
}
