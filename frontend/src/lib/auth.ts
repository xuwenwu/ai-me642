'use client';

import { useEffect, useState } from 'react';
import type { User } from './types';

function availableStorage(): Storage | null {
  if (typeof window === 'undefined') return null;
  for (const storage of [window.localStorage, window.sessionStorage]) {
    try {
      const key = '__ai_me642_storage_check__';
      storage.setItem(key, '1');
      storage.removeItem(key);
      return storage;
    } catch {
    }
  }
  return null;
}

function storedValue(key: string) {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(key) || window.sessionStorage.getItem(key);
}

export const token = () => storedValue('token');

export const setAuth = (accessToken: string, user: User) => {
  const storage = availableStorage();
  if (!storage) throw new Error('Browser storage is blocked. Enable site storage or leave private browsing mode.');
  storage.setItem('token', accessToken);
  storage.setItem('user', JSON.stringify(user));
};

export const updateStoredUser = (user: User) => {
  const storage = availableStorage();
  if (!storage) throw new Error('Browser storage is blocked. Enable site storage or leave private browsing mode.');
  storage.setItem('user', JSON.stringify(user));
};

export const currentUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const raw = storedValue('user');
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    localStorage.removeItem('user');
    sessionStorage.removeItem('user');
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
  sessionStorage.clear();
  location.href = '/login';
};
