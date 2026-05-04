<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { user } from '$lib/stores';

  let activities = [];
  let streak = null;
  let loading = true;

  const subtypeIcons = {
    cycling: '🚴', running: '🏃', hiking: '🥾', swimming: '🏊',
    weightlifting: '🏋️', calisthenics: '💪', yoga: '🧘', other: '⚡'
  };

  onMount(async () => {
    try {
      [activities, streak] = await Promise.all([
        api.getActivities({ limit: 20 }),
        api.streak()
      ]);
    } finally {
      loading = false;
    }
  });

  function formatDuration(mins) {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString('de-CH', { weekday: 'short', day: 'numeric', month: 'short' });
  }
</script>

<div class="space-y-4">
  {#if $user}
    <div class="flex items-center justify-between">
      <div>
        <p class="text-gray-400 text-sm">Hallo,</p>
        <h2 class="text-xl font-bold">{$user.username} 👋</h2>
      </div>
      {#if streak}
        <div class="card text-center px-5">
          <div class="text-2xl font-bold text-primary">{streak.current_streak}</div>
          <div class="text-xs text-gray-400">Streak 🔥</div>
        </div>
      {/if}
    </div>
  {/if}

  <button on:click={() => goto('/activities/new')} class="btn-primary w-full text-center">
    + Aktivität erfassen
  </button>

  <h3 class="font-semibold text-gray-300 mt-4">Letzte Aktivitäten</h3>

  {#if loading}
    <div class="text-center text-gray-500 py-8">Laden...</div>
  {:else if activities.length === 0}
    <div class="card text-center text-gray-500 py-8">
      <div class="text-4xl mb-2">🏁</div>
      Noch keine Aktivitäten. Los geht's!
    </div>
  {:else}
    <div class="space-y-2">
      {#each activities as activity}
        <button
          on:click={() => goto(`/activities/${activity.id}`)}
          class="card w-full text-left flex items-center gap-3 hover:bg-gray-700 transition-colors"
        >
          <span class="text-3xl">{subtypeIcons[activity.subtype] || '⚡'}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-medium capitalize">{activity.subtype}</span>
              <span class="text-gray-400 text-sm">{formatDate(activity.activity_date)}</span>
            </div>
            <div class="text-sm text-gray-400 flex gap-3 mt-0.5">
              <span>⏱ {formatDuration(activity.duration_minutes)}</span>
              {#if activity.distance_km}
                <span>📍 {activity.distance_km} km</span>
              {/if}
              {#if activity.exercises?.length}
                <span>💪 {activity.exercises.length} Übungen</span>
              {/if}
            </div>
          </div>
          <span class="text-gray-600">›</span>
        </button>
      {/each}
    </div>
  {/if}
</div>
