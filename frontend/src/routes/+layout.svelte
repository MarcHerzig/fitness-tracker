<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { token, user } from '$lib/stores';
  import { api } from '$lib/api';

  onMount(async () => {
    if ($page.url.pathname === '/login') return;
    if (!$token) { goto('/login'); return; }
    try {
      user.set(await api.me());
    } catch {
      token.set(null);
      goto('/login');
    }
  });
</script>

{#if $page.url.pathname === '/login'}
  <div class="min-h-screen bg-bg text-white">
    <slot />
  </div>
{:else}
  <div class="min-h-screen bg-bg text-white">
    <div class="max-w-2xl mx-auto px-4 pt-5 pb-8">
      <slot />
    </div>
  </div>
{/if}
