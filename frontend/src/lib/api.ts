'use client';

import { token } from './auth';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, message: string, body: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

function messageFromBody(body: string) {
  try {
    const parsed = JSON.parse(body);
    if (typeof parsed.detail === 'string') return parsed.detail;
    if (Array.isArray(parsed.detail)) return parsed.detail.map((item: { msg?: string }) => item.msg || JSON.stringify(item)).join(', ');
  } catch {
  }
  return body || 'Request failed';
}

function headers(init: RequestInit = {}, authenticated = true) {
  const h = new Headers(init.headers);
  if (!(init.body instanceof FormData)) h.set('Content-Type', 'application/json');
  const t = token();
  if (authenticated && t) h.set('Authorization', `Bearer ${t}`);
  return h;
}

export async function api<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: headers(init, authenticated) });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, messageFromBody(body), body);
  }
  const contentType = response.headers.get('content-type') || '';
  return (contentType.includes('json') ? response.json() : response.text()) as Promise<T>;
}

export async function download(path: string, filename: string) {
  const response = await fetch(`${API}${path}`, { headers: headers() });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, messageFromBody(body), body);
  }
  const blob = await response.blob();
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
