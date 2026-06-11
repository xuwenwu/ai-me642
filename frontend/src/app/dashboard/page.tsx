'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { api } from '@/lib/api';
import { useCurrentUser } from '@/lib/auth';
import type { Assignment, Submission } from '@/lib/types';

export default function DashboardPage() {
  const { user, ready } = useCurrentUser();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ready || !user) return;
    Promise.all([api<Assignment[]>('/assignments'), api<Submission[]>('/submissions')])
      .then(([a, s]) => {
        setAssignments(a);
        setSubmissions(s);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load dashboard'));
  }, [ready, user]);

  const submissionByAssignment = new Map(submissions.map((submission) => [submission.assignment_id, submission]));

  return (
    <AppShell>
      <h1>Dashboard</h1>
      {!user && ready ? <div className="error">Please sign in to use the studio.</div> : null}
      {error ? <div className="error">{error}</div> : null}
      <div className="grid two">
        <section className="card">
          <h2>Phase II Pilot Labs</h2>
          {assignments.map((assignment) => {
            const submission = submissionByAssignment.get(assignment.id);
            return (
              <div key={assignment.id} className="assignment-row">
                <div className="section-header">
                  <h3>{assignment.title}</h3>
                  <span className="status">{submission?.status || 'not started'}</span>
                </div>
                <p>{assignment.description}</p>
                <p className="muted">Due: {assignment.due_date || 'not set'} - {assignment.total_points} pts - {assignment.validation_profile}</p>
                <p className="muted">Validation: {submission?.validation_reports[0]?.status || 'not run'}</p>
                <Link href="/submissions">Open submission workflow</Link>
              </div>
            );
          })}
        </section>
        <section className="card">
          <h2>Evidence Chain</h2>
          <ol>
            <li>Scientific specification</li>
            <li>AI prompt disclosure</li>
            <li>Artifacts and logs</li>
            <li>Validation report</li>
            <li>Student interpretation</li>
            <li>Instructor grading</li>
            <li>Reproducible ZIP</li>
          </ol>
        </section>
      </div>
      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>Your Submissions</h2>
        {submissions.length ? (
          <table>
            <thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Validation</th><th>Grade</th></tr></thead>
            <tbody>
              {submissions.map((submission) => (
                <tr key={submission.id}>
                  <td>{submission.id}</td>
                  <td>{submission.title}</td>
                  <td>{submission.status}</td>
                  <td>{submission.validation_reports[0]?.status || 'not run'}</td>
                  <td>{submission.grade ? `${submission.grade.final_score}` : 'not graded'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="muted">No submissions yet.</p>}
      </section>
    </AppShell>
  );
}
