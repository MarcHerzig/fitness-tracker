<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let weekly = [];
  let monthly = [];
  let prs = [];
  let streak = null;
  let loading = true;
  let activeTab = 'weekly';

  onMount(async () => {
    try {
      [weekly, monthly, prs, streak] = await Promise.all([
        api.weeklyStats(),
        api.monthlyStats(),
        api.prs(),
        api.streak()
      ]);
    } finally {
      loading = false;
    }
  });

  function formatDate(d) {
    return new Date(d).toLocaleDateString('de-CH', { day: 'numeric', month: 'short' });
  }

  function monthName(m) {
    return new Date(2024, m - 1, 1).toLocaleDateString('de-CH', { month: 'short' });
  }

  function formatDuration(mins) {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  const maxWeeklyDuration = () => Math.max(...weekly.map(w => w.total_duration_minutes), 1);
  const maxMonthlyDuration = () => Math.max(...monthly.map(m => m.total_duration_minutes), 1);
</script>

<div class="space-y-4">
  <h2 class="text-lg font-bold">Statistiken</h2>

  {#if loading}
    <div class="text-center text-gray-500 py-12">Laden...</div>
  {:else}
    <!-- Streak -->
    {#if streak}
      <div class="grid grid-cols-2 gap-3">
        <div class="card text-center">
          <div class="text-3xl font-bold text-primary">{streak.current_streak}</div>
          <div class="text-xs text-gray-400 mt-1">Aktueller Streak 🔥</div>
        </div>
        <div class="card text-center">
          <div class="text-3xl font-bold text-yellow-400">{streak.longest_streak}</div>
          <div class="text-xs text-gray-400 mt-1">Längster Streak 🏆</div>
        </div>
      </div>
    {/if}

    <!-- Tabs -->
    <div class="flex gap-1 bg-surface rounded-xl p-1">
      {#each [['weekly', 'Wochen'], ['monthly', 'Monate'], ['prs', 'Rekorde']] as [tab, label]}
        <button
          on:click={() => activeTab = tab}
          class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
          class:bg-primary={activeTab === tab}
          class:text-white={activeTab === tab}
          class:text-gray-400={activeTab !== tab}
        >{label}</button>
      {/each}
    </div>

    <!-- Wochen -->
    {#if activeTab === 'weekly'}
      <div class="space-y-3">
        {#each weekly as w}
          <div class="card">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm font-medium">KW {formatDate(w.week_start)}</span>
              <span class="text-xs text-gray-400">{w.total_activities} Aktivitäten</span>
            </div>
            <div class="h-2 bg-bg rounded-full overflow-hidden mb-3">
              <div
                class="h-full bg-primary rounded-full transition-all"
                style="width: {(w.total_duration_minutes / maxWeeklyDuration()) * 100}%"
              ></div>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center text-xs text-gray-400">
              <div><span class="block text-white font-medium">{formatDuration(w.total_duration_minutes)}</span>Dauer</div>
              <div><span class="block text-white font-medium">{w.total_distance_km} km</span>Distanz</div>
              <div><span class="block text-white font-medium">{w.total_volume_kg} kg</span>Volumen</div>
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Monate -->
    {#if activeTab === 'monthly'}
      <div class="space-y-3">
        {#each monthly as m}
          <div class="card">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm font-medium">{monthName(m.month)} {m.year}</span>
              <span class="text-xs text-gray-400">{m.total_activities} Aktivitäten</span>
            </div>
            <div class="h-2 bg-bg rounded-full overflow-hidden mb-3">
              <div
                class="h-full bg-blue-500 rounded-full"
                style="width: {(m.total_duration_minutes / maxMonthlyDuration()) * 100}%"
              ></div>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center text-xs text-gray-400">
              <div><span class="block text-white font-medium">{formatDuration(m.total_duration_minutes)}</span>Dauer</div>
              <div><span class="block text-white font-medium">{m.total_distance_km} km</span>Distanz</div>
              <div><span class="block text-white font-medium">{m.total_volume_kg} kg</span>Volumen</div>
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- PRs -->
    {#if activeTab === 'prs'}
      <div class="space-y-2">
        {#if prs.length === 0}
          <div class="card text-center text-gray-500 py-8">
            Noch keine Krafteinträge vorhanden
          </div>
        {:else}
          {#each prs as pr}
            <div class="card flex items-center justify-between">
              <div>
                <div class="font-medium">{pr.exercise_name}</div>
                <div class="text-xs text-gray-400 mt-0.5">{new Date(pr.achieved_on).toLocaleDateString('de-CH')}</div>
              </div>
              <div class="text-right">
                <div class="text-primary font-bold">{pr.max_weight_kg} kg</div>
                {#if pr.max_reps}
                  <div class="text-xs text-gray-400">{pr.max_reps} Wdh.</div>
                {/if}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    {/if}

    <!-- Export -->
    <button on:click={() => api.exportCsv()} class="btn-ghost w-full border border-gray-700 mt-2">
      ↓ CSV exportieren
    </button>
  {/if}
</div>
