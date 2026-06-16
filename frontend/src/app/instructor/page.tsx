'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { api, download } from '@/lib/api';
import type { AIPolicy, AIProviderReadiness, Assignment, InstructorAnalytics, PromptTemplate, RosterStudent } from '@/lib/types';

type LaunchCheck = {
  title: string;
  status: 'ready' | 'review' | 'blocked';
  detail: string;
  href?: string;
};

function launchStatusClass(status: LaunchCheck['status']) {
  if (status === 'ready') return 'passed';
  if (status === 'review') return 'warning';
  return 'failed';
}

function launchStatusLabel(status: LaunchCheck['status']) {
  if (status === 'ready') return 'Ready';
  if (status === 'review') return 'Review';
  return 'Blocked';
}

export default function InstructorOverviewPage() {
  const [analytics, setAnalytics] = useState<InstructorAnalytics | null>(null);
  const [roster, setRoster] = useState<RosterStudent[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [policy, setPolicy] = useState<AIPolicy | null>(null);
  const [aiReadiness, setAiReadiness] = useState<AIProviderReadiness | null>(null);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      api<InstructorAnalytics>('/instructor/analytics'),
      api<RosterStudent[]>('/instructor/roster'),
      api<Assignment[]>('/instructor/assignments'),
      api<AIPolicy>('/instructor/ai-policy'),
      api<AIProviderReadiness>('/instructor/ai-policy/readiness'),
      api<PromptTemplate[]>('/instructor/prompt-templates'),
    ])
      .then(([a, r, assignmentList, aiPolicy, readiness, promptTemplates]) => {
        setAnalytics(a);
        setRoster(r);
        setAssignments(assignmentList);
        setPolicy(aiPolicy);
        setAiReadiness(readiness);
        setTemplates(promptTemplates);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load instructor overview'));
  }, []);

  const rosterTotals = useMemo(() => ({
    missing: roster.reduce((total, student) => total + student.missing_count, 0),
    warnings: roster.reduce((total, student) => total + student.warning_count, 0),
    graded: roster.reduce((total, student) => total + student.graded_count, 0),
  }), [roster]);

  const launchChecks = useMemo(() => {
    const publishedAssignments = assignments.filter((assignment) => assignment.status === 'published');
    const activeStudents = roster.filter((student) => student.account_status !== 'inactive');
    const passwordResetCount = activeStudents.filter((student) => student.must_change_password).length;
    const configuredAssignments = publishedAssignments.filter((assignment) => assignment.validation_profile && assignment.required_file_types.length);
    const aiPolicyReady = Boolean(policy?.body.trim() && policy.disclosure_requirements.length);
    const assistantReady = Boolean(policy?.assistant_enabled && aiReadiness?.configured);

    const required: LaunchCheck[] = [
      {
        title: 'Roster loaded',
        status: activeStudents.length ? 'ready' : 'blocked',
        detail: activeStudents.length ? `${activeStudents.length} active student account${activeStudents.length === 1 ? '' : 's'} available.` : 'Add or import students before launch.',
        href: '/instructor/setup',
      },
      {
        title: 'Assignments published',
        status: publishedAssignments.length ? 'ready' : 'blocked',
        detail: publishedAssignments.length ? `${publishedAssignments.length} published assignment${publishedAssignments.length === 1 ? '' : 's'} visible to students.` : 'Publish at least one assignment for the pilot.',
        href: '/instructor/setup',
      },
      {
        title: 'Validation configured',
        status: publishedAssignments.length && configuredAssignments.length === publishedAssignments.length ? 'ready' : publishedAssignments.length ? 'review' : 'blocked',
        detail: publishedAssignments.length ? `${configuredAssignments.length}/${publishedAssignments.length} published assignments have required files and a validation profile.` : 'Validation readiness depends on published assignments.',
        href: '/instructor/setup',
      },
      {
        title: 'AI policy and disclosure',
        status: aiPolicyReady ? 'ready' : 'review',
        detail: aiPolicyReady ? 'Responsible AI policy text and disclosure requirements are present.' : 'Review the AI policy body and disclosure requirements.',
        href: '/instructor/setup',
      },
      {
        title: 'Live assistant readiness',
        status: assistantReady ? 'ready' : 'review',
        detail: assistantReady ? `${aiReadiness?.provider_mode} is configured with ${aiReadiness?.remaining_requests ?? 0} requests remaining.` : 'Enable and test the course assistant if the pilot will use live AI guidance.',
        href: '/instructor/setup',
      },
      {
        title: 'Prompt templates',
        status: templates.length ? 'ready' : 'review',
        detail: templates.length ? `${templates.length} reusable prompt template${templates.length === 1 ? '' : 's'} available.` : 'Add prompt templates for common student AI-assistance tasks.',
        href: '/instructor/setup',
      },
    ];

    const optional: LaunchCheck[] = [
      {
        title: 'Student password reset flow',
        status: activeStudents.length && passwordResetCount === activeStudents.length ? 'ready' : activeStudents.length ? 'review' : 'blocked',
        detail: activeStudents.length ? `${passwordResetCount}/${activeStudents.length} active accounts require a password change.` : 'No active accounts to check yet.',
        href: '/instructor/setup',
      },
      {
        title: 'Pilot smoke submission',
        status: analytics?.total_submissions ? 'ready' : 'review',
        detail: analytics?.total_submissions ? `${analytics.total_submissions} submission package${analytics.total_submissions === 1 ? '' : 's'} exist for workflow review.` : 'Create one student smoke submission before class if you want a final rehearsal.',
        href: '/instructor/submissions',
      },
      {
        title: 'Review queue',
        status: analytics && analytics.needs_attention_count === 0 ? 'ready' : analytics ? 'review' : 'blocked',
        detail: analytics ? `${analytics.needs_attention_count} package${analytics.needs_attention_count === 1 ? '' : 's'} currently need attention.` : 'Review queue status is still loading.',
        href: '/instructor/submissions',
      },
      {
        title: 'Gradebook exports',
        status: 'ready',
        detail: 'Course, Canvas, LMS detail, and roster CSV exports are available from instructor pages.',
        href: '/instructor/gradebook',
      },
    ];

    return { required, optional };
  }, [aiReadiness, analytics, assignments, policy, roster, templates]);

  const requiredReady = launchChecks.required.filter((item) => item.status === 'ready').length;
  const requiredBlocked = launchChecks.required.filter((item) => item.status === 'blocked').length;
  const launchStatus = requiredBlocked ? 'Blocked' : requiredReady === launchChecks.required.length ? 'Ready for pilot' : 'Needs review';

  return (
    <AppShell>
      <div className="section-header">
        <h1>Instructor Overview</h1>
        <div className="row">
          <button className="secondary" onClick={() => download('/instructor/gradebook.csv', 'gradebook.csv')}>Download gradebook</button>
          <Link href="/instructor/gradebook">Gradebook dashboard</Link>
          <Link href="/instructor/setup">Course setup</Link>
          <Link href="/instructor/submissions">Open review queue</Link>
        </div>
      </div>
      {error ? <div className="error">{error}</div> : null}
      {analytics ? (
        <>
          <section className="card">
            <div className="section-header">
              <div>
                <h2>Pilot Launch Checklist</h2>
                <p className="muted">{requiredReady}/{launchChecks.required.length} required checks ready.</p>
              </div>
              <span className={`status ${requiredBlocked ? 'failed' : requiredReady === launchChecks.required.length ? 'passed' : 'warning'}`}>{launchStatus}</span>
            </div>
            <div className="launch-check-grid">
              {launchChecks.required.map((item) => (
                <div className="launch-check-item" key={item.title}>
                  <div className="section-header">
                    <strong>{item.title}</strong>
                    <span className={`status ${launchStatusClass(item.status)}`}>{launchStatusLabel(item.status)}</span>
                  </div>
                  <p>{item.detail}</p>
                  {item.href ? <Link href={item.href}>Open</Link> : null}
                </div>
              ))}
            </div>
            <details className="details-panel">
              <summary>Optional rehearsal checks</summary>
              <div className="launch-check-grid">
                {launchChecks.optional.map((item) => (
                  <div className="launch-check-item" key={item.title}>
                    <div className="section-header">
                      <strong>{item.title}</strong>
                      <span className={`status ${launchStatusClass(item.status)}`}>{launchStatusLabel(item.status)}</span>
                    </div>
                    <p>{item.detail}</p>
                    {item.href ? <Link href={item.href}>Open</Link> : null}
                  </div>
                ))}
              </div>
            </details>
          </section>

          <section className="card" style={{ marginTop: '1rem' }}>
            <div className="summary-strip">
              <div className="summary-item"><span>Students</span><strong>{analytics.total_students}</strong></div>
              <div className="summary-item"><span>Assignments</span><strong>{analytics.total_assignments}</strong></div>
              <div className="summary-item"><span>Submissions</span><strong>{analytics.total_submissions}</strong></div>
              <div className="summary-item"><span>Submitted</span><strong>{analytics.submitted_count}</strong></div>
              <div className="summary-item"><span>Graded</span><strong>{analytics.graded_count}</strong></div>
              <div className="summary-item"><span>AI Disclosure</span><strong>{analytics.ai_disclosure_missing_count}</strong></div>
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
                  <th>AI Disclosure</th>
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
                    <td>{assignment.ai_disclosure_missing_count} missing/thin</td>
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
