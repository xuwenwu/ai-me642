'use client';

import { useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { api } from '@/lib/api';
import { updateStoredUser, useCurrentUser } from '@/lib/auth';
import type { User } from '@/lib/types';

export default function PasswordPage() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { user } = useCurrentUser();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage('');
    setError('');
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }
    setBusy(true);
    try {
      const updated = await api<User>('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      updateStoredUser(updated);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setMessage('Password updated.');
      if (user?.must_change_password) {
        window.location.assign('/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update password');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="section-header">
        <h1>Account</h1>
      </div>
      <section className="card" style={{ maxWidth: 620 }}>
        <h2>Change Password</h2>
        {user?.must_change_password ? <div className="error">Password change required before using the course workspace.</div> : null}
        {error ? <div className="error" role="alert">{error}</div> : null}
        {message ? <div className="success" role="status">{message}</div> : null}
        <form className="form" onSubmit={submit} style={{ marginTop: '0.85rem' }}>
          <label>Current password<input type="password" autoComplete="current-password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required /></label>
          <label>New password<input type="password" autoComplete="new-password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} minLength={10} required /></label>
          <label>Confirm new password<input type="password" autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} minLength={10} required /></label>
          <button type="submit" disabled={busy}>{busy ? 'Updating...' : 'Update password'}</button>
        </form>
      </section>
    </AppShell>
  );
}
