'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { api, download } from '@/lib/api';
import type { Assignment, Gradebook } from '@/lib/types';

function percent(value: number | null | undefined) {
  return value === null || value === undefined ? '-' : `${value.toFixed(1)}%`;
}

export default function InstructorGradebookPage() {
  const [gradebook, setGradebook] = useState<Gradebook | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [assignmentFilter, setAssignmentFilter] = useState('all');
  const [error, setError] = useState('');

  const query = useMemo(() => (assignmentFilter === 'all' ? '' : `?assignment_id=${assignmentFilter}`), [assignmentFilter]);

  async function load() {
    const [g, a] = await Promise.all([
      api<Gradebook>(`/instructor/gradebook${query}`),
      api<Assignment[]>('/instructor/assignments'),
    ]);
    setGradebook(g);
    setAssignments(a);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load gradebook'));
  }, [query]);

  return (
    <AppShell>
      <div className="section-header">
        <h1>Gradebook</h1>
        <div className="row">
          <Link href="/instructor">Instructor overview</Link>
          <Link href="/instructor/submissions">Review queue</Link>
        </div>
      </div>
      {error ? <div className="error">{error}</div> : null}
      <section className="card">
        <div className="filter-grid">
          <label>Assignment<select value={assignmentFilter} onChange={(e) => setAssignmentFilter(e.target.value)}>
            <option value="all">All assignments</option>
            {assignments.map((assignment) => <option key={assignment.id} value={assignment.id}>{assignment.title}</option>)}
          </select></label>
        </div>
        <div className="row" style={{ marginTop: '0.85rem' }}>
          <button className="secondary" onClick={() => download(`/instructor/course-gradebook.csv${query}`, 'course_gradebook.csv')}>Download course CSV</button>
          <button className="secondary" onClick={() => download(`/instructor/canvas-gradebook.csv${query}`, 'canvas_gradebook_import.csv')}>Download Canvas import CSV</button>
          <button className="secondary" onClick={() => download(`/instructor/lms-submission-detail.csv${query}`, 'lms_submission_detail.csv')}>Download LMS detail CSV</button>
        </div>
      </section>

      {gradebook ? (
        <>
          <section className="card" style={{ marginTop: '1rem' }}>
            <div className="summary-strip">
              <div className="summary-item"><span>Students</span><strong>{gradebook.total_students}</strong></div>
              <div className="summary-item"><span>Assignments</span><strong>{gradebook.total_assignments}</strong></div>
              <div className="summary-item"><span>Submitted</span><strong>{gradebook.total_submitted}</strong></div>
              <div className="summary-item"><span>Graded</span><strong>{gradebook.total_graded}</strong></div>
              <div className="summary-item"><span>Missing</span><strong>{gradebook.total_missing}</strong></div>
              <div className="summary-item"><span>Current Avg</span><strong>{percent(gradebook.current_average_score)}</strong></div>
            </div>
          </section>

          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Assignment Operations</h2>
            <table>
              <thead><tr><th>Assignment</th><th>Submitted</th><th>Graded</th><th>Ungraded</th><th>Missing</th><th>Validation</th><th>Avg Score</th></tr></thead>
              <tbody>
                {gradebook.assignments.map((assignment) => (
                  <tr key={assignment.assignment_id}>
                    <td><strong>{assignment.title}</strong><div className="muted">Due {assignment.due_date || 'not set'} - {assignment.total_points} pts</div></td>
                    <td>{assignment.submitted_count}</td>
                    <td>{assignment.graded_count}</td>
                    <td>{assignment.ungraded_count}</td>
                    <td>{assignment.missing_count}</td>
                    <td>{assignment.warning_count} warning, {assignment.failed_count} failed</td>
                    <td>{assignment.average_score === null ? '-' : assignment.average_score.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Student Gradebook</h2>
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Progress</th>
                  <th>Current Score</th>
                  {gradebook.assignments.map((assignment) => <th key={assignment.assignment_id}>{assignment.title}</th>)}
                </tr>
              </thead>
              <tbody>
                {gradebook.students.map((student) => (
                  <tr key={student.student_id}>
                    <td>{student.full_name}<div className="muted">{student.email} - {student.section || 'Unassigned'}</div></td>
                    <td>{student.submitted_count} submitted, {student.graded_count} graded, {student.missing_count} missing</td>
                    <td>{student.current_score}/{student.possible_score || 0}</td>
                    {student.assignments.map((cell) => (
                      <td key={`${student.student_id}-${cell.assignment_id}`}>
                        <span className={`status ${cell.validation_status === 'passed' ? 'passed' : cell.validation_status === 'failed' ? 'failed' : cell.validation_status === 'missing' ? '' : 'warning'}`}>
                          {cell.grade_state}
                        </span>
                        <div>{cell.final_score === null ? '-' : `${cell.final_score}/${cell.total_points}`}</div>
                        <div className="muted">{cell.submission_status} / {cell.validation_status}</div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      ) : <p className="muted">Loading gradebook...</p>}
    </AppShell>
  );
}
