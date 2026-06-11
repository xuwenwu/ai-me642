'use client';

import { useEffect, useMemo, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { InterpretationNotes } from '@/components/InterpretationNotes';
import { ThermoPlots } from '@/components/ThermoPlots';
import { EvidenceChecklist, ValidationSummary } from '@/components/ValidationSummary';
import { api, download } from '@/lib/api';
import type { Assignment, Submission } from '@/lib/types';

export default function InstructorSubmissionsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [assignmentFilter, setAssignmentFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [validationFilter, setValidationFilter] = useState('all');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [scores, setScores] = useState<Record<number, number>>({});
  const [comments, setComments] = useState<Record<number, string>>({});
  const [feedback, setFeedback] = useState('');
  const [latePenalty, setLatePenalty] = useState(0);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [gradeMessage, setGradeMessage] = useState('');

  const assignmentById = useMemo(() => new Map(assignments.map((assignment) => [assignment.id, assignment])), [assignments]);
  const filteredSubmissions = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return submissions.filter((submission) => {
      const assignment = assignmentById.get(submission.assignment_id);
      const latestStatus = submission.validation_reports[0]?.status || 'not_run';
      const graded = Boolean(submission.grade);
      const text = `${submission.id} ${submission.user_id} ${submission.title} ${assignment?.title || ''}`.toLowerCase();
      return (
        (assignmentFilter === 'all' || submission.assignment_id === Number(assignmentFilter)) &&
        (statusFilter === 'all' || submission.status === statusFilter) &&
        (validationFilter === 'all' || latestStatus === validationFilter) &&
        (gradeFilter === 'all' || (gradeFilter === 'graded' ? graded : !graded)) &&
        (!needle || text.includes(needle))
      );
    });
  }, [assignmentById, assignmentFilter, gradeFilter, search, statusFilter, submissions, validationFilter]);
  const selected = useMemo(
    () => submissions.find((submission) => submission.id === selectedId) || filteredSubmissions[0] || submissions[0],
    [filteredSubmissions, selectedId, submissions],
  );
  const assignment = useMemo(() => assignments.find((item) => item.id === selected?.assignment_id), [assignments, selected]);
  const latestReport = selected?.validation_reports[0];
  const submittedCount = submissions.filter((submission) => submission.status === 'submitted').length;
  const needsGradingCount = submissions.filter((submission) => submission.status === 'submitted' && !submission.grade).length;
  const warningCount = submissions.filter((submission) => submission.validation_reports[0]?.status === 'warning').length;

  const gradebookPath = useMemo(() => {
    const params = new URLSearchParams();
    if (assignmentFilter !== 'all') params.set('assignment_id', assignmentFilter);
    if (statusFilter !== 'all') params.set('status', statusFilter);
    if (validationFilter !== 'all') params.set('validation_status', validationFilter);
    if (gradeFilter !== 'all') params.set('grade_state', gradeFilter);
    const query = params.toString();
    return `/instructor/gradebook.csv${query ? `?${query}` : ''}`;
  }, [assignmentFilter, gradeFilter, statusFilter, validationFilter]);

  async function load() {
    const [a, s] = await Promise.all([api<Assignment[]>('/assignments'), api<Submission[]>('/instructor/submissions')]);
    setAssignments(a);
    setSubmissions(s);
    if (!selectedId && s[0]) setSelectedId(s[0].id);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load instructor page'));
  }, []);

  useEffect(() => {
    setGradeMessage('');
    setFeedback(selected?.grade?.feedback || '');
    setLatePenalty(selected?.grade?.late_penalty || 0);
  }, [selected?.id]);

  async function saveGrade(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || !assignment) return;
    setError('');
    setMessage('');
    setGradeMessage('');
    try {
      const grade = await api<{ final_score: number }>('/instructor/grades', {
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
      setGradeMessage(`Grade saved. Final score: ${grade.final_score}`);
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
        <div className="summary-strip">
          <div className="summary-item"><span>Total</span><strong>{submissions.length}</strong></div>
          <div className="summary-item"><span>Submitted</span><strong>{submittedCount}</strong></div>
          <div className="summary-item"><span>Needs grading</span><strong>{needsGradingCount}</strong></div>
          <div className="summary-item"><span>Warnings</span><strong>{warningCount}</strong></div>
        </div>
        <div className="filter-grid">
          <label>Assignment<select value={assignmentFilter} onChange={(e) => setAssignmentFilter(e.target.value)}>
            <option value="all">All assignments</option>
            {assignments.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select></label>
          <label>Status<select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
          </select></label>
          <label>Validation<select value={validationFilter} onChange={(e) => setValidationFilter(e.target.value)}>
            <option value="all">All validation</option>
            <option value="not_run">Not run</option>
            <option value="passed">Passed</option>
            <option value="warning">Warning</option>
            <option value="failed">Failed</option>
          </select></label>
          <label>Grade<select value={gradeFilter} onChange={(e) => setGradeFilter(e.target.value)}>
            <option value="all">All grades</option>
            <option value="ungraded">Ungraded</option>
            <option value="graded">Graded</option>
          </select></label>
          <label>Search<input value={search} onChange={(e) => setSearch(e.target.value)} /></label>
        </div>
        <div className="row" style={{ marginTop: '0.85rem' }}>
          <select value={selected?.id || ''} onChange={(e) => setSelectedId(Number(e.target.value))}>
            {filteredSubmissions.map((submission) => (
              <option key={submission.id} value={submission.id}>
                #{submission.id} {assignmentById.get(submission.assignment_id)?.title || 'Assignment'} - {submission.title}
              </option>
            ))}
          </select>
          <button className="secondary" onClick={() => download(gradebookPath, 'gradebook.csv')}>Download filtered gradebook</button>
        </div>
      </section>
      {selected ? (
        <div className="grid two" style={{ marginTop: '1rem' }}>
          <section className="card">
            <div className="section-header">
              <h2>Submission Evidence</h2>
              <span className={`status ${latestReport?.status ?? ''}`}>{latestReport?.status ?? 'not run'}</span>
            </div>
            <p><strong>{selected.title}</strong></p>
            <p>Status: {selected.status} - Grade: {selected.grade ? selected.grade.final_score : 'not graded'}</p>
            <p className="muted">{assignment?.title || `Assignment ${selected.assignment_id}`} - {latestReport?.validation_profile || assignment?.validation_profile || 'profile not set'}</p>
            <ValidationSummary submission={selected} report={latestReport} />
            <EvidenceChecklist submission={selected} assignment={assignment} />
            {latestReport ? <ThermoPlots series={latestReport.thermo_series} /> : null}
            {latestReport ? <InterpretationNotes notes={latestReport.interpretation_notes} /> : null}
            <h3>Files</h3>
            {selected.files.map((file) => <p key={file.id}>{file.file_type}: {file.original_filename}</p>)}
            <h3>Student Interpretation</h3>
            <p>{selected.student_interpretation || 'No interpretation recorded.'}</p>
          </section>
          <section className="card">
            <h2>Rubric Grade</h2>
            {selected.grade ? <p className="muted">Current final score: {selected.grade.final_score}</p> : null}
            {gradeMessage ? <div className="inline-success" role="status">{gradeMessage}</div> : null}
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
