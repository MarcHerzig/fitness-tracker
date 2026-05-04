<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { token, user } from '$lib/stores';
  import { api } from '$lib/api';

  const publicRoutes = ['/login'];

  onMount(async () => {
    if (publicRoutes.includes($page.url.pathname)) return;
    if (!$token) { goto('/login'); return; }
    try {
      $user = await api.me();
    } catch {
      goto('/login');
    }
  });

  const navItems = [
    { href: '/', label: 'Home', icon: '🏠' },
    { href: '/activities/new', label: 'Neu', icon: '➕' },
    { href: '/stats', label: 'Stats', icon: '📊' }
  ];

  function logout() {
    token.set(null);
    user.set(null);
    goto('/login');
  }
</script>

<div class="min-h-screen flex flex-col pb-20">
  {#if !publicRoutes.includes($page.url.pathname)}
    <header class="sticky top-0 z-10 bg-bg/90 backdrop-blur border-b border-gray-800 px-4 py-3 flex items-center justify-between">
      <h1 class="text-lg font-bold text-primary">Fitness</h1>
      {#if $user}
        <button on:click={logout} class="text-gray-400 text-sm">Logout</button>
      {/if}
    </header>
  {/if}

  <main class="flex-1 max-w-2xl mx-auto w-full px-4 py-4">
    <slot />
  </main>

  {#if !publicRoutes.includes($page.url.pathname)}
    <nav class="fixed bottom-0 left-0 right-0 bg-bg/95 backdrop-blur border-t border-gray-800 flex justify-around py-2 z-10">
      {#each navItems as item}
        <a
          href={item.href}
          class="flex flex-col items-center gap-1 px-4 py-1 rounded-xl transition-colors"
          class:text-primary={$page.url.pathname === item.href}
          class:text-gray-500={$page.url.pathname !== item.href}
        >
          <span class="text-xl">{item.icon}</span>
          <span class="text-xs">{item.label}</span>
        </a>
      {/each}
    </nav>
  {/if}
</div>
