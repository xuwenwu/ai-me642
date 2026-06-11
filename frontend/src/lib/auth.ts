'use client';

import { useEffect, useState } from 'react';
import type { User } from './types';

export const token = () => (typeof window === 'undefined' ? null : localStorage.getItem('token'));

export const setAuth = (accessToken: string, user: User) => {
  localStorage.setItem('token', accessToken);
  localStorage.setItem('user', JSON.stringify(user));
};

export const currentUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem('user');
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    localStorage.removeItem('user');
    return null;
  }
};

export const useCurrentUser = () => {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setUser(currentUser());
    setReady(true);
  }, []);

  return { user, ready };
};

export const isStaff = (user: Pick<User, 'role'> | null | undefined) => user?.role === 'instructor' || user?.role === 'ta';

export const logout = () => {
  localStorage.clear();
  location.href = '/login';
};

