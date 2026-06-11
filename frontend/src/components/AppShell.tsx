'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { isStaff, logout, useCurrentUser } from '@/lib/auth';

export function AppShell({ children }: { children: ReactNode }) {
  const { user, ready } = useCurrentUser();

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <Link className="brand" href="/dashboard">AI-ME642 Studio</Link>
          <div className="muted">Responsible AI-assisted scientific computing</div>
        </div>
        <nav className="nav">
          <Link href="/dashboard">Dashboard</Link>
          <Link href="/projects/new">Project Spec</Link>
          <Link href="/prompt-logs">Prompt Logs</Link>
          <Link href="/submissions">Submission</Link>
          {ready && isStaff(user) ? <Link href="/instructor">Instructor</Link> : null}
          {ready && user ? <button className="secondary" onClick={logout}>Logout</button> : <Link href="/login">Login</Link>}
        </nav>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}
