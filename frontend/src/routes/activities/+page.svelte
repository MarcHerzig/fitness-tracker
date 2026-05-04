<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  let activities = [];
  let loading = true;

  const subtypeIcons = {
    cycling: '🚴', running: '🏃', hiking: '🥾', swimming: '🏊',
    strength: '🏋️',
  };

  onMount(async () => {
    activities = await api.getActivities({ limit: 50 });
    loading = false;
  });

  function formatDate(d) {
    return new Date(d + 'T00:00:00').toLocaleDateString('de-CH', { weekday: 'short', day: 'numeric', month: 'short' });
  }

  function stars(n) {
    return '★'.repeat(n) + '☆'.repeat(3 - n);
  }

  async function remove(id) {
    if (!confirm('Aktivität löschen?')) return;
    await api.deleteActivity(id);
    activities = activities.filter(a => a.id !== id);
  }
</script>

<div class="space-y-4">
  <div class="flex items-center gap-3">
    <button on:click={() => goto('/')} class="text-gray-400 text-xl">‹</button>
    <h2 class="text-lg font-bold">Alle Aktivitäten</h2>
  </div>

  {#if loading}
    <div class="text-center text-gray-500 py-8">Laden...</div>
  {:else if activities.length === 0}
    <div class="card text-center text-gray-500 py-10">
      <div class="text-4xl mb-2">🏁</div>
      Noch keine Aktivitäten.
    </div>
  {:else}
    <div class="space-y-2">
      {#each activities as a}
        <div class="card flex items-center gap-3">
          <span class="text-2xl">{subtypeIcons[a.subtype] || '⚡'}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-medium">{formatDate(a.activity_date)}</span>
              <span class="text-primary font-bold">{stars(a.stars)}</span>
            </div>
            <div class="text-sm text-gray-400 mt-0.5">
              {#if a.distance_km}📍 {a.distance_km} km{/if}
              {#if a.activity_exercises?.length}💪 {a.activity_exercises.length} Übungen{/if}
            </div>
          </div>
          <button on:click={() => remove(a.id)} class="text-gray-600 hover:text-red-400 transition-colors px-1">🗑</button>
        </div>
      {/each}
    </div>
  {/if}
</div>
