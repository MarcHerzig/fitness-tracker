import { token } from '$lib/stores';
import { get } from 'svelte/store';

const BASE = typeof window !== 'undefined'
  ? (import.meta.env.VITE_API_URL || '/api')
  : '/api';

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const t = get(token);
  if (t) headers['Authorization'] = `Bearer ${t}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  if (res.status === 401) {
    token.set(null);
    localStorage.removeItem('token');
    window.location.href = '/login';
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Fehler' }));
    throw new Error(err.detail || 'Fehler');
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  login: (username, password) => request('POST', '/auth/login', { username, password }),
  register: (username, email, password) => request('POST', '/auth/register', { username, email, password }),
  me: () => request('GET', '/auth/me'),

  getActivities: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/activities${q ? '?' + q : ''}`);
  },
  getActivity: (id) => request('GET', `/activities/${id}`),
  createActivity: (data) => request('POST', '/activities', data),
  deleteActivity: (id) => request('DELETE', `/activities/${id}`),
  exportCsv: () => {
    const t = get(token);
    window.open(`${BASE}/activities/export/csv?token=${t}`, '_blank');
  },

  weeklyStats: () => request('GET', '/stats/weekly'),
  monthlyStats: () => request('GET', '/stats/monthly'),
  prs: () => request('GET', '/stats/prs'),
  streak: () => request('GET', '/stats/streak')
};
