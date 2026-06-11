'use client';

import { useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { api } from '@/lib/api';
import type { ProjectSpec } from '@/lib/types';

const fields = [
  ['material_system', 'Material system'],
  ['research_question', 'Research question'],
  ['physical_property', 'Physical property'],
  ['atomistic_model', 'Atomistic model'],
  ['interatomic_potential', 'Interatomic potential'],
  ['ensemble', 'Ensemble'],
  ['boundary_conditions', 'Boundary conditions'],
  ['temperature_pressure_conditions', 'Temperature/pressure conditions'],
  ['expected_outputs', 'Expected outputs'],
  ['validation_strategy', 'Validation strategy'],
  ['computational_resources', 'Computational resources'],
  ['risks_limitations', 'Risks and limitations'],
] as const;

export default function ProjectSpecPage() {
  const [form, setForm] = useState<Record<string, string>>({
    title: 'Lab 3 NVE timestep stability study',
    material_system: '',
    research_question: '',
    physical_property: 'Total-energy conservation in NVE dynamics',
    atomistic_model: '',
    interatomic_potential: '',
    potential_type: '',
    ensemble: 'NVE',
    boundary_conditions: '',
    temperature_pressure_conditions: '',
    expected_outputs: '',
    validation_strategy: 'Compare total-energy drift across timesteps and inspect LAMMPS warnings/errors.',
    computational_resources: '',
    risks_limitations: '',
  });
  const [saved, setSaved] = useState<ProjectSpec | null>(null);
  const [error, setError] = useState('');

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    try {
      setSaved(await api<ProjectSpec>('/projects', { method: 'POST', body: JSON.stringify(form) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save project');
    }
  }

  return (
    <AppShell>
      <h1>Project Specification</h1>
      <form className="form card" onSubmit={submit}>
        <label>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
        {fields.map(([key, label]) => (
          <label key={key}>{label}<textarea value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} /></label>
        ))}
        {error ? <div className="error">{error}</div> : null}
        {saved ? <div className="success">Saved project specification #{saved.id}</div> : null}
        <button>Save specification</button>
      </form>
    </AppShell>
  );
}

