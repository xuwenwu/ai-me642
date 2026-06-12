'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { api } from '@/lib/api';
import type { AIPolicy, Assignment, ProjectSpec, PromptLog, PromptTemplate } from '@/lib/types';

export default function PromptLogsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [projects, setProjects] = useState<ProjectSpec[]>([]);
  const [logs, setLogs] = useState<PromptLog[]>([]);
  const [policy, setPolicy] = useState<AIPolicy | null>(null);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
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
    const [a, p, l, aiPolicy, t] = await Promise.all([
      api<Assignment[]>('/assignments'),
      api<ProjectSpec[]>('/projects'),
      api<PromptLog[]>('/prompt-logs'),
      api<AIPolicy>('/prompt-logs/policy'),
      api<PromptTemplate[]>('/prompt-logs/templates'),
    ]);
    setAssignments(a);
    setProjects(p);
    setLogs(l);
    setPolicy(aiPolicy);
    setTemplates(t);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load prompt logs'));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');
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
      setMessage('Prompt log saved. It will be included in validation evidence and submission ZIP exports.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prompt log');
    }
  }

  async function generateAssistantLog() {
    setError('');
    setMessage('');
    setIsGenerating(true);
    try {
      const log = await api<PromptLog>('/prompt-logs/assistant', {
        method: 'POST',
        body: JSON.stringify({
          title: form.title.trim() || 'Course assistant guidance',
          assignment_id: form.assignment_id ? Number(form.assignment_id) : null,
          project_id: form.project_id ? Number(form.project_id) : null,
          task_type: form.task_type,
          prompt_text: form.prompt_text,
        }),
      });
      await load();
      setForm({
        ...form,
        title: log.title,
        ai_tool_name: log.ai_tool_name,
        task_type: log.task_type,
        ai_output_summary: log.ai_output_summary,
      });
      const flags = log.privacy_flags.length ? ` Privacy flags: ${log.privacy_flags.join(', ')}.` : '';
      setMessage(`Course assistant guidance saved to prompt logs.${flags}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate course assistant guidance');
    } finally {
      setIsGenerating(false);
    }
  }

  function applyTemplate(templateId: string) {
    setSelectedTemplateId(templateId);
    const template = templates.find((item) => item.id === Number(templateId));
    if (!template) return;
    setForm({
      ...form,
      title: template.title,
      task_type: template.task_type,
      prompt_text: template.prompt_text,
    });
  }

  const selectedTemplate = templates.find((item) => item.id === Number(selectedTemplateId));

  return (
    <AppShell>
      <h1>AI Prompt Logs</h1>
      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}

      <div className="grid two">
        <section className="card">
          <h2>{policy?.title || 'Responsible AI Use Policy'}</h2>
          <p>{policy?.body || 'Loading policy...'}</p>
          {policy?.allowed_tools.length ? <p className="muted">Allowed tools: {policy.allowed_tools.join(', ')}</p> : null}
          {policy?.disclosure_requirements.length ? (
            <div className="prompt-cues">
              {policy.disclosure_requirements.map((item) => <p key={item}>{item}</p>)}
            </div>
          ) : null}
        </section>

        <section className="card">
          <h2>Prompt Template</h2>
          <label>Template<select value={selectedTemplateId} onChange={(e) => applyTemplate(e.target.value)}>
            <option value="">Start from blank or choose a template</option>
            {templates.map((template) => <option key={template.id} value={template.id}>{template.title}</option>)}
          </select></label>
          {selectedTemplate ? (
            <div className="assignment-context" style={{ marginTop: '0.85rem' }}>
              <strong>{selectedTemplate.task_type}</strong>
              {selectedTemplate.checklist.map((item) => <p key={item}>{item}</p>)}
            </div>
          ) : <p className="muted">Templates provide guardrails for common ME642 AI-assistance tasks.</p>}
        </section>
      </div>

      <form className="form card" onSubmit={submit} style={{ marginTop: '1rem' }}>
        <div className="filter-grid">
          <label>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <label>AI tool<input value={form.ai_tool_name} onChange={(e) => setForm({ ...form, ai_tool_name: e.target.value })} /></label>
          <label>Task type<input value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value })} /></label>
        </div>
        <div className="filter-grid">
          <label>Assignment<select value={form.assignment_id} onChange={(e) => setForm({ ...form, assignment_id: e.target.value })}>
            <option value="">Select assignment</option>
            {assignments.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}
          </select></label>
          <label>Project<select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })}>
            <option value="">Optional project</option>
            {projects.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
          </select></label>
        </div>
        <label>Prompt text<textarea value={form.prompt_text} onChange={(e) => setForm({ ...form, prompt_text: e.target.value })} /></label>
        <label>AI output summary<textarea value={form.ai_output_summary} onChange={(e) => setForm({ ...form, ai_output_summary: e.target.value })} /></label>
        <div className="grid two">
          <label>Accepted parts<textarea value={form.accepted_parts} onChange={(e) => setForm({ ...form, accepted_parts: e.target.value })} /></label>
          <label>Rejected parts<textarea value={form.rejected_parts} onChange={(e) => setForm({ ...form, rejected_parts: e.target.value })} /></label>
        </div>
        <label>Manual edits<textarea value={form.manual_edits} onChange={(e) => setForm({ ...form, manual_edits: e.target.value })} /></label>
        <label>Validation performed<textarea value={form.validation_performed} onChange={(e) => setForm({ ...form, validation_performed: e.target.value })} /></label>
        <label>Remaining concerns<textarea value={form.remaining_concerns} onChange={(e) => setForm({ ...form, remaining_concerns: e.target.value })} /></label>
        <div className="row">
          <button>Save prompt log</button>
          {policy?.assistant_enabled ? (
            <button className="secondary" type="button" onClick={generateAssistantLog} disabled={isGenerating || !form.prompt_text.trim()}>
              {isGenerating ? 'Generating...' : 'Generate logged guidance'}
            </button>
          ) : null}
        </div>
      </form>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>Recorded Logs</h2>
        {logs.length ? (
          logs.map((log) => (
            <p key={log.id}>
              <strong>{log.title}</strong> - {log.ai_tool_name} - {log.task_type}
              {log.provider_status !== 'manual' ? <span className="muted"> - {log.provider_status}</span> : null}
            </p>
          ))
        ) : <p className="muted">No prompt logs recorded yet.</p>}
      </section>
    </AppShell>
  );
}
