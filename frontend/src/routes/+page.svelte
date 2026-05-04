<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { user, token } from '$lib/stores';

  let dashboard = null;
  let loading = true;
  let showWeightModal = false;
  let newWeight = '';
  let weightDate = new Date().toISOString().split('T')[0];
  let weightError = '';

  const DAYS = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];

  onMount(async () => {
    try {
      dashboard = await api.dashboard();
    } catch (e) {
      if (e.message === 'Fehler') goto('/login');
    } finally {
      loading = false;
    }
  });

  function stars(n) {
    return '★'.repeat(n) + '☆'.repeat(3 - n);
  }

  function dayLabel(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (d.getTime() === today.getTime()) return 'Heute';
    return DAYS[d.getDay()];
  }

  async function submitWeight() {
    weightError = '';
    const kg = parseFloat(newWeight);
    if (!kg || kg < 20 || kg > 300) { weightError = 'Ungültiges Gewicht'; return; }
    try {
      await api.addBodyWeight({ measured_at: weightDate, weight_kg: kg });
      dashboard = await api.dashboard();
      showWeightModal = false;
      newWeight = '';
    } catch (e) {
      weightError = e.message;
    }
  }

  function logout() {
    token.set(null);
    user.set(null);
    localStorage.removeItem('token');
    goto('/login');
  }
</script>

{#if loading}
  <div class="flex items-center justify-center h-48 text-gray-400">Laden...</div>
{:else if dashboard}
  <div class="space-y-5">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold">Fitness</h1>
      <div class="flex gap-2">
        <button on:click={() => showWeightModal = true} class="text-sm text-gray-400 px-3 py-1 rounded-lg border border-gray-700">⚖️ Gewicht</button>
        <button on:click={logout} class="text-sm text-gray-500 px-3 py-1">Logout</button>
      </div>
    </div>

    <!-- Side-by-side: Marc & Pia -->
    <div class="grid grid-cols-2 gap-3">
      {#each [dashboard.marc, dashboard.pia] as person}
        {#if person}
          <div class="card space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-bold capitalize">{person.username}</span>
              <span class="text-primary font-bold">{stars(person.today_stars)}</span>
            </div>

            <!-- Week strip -->
            <div class="grid grid-cols-7 gap-0.5">
              {#each person.week as day}
                <div class="flex flex-col items-center">
                  <span class="text-gray-500 text-xs">{dayLabel(day.date)}</span>
                  <div class="flex flex-col gap-0.5 mt-0.5">
                    {#each [1,2,3] as s}
                      <div class="w-2 h-2 rounded-full {day.stars >= s ? 'bg-primary' : 'bg-gray-700'}"></div>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>

            <!-- 2-week stats -->
            <div class="flex justify-between text-xs text-gray-400 border-t border-gray-700 pt-2">
              <span>⭐ {person.two_week_total_stars} Sterne</span>
              <span>📅 {person.two_week_training_days} Tage</span>
              {#if person.last_weight}
                <span>⚖️ {person.last_weight}kg</span>
              {/if}
            </div>
          </div>
        {/if}
      {/each}
    </div>

    <!-- Weight chart (if both have data) -->
    {#if (dashboard.marc?.weight_history?.length || dashboard.pia?.weight_history?.length)}
      <div class="card">
        <h3 class="text-sm font-semibold text-gray-300 mb-3">Gewichtsverlauf</h3>
        <div class="space-y-1">
          {#each [...(dashboard.marc?.weight_history || []).map(w => ({...w, who:'marc'})),
                  ...(dashboard.pia?.weight_history || []).map(w => ({...w, who:'pia'}))]
            .sort((a, b) => b.measured_at.localeCompare(a.measured_at))
            .slice(0, 10) as entry}
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">{new Date(entry.measured_at + 'T00:00:00').toLocaleDateString('de-CH', {day:'numeric', month:'short'})}</span>
              <span class="capitalize text-gray-500 text-xs">{entry.who}</span>
              <span class="font-medium">{entry.weight_kg} kg</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- New activity button -->
    <button on:click={() => goto('/activities/new')} class="btn-primary w-full text-center text-lg py-4">
      + Aktivität erfassen
    </button>

    <!-- Recent activities -->
    <button on:click={() => goto('/activities')} class="w-full text-sm text-gray-400 text-center py-2">
      Alle Aktivitäten anzeigen →
    </button>
  </div>

  <!-- Weight modal -->
  {#if showWeightModal}
    <div class="fixed inset-0 bg-black/70 flex items-center justify-center p-6 z-50" on:click|self={() => showWeightModal = false}>
      <div class="card w-full max-w-sm space-y-4">
        <h3 class="font-bold text-lg">Gewicht eintragen</h3>
        <div>
          <label class="label">Datum</label>
          <input bind:value={weightDate} type="date" class="input" />
        </div>
        <div>
          <label class="label">Gewicht (kg)</label>
          <input bind:value={newWeight} type="number" step="0.1" min="20" max="300" class="input" placeholder="z.B. 78.5" />
        </div>
        {#if weightError}
          <p class="text-red-400 text-sm">{weightError}</p>
        {/if}
        <div class="flex gap-3">
          <button on:click={() => showWeightModal = false} class="flex-1 py-2 rounded-xl border border-gray-600 text-gray-400">Abbrechen</button>
          <button on:click={submitWeight} class="flex-1 btn-primary">Speichern</button>
        </div>
      </div>
    </div>
  {/if}
{/if}
