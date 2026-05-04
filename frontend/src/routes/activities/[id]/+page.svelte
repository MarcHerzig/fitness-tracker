<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let activity = null;
  let loading = true;
  let deleting = false;

  const subtypeIcons = {
    cycling: '🚴', running: '🏃', hiking: '🥾', swimming: '🏊',
    weightlifting: '🏋️', calisthenics: '💪', yoga: '🧘', other: '⚡'
  };

  onMount(async () => {
    try {
      activity = await api.getActivity($page.params.id);
    } finally {
      loading = false;
    }
  });

  async function deleteActivity() {
    if (!confirm('Aktivität löschen?')) return;
    deleting = true;
    await api.deleteActivity(activity.id);
    goto('/');
  }

  function formatDuration(mins) {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('de-CH', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-2">
    <button on:click={() => goto('/')} class="text-gray-400">‹ Zurück</button>
    {#if activity}
      <button on:click={deleteActivity} disabled={deleting} class="text-red-400 text-sm">Löschen</button>
    {/if}
  </div>

  {#if loading}
    <div class="text-center text-gray-500 py-12">Laden...</div>
  {:else if activity}
    <div class="card text-center py-6">
      <div class="text-6xl mb-2">{subtypeIcons[activity.subtype] || '⚡'}</div>
      <h2 class="text-xl font-bold capitalize">{activity.subtype}</h2>
      <p class="text-gray-400 mt-1">{formatDate(activity.activity_date)}</p>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div class="card text-center">
        <div class="text-2xl font-bold text-primary">{formatDuration(activity.duration_minutes)}</div>
        <div class="text-xs text-gray-400 mt-1">Dauer</div>
      </div>
      {#if activity.distance_km}
        <div class="card text-center">
          <div class="text-2xl font-bold text-primary">{activity.distance_km} km</div>
          <div class="text-xs text-gray-400 mt-1">Distanz</div>
        </div>
      {/if}
    </div>

    {#if activity.exercises?.length}
      <div class="space-y-3">
        <h3 class="font-semibold text-gray-300">Übungen</h3>
        {#each activity.exercises as ex}
          <div class="card">
            <h4 class="font-medium mb-3">{ex.name}</h4>
            <div class="space-y-1.5">
              <div class="grid grid-cols-4 gap-2 text-xs text-gray-500 mb-2">
                <span>Satz</span><span class="text-center">Wdh.</span><span class="text-center">kg</span><span class="text-center">Pause</span>
              </div>
              {#each ex.sets as set}
                <div class="grid grid-cols-4 gap-2 text-sm">
                  <span class="text-gray-400">S{set.set_number}</span>
                  <span class="text-center">{set.reps ?? '—'}</span>
                  <span class="text-center">{set.weight_kg ?? '—'}</span>
                  <span class="text-center text-gray-400">{set.rest_seconds ? set.rest_seconds + 's' : '—'}</span>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    {/if}

    {#if activity.notes}
      <div class="card">
        <h3 class="font-semibold text-gray-300 mb-2">Notizen</h3>
        <p class="text-gray-300">{activity.notes}</p>
      </div>
    {/if}
  {/if}
</div>
