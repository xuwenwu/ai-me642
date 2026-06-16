'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useEffect } from 'react';
import { isStaff, logout, useCurrentUser } from '@/lib/auth';

export function AppShell({ children }: { children: ReactNode }) {
  const { user, ready } = useCurrentUser();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (ready && user?.must_change_password && pathname !== '/account/password') {
      router.replace('/account/password');
    }
  }, [pathname, ready, router, user]);

  const locked = Boolean(user?.must_change_password);

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <Link className="brand" href="/dashboard">AI-ME642 Studio</Link>
          <div className="muted">Responsible AI-assisted scientific computing</div>
        </div>
        <nav className="nav">
          {!locked ? <Link href="/dashboard">Dashboard</Link> : null}
          {!locked ? <Link href="/projects/new">Project Spec</Link> : null}
          {!locked ? <Link href="/prompt-logs">Prompt Logs</Link> : null}
          {!locked ? <Link href="/submissions">Submission</Link> : null}
          {ready && isStaff(user) && !locked ? <Link href="/instructor">Instructor</Link> : null}
          {ready && user ? <Link href="/account/password">Account</Link> : null}
          {ready && user ? <button className="secondary" onClick={logout}>Logout</button> : <Link href="/login">Login</Link>}
        </nav>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}
