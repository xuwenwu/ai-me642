'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { api, download } from '@/lib/api';
import type { InstructorAnalytics, RosterStudent } from '@/lib/types';

export default function InstructorOverviewPage() {
  const [analytics, setAnalytics] = useState<InstructorAnalytics | null>(null);
  const [roster, setRoster] = useState<RosterStudent[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api<InstructorAnalytics>('/instructor/analytics'), api<RosterStudent[]>('/instructor/roster')])
      .then(([a, r]) => {
        setAnalytics(a);
        setRoster(r);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load instructor overview'));
  }, []);

  const rosterTotals = useMemo(() => ({
    missing: roster.reduce((total, student) => total + student.missing_count, 0),
    warnings: roster.reduce((total, student) => total + student.warning_count, 0),
    graded: roster.reduce((total, student) => total + student.graded_count, 0),
  }), [roster]);

  return (
    <AppShell>
      <div className="section-header">
        <h1>Instructor Overview</h1>
        <div className="row">
          <button className="secondary" onClick={() => download('/instructor/gradebook.csv', 'gradebook.csv')}>Download gradebook</button>
          <Link href="/instructor/setup">Course setup</Link>
          <Link href="/instructor/submissions">Open review queue</Link>
        </div>
      </div>
      {error ? <div className="error">{error}</div> : null}
      {analytics ? (
        <>
          <section className="card">
            <div className="summary-strip">
              <div className="summary-item"><span>Students</span><strong>{analytics.total_students}</strong></div>
              <div className="summary-item"><span>Assignments</span><strong>{analytics.total_assignments}</strong></div>
              <div className="summary-item"><span>Submissions</span><strong>{analytics.total_submissions}</strong></div>
              <div className="summary-item"><span>Submitted</span><strong>{analytics.submitted_count}</strong></div>
              <div className="summary-item"><span>Graded</span><strong>{analytics.graded_count}</strong></div>
              <div className="summary-item"><span>Attention</span><strong>{analytics.needs_attention_count}</strong></div>
            </div>
          </section>

          <section className="card" style={{ marginTop: '1rem' }}>
            <h2>Assignment Analytics</h2>
            <table>
              <thead>
                <tr>
                  <th>Assignment</th>
                  <th>Submitted</th>
                  <th>Missing</th>
                  <th>Validation</th>
                  <th>Grading</th>
                  <th>Attention</th>
                </tr>
              </thead>
              <tbody>
                {analytics.assignments.map((assignment) => (
                  <tr key={assignment.assignment_id}>
                    <td>
                      <strong>{assignment.title}</strong>
                      <div className="muted">Due {assignment.due_date || 'not set'}</div>
                    </td>
                    <td>{assignment.submitted_count}/{assignment.total_students}</td>
                    <td>{assignment.missing_count}</td>
                    <td>
                      {assignment.validation_warning_count} warning, {assignment.validation_failed_count} failed, {assignment.validation_not_run_count} not run
                    </td>
                    <td>{assignment.graded_count} graded, {assignment.ungraded_submitted_count} submitted ungraded</td>
                    <td><span className={assignment.needs_attention_count ? 'status warning' : 'status passed'}>{assignment.needs_attention_count}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card" style={{ marginTop: '1rem' }}>
            <div className="section-header">
              <h2>Needs Attention</h2>
              <Link href="/instructor/submissions">Review submissions</Link>
            </div>
            {analytics.needs_attention.length ? (
              <table>
                <thead><tr><th>Student</th><th>Assignment</th><th>Status</th><th>Reasons</th></tr></thead>
                <tbody>
                  {analytics.needs_attention.map((item) => (
                    <tr key={item.submission_id}>
                      <td>{item.student_name}<div className="muted">{item.student_email}</div></td>
                      <td>{item.assignment_title}</td>
                      <td>{item.status} / {item.validation_status} / {item.grade_state}</td>
                      <td>{item.reasons.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="muted">No submitted packages need instructor attention right now.</p>}
          </section>
        </>
      ) : <p className="muted">Loading instructor overview...</p>}

      <section className="card" style={{ marginTop: '1rem' }}>
        <div className="section-header">
          <h2>Roster Readiness</h2>
          <span className="muted">{rosterTotals.missing} missing assignments, {rosterTotals.warnings} warnings, {rosterTotals.graded} graded</span>
        </div>
        {roster.length ? (
          <table>
            <thead><tr><th>Student</th><th>Section</th><th>Submissions</th><th>Submitted</th><th>Warnings</th><th>Graded</th><th>Missing</th></tr></thead>
            <tbody>
              {roster.map((student) => (
                <tr key={student.student_id}>
                  <td>{student.full_name}<div className="muted">{student.email}</div></td>
                  <td>{student.section || 'Unassigned'}</td>
                  <td>{student.submissions_count}/{student.total_assignments}</td>
                  <td>{student.submitted_count}</td>
                  <td>{student.warning_count}</td>
                  <td>{student.graded_count}</td>
                  <td>{student.missing_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="muted">No active student enrollments found.</p>}
      </section>
    </AppShell>
  );
}
