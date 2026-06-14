'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { setAuth } from '@/lib/auth';
import type { User } from '@/lib/types';

type LoginResponse = {
  access_token: string;
  user: User;
};

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await api<LoginResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }, false);
      setAuth(result.access_token, result.user);
      window.location.assign(result.user.must_change_password ? '/account/password' : '/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="main">
      <section className="card" style={{ maxWidth: 520, margin: '4rem auto' }}>
        <h1>AI-ME642 Studio</h1>
        <p className="muted">Sign in with your course account.</p>
        <form className="form" onSubmit={submit}>
          <label>Email<input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          {error ? <div className="error" role="alert">{error}</div> : null}
          {busy ? <div className="muted" role="status">Signing in...</div> : null}
          <button type="submit" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'}</button>
        </form>
      </section>
    </main>
  );
}
