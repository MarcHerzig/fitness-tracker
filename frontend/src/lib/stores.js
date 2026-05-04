import { writable } from 'svelte/store';

const storedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;

export const token = writable(storedToken);
export const user = writable(null);

token.subscribe((t) => {
  if (typeof localStorage !== 'undefined') {
    if (t) localStorage.setItem('token', t);
    else localStorage.removeItem('token');
  }
});
