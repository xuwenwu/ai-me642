'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { api, download } from '@/lib/api';
import type { PilotFeedback, PilotFeedbackUpdate } from '@/lib/types';

const categories = [
  ['all', 'All categories'],
  ['login_account', 'Login/account'],
  ['upload', 'Upload'],
  ['validation', 'Validation'],
  ['ai_guidance', 'AI guidance'],
  ['submission', 'Submission'],
  ['grading_feedback', 'Grading/feedback'],
  ['confusing_ui', 'Confusing UI'],
  ['other', 'Other'],
];

const severities = [
  ['all', 'All severities'],
  ['question', 'Question'],
  ['minor_confusion', 'Minor confusion'],
  ['blocks_progress', 'Blocks progress'],
];

const statuses = [
  ['all', 'All statuses'],
  ['new', 'New'],
  ['reviewing', 'Reviewing'],
  ['resolved', 'Resolved'],
  ['dismissed', 'Dismissed'],
];

const roleFilters = [
  ['all', 'All roles'],
  ['student', 'Student'],
  ['ta', 'TA'],
  ['instructor', 'Instructor'],
];

function statusClass(item: PilotFeedback) {
  if (item.status === 'resolved' || item.status === 'dismissed') return 'passed';
  if (item.severity === 'blocks_progress') return 'failed';
  return 'warning';
}

export default function InstructorFeedbackPage() {
  const [items, setItems] = useState<PilotFeedback[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');
  const [notes, setNotes] = useState('');
  const [nextStatus, setNextStatus] = useState('reviewing');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const selected = useMemo(() => items.find((item) => item.id === selectedId) || items[0], [items, selectedId]);
  const openCount = items.filter((item) => item.status === 'new' || item.status === 'reviewing').length;
  const blockingCount = items.filter((item) => item.severity === 'blocks_progress' && item.status !== 'resolved' && item.status !== 'dismissed').length;

  async function load() {
    const params = new URLSearchParams({ status: statusFilter, category: categoryFilter, severity: severityFilter, role: roleFilter });
    const data = await api<PilotFeedback[]>(`/instructor/feedback?${params.toString()}`);
    setItems(data);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load pilot feedback'));
  }, [statusFilter, categoryFilter, severityFilter, roleFilter]);

  useEffect(() => {
    if (!selected) return;
    setNotes(selected.instructor_notes || '');
    setNextStatus(selected.status);
  }, [selected]);

  async function saveTriage() {
    if (!selected) return;
    setMessage('');
    setError('');
    try {
      const payload: PilotFeedbackUpdate = { status: nextStatus, instructor_notes: notes };
      const saved = await api<PilotFeedback>(`/instructor/feedback/${selected.id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      await load();
      setSelectedId(saved.id);
      setMessage(`Updated feedback #${saved.id}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update feedback');
    }
  }

  const csvPath = `/instructor/feedback.csv?${new URLSearchParams({ status: statusFilter, category: categoryFilter, severity: severityFilter, role: roleFilter }).toString()}`;

  return (
    <AppShell>
      <div className="section-header">
        <h1>Pilot Feedback</h1>
        <div className="row">
          <button className="secondary" onClick={() => download(csvPath, 'pilot_feedback.csv')}>Download CSV</button>
          <Link href="/instructor">Instructor overview</Link>
        </div>
      </div>
      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}

      <section className="card">
        <div className="summary-strip">
          <div className="summary-item"><span>Total shown</span><strong>{items.length}</strong></div>
          <div className="summary-item"><span>Open</span><strong>{openCount}</strong></div>
          <div className="summary-item"><span>Blocking</span><strong>{blockingCount}</strong></div>
        </div>
        <div className="filter-grid">
          <label>Status<select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            {statuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
          <label>Category<select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            {categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
          <label>Severity<select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            {severities.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
          <label>Role<select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            {roleFilters.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
        </div>
      </section>

      <div className="grid two" style={{ marginTop: '1rem' }}>
        <section className="card">
          <h2>Feedback Queue</h2>
          {items.length ? (
            items.map((item) => (
              <button className="feedback-list-item" key={item.id} type="button" onClick={() => setSelectedId(item.id)}>
                <span><strong>#{item.id}</strong> {item.category}</span>
                <span className={`status ${statusClass(item)}`}>{item.status}</span>
                <span className="muted">{item.user_full_name} - {item.severity}</span>
              </button>
            ))
          ) : <p className="muted">No feedback matches the current filters.</p>}
        </section>

        <section className="card">
          <h2>Feedback Detail</h2>
          {selected ? (
            <div className="form">
              <div className="assignment-context">
                <strong>#{selected.id} {selected.category} - {selected.severity}</strong>
                <p>{selected.message}</p>
                <p className="muted">{selected.user_full_name} ({selected.user_email}) - {selected.role}</p>
                <p className="muted">{selected.page_url || 'No page context'} - {new Date(selected.created_at).toLocaleString()}</p>
                <p className="muted">Contact allowed: {selected.contact_allowed ? 'yes' : 'no'}</p>
              </div>
              <label>Status<select value={nextStatus} onChange={(e) => setNextStatus(e.target.value)}>
                {statuses.filter(([value]) => value !== 'all').map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select></label>
              <label>Instructor notes<textarea value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
              <button onClick={saveTriage}>Save triage</button>
            </div>
          ) : <p className="muted">Select a feedback item to review.</p>}
        </section>
      </div>
    </AppShell>
  );
}
