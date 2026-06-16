'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { api } from '@/lib/api';
import type { PilotFeedback, PilotFeedbackInput } from '@/lib/types';

const categories = [
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
  ['question', 'Question'],
  ['minor_confusion', 'Minor confusion'],
  ['blocks_progress', 'Blocks progress'],
];

const emptyFeedback: PilotFeedbackInput = {
  category: 'confusing_ui',
  severity: 'minor_confusion',
  page_url: '',
  message: '',
  contact_allowed: true,
};

function labelFor(options: string[][], value: string) {
  return options.find(([key]) => key === value)?.[1] || value;
}

export default function FeedbackPage() {
  const [form, setForm] = useState<PilotFeedbackInput>(emptyFeedback);
  const [items, setItems] = useState<PilotFeedback[]>([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function load() {
    setItems(await api<PilotFeedback[]>('/feedback'));
  }

  useEffect(() => {
    setForm((current) => ({ ...current, page_url: window.location.pathname }));
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load feedback'));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage('');
    setError('');
    try {
      await api<PilotFeedback>('/feedback', { method: 'POST', body: JSON.stringify(form) });
      setForm({ ...emptyFeedback, page_url: window.location.pathname });
      await load();
      setMessage('Feedback submitted. Thank you for helping improve the pilot.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    }
  }

  return (
    <AppShell>
      <div className="section-header">
        <h1>Pilot Feedback</h1>
      </div>
      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}

      <form className="form card" onSubmit={submit}>
        <div className="filter-grid">
          <label>Category<select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
          <label>Severity<select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
            {severities.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></label>
        </div>
        <label>Page or context<input value={form.page_url} onChange={(e) => setForm({ ...form, page_url: e.target.value })} /></label>
        <label>Description<textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} required /></label>
        <fieldset className="check-panel">
          <legend>Follow-up</legend>
          <label><input type="checkbox" checked={form.contact_allowed} onChange={(e) => setForm({ ...form, contact_allowed: e.target.checked })} /> Instructor may contact me about this</label>
        </fieldset>
        <button>Submit feedback</button>
      </form>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>My Feedback</h2>
        {items.length ? (
          <div className="grid">
            {items.map((item) => (
              <div className="assignment-row" key={item.id}>
                <div className="section-header">
                  <strong>{labelFor(categories, item.category)}</strong>
                  <span className={`status ${item.status === 'resolved' ? 'passed' : item.severity === 'blocks_progress' ? 'failed' : 'warning'}`}>{item.status}</span>
                </div>
                <p>{item.message}</p>
                <p className="muted">{labelFor(severities, item.severity)} - {item.page_url || 'No page context'} - {new Date(item.created_at).toLocaleString()}</p>
                {item.instructor_notes ? <div className="assignment-context"><strong>Instructor notes</strong><p>{item.instructor_notes}</p></div> : null}
              </div>
            ))}
          </div>
        ) : <p className="muted">No feedback submitted yet.</p>}
      </section>
    </AppShell>
  );
}
