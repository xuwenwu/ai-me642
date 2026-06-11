'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { setAuth } from '@/lib/auth';
import type { User } from '@/lib/types';

type LoginResponse = {
  access_token: string;
  user: User;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('student@example.edu');
  const [password, setPassword] = useState('password123');
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
      router.push('/dashboard');
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
        <p className="muted">Sign in with a seeded account to test the Phase II pilot workflow.</p>
        <form className="form" onSubmit={submit}>
          <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
          {error ? <div className="error">{error}</div> : null}
          <button disabled={busy}>{busy ? 'Signing in...' : 'Sign in'}</button>
        </form>
        <p className="muted">Try `student@example.edu`, `ta@example.edu`, or `instructor@example.edu` with `password123`.</p>
      </section>
    </main>
  );
}
