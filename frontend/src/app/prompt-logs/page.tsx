'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { api } from '@/lib/api';
import type { Assignment, ProjectSpec, PromptLog } from '@/lib/types';

export default function PromptLogsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [projects, setProjects] = useState<ProjectSpec[]>([]);
  const [logs, setLogs] = useState<PromptLog[]>([]);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    title: 'AI assistance for NVE energy drift check',
    assignment_id: '',
    project_id: '',
    ai_tool_name: 'ChatGPT',
    task_type: 'lammps_debugging',
    prompt_text: '',
    ai_output_summary: '',
    accepted_parts: '',
    rejected_parts: '',
    manual_edits: '',
    validation_performed: '',
    remaining_concerns: '',
  });

  async function load() {
    const [a, p, l] = await Promise.all([api<Assignment[]>('/assignments'), api<ProjectSpec[]>('/projects'), api<PromptLog[]>('/prompt-logs')]);
    setAssignments(a);
    setProjects(p);
    setLogs(l);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load prompt logs'));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    try {
      await api<PromptLog>('/prompt-logs', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          assignment_id: form.assignment_id ? Number(form.assignment_id) : null,
          project_id: form.project_id ? Number(form.project_id) : null,
        }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prompt log');
    }
  }

  return (
    <AppShell>
      <h1>AI Prompt Logs</h1>
      <form className="form card" onSubmit={submit}>
        <label>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
        <label>Assignment<select value={form.assignment_id} onChange={(e) => setForm({ ...form, assignment_id: e.target.value })}>
          <option value="">Select assignment</option>
          {assignments.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}
        </select></label>
        <label>Project<select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })}>
          <option value="">Optional project</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
        </select></label>
        <label>AI tool<input value={form.ai_tool_name} onChange={(e) => setForm({ ...form, ai_tool_name: e.target.value })} /></label>
        <label>Task type<input value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value })} /></label>
        <label>Prompt text<textarea value={form.prompt_text} onChange={(e) => setForm({ ...form, prompt_text: e.target.value })} /></label>
        <label>AI output summary<textarea value={form.ai_output_summary} onChange={(e) => setForm({ ...form, ai_output_summary: e.target.value })} /></label>
        <label>Accepted parts<textarea value={form.accepted_parts} onChange={(e) => setForm({ ...form, accepted_parts: e.target.value })} /></label>
        <label>Rejected parts<textarea value={form.rejected_parts} onChange={(e) => setForm({ ...form, rejected_parts: e.target.value })} /></label>
        <label>Manual edits<textarea value={form.manual_edits} onChange={(e) => setForm({ ...form, manual_edits: e.target.value })} /></label>
        <label>Validation performed<textarea value={form.validation_performed} onChange={(e) => setForm({ ...form, validation_performed: e.target.value })} /></label>
        <label>Remaining concerns<textarea value={form.remaining_concerns} onChange={(e) => setForm({ ...form, remaining_concerns: e.target.value })} /></label>
        {error ? <div className="error">{error}</div> : null}
        <button>Save prompt log</button>
      </form>
      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>Recorded Logs</h2>
        {logs.map((log) => <p key={log.id}><strong>{log.title}</strong> · {log.ai_tool_name} · {log.task_type}</p>)}
      </section>
    </AppShell>
  );
}

