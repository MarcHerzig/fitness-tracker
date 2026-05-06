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

  const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

  const EMOJI = {
    cycling:  '🚴',
    running:  '🏃',
    hiking:   '🥾',
    swimming: '🏊',
    strength: '🏋️',
  };

  function activityEmoji(subtypes) {
    return subtypes.map(s => EMOJI[s] ?? '●').join('');
  }

  function todayEmoji(person) {
    const todayStr = new Date().toISOString().split('T')[0];
    const day = person.month?.find(d => d.date === todayStr);
    if (day?.subtypes?.length) return activityEmoji(day.subtypes);
    return person.today_stars > 0 ? '🏋️' : '';
  }

  onMount(async () => {
    try {
      dashboard = await api.dashboard();
    } catch (e) {
      goto('/login');
    } finally {
      loading = false;
    }
  });

  // Build month grid: array of {day, stars, subtypes} | null (empty offset cells)
  function monthGrid(monthDays) {
    if (!monthDays?.length) return [];
    const first = new Date(monthDays[0].date + 'T00:00:00');
    const offset = (first.getDay() + 6) % 7; // Mon=0 … Sun=6
    const cells = Array(offset).fill(null);
    for (const d of monthDays) {
      const dayNum = new Date(d.date + 'T00:00:00').getDate();
      cells.push({ day: dayNum, stars: d.stars, subtypes: d.subtypes ?? [] });
    }
    return cells;
  }

  function starColor(s) {
    if (s >= 3) return 'bg-primary';
    if (s === 2) return 'bg-primary/60';
    if (s === 1) return 'bg-primary/30';
    return 'bg-gray-800';
  }

  async function submitWeight() {
    weightError = '';
    const kg = parseFloat(newWeight);
    if (!kg || kg < 20 || kg > 300) { weightError = 'Ungültig'; return; }
    try {
      await api.addBodyWeight({ measured_at: weightDate, weight_kg: kg });
      dashboard = await api.dashboard();
      showWeightModal = false;
      newWeight = '';
    } catch (e) { weightError = e.message; }
  }

  async function deleteWeight(id) {
    await api.deleteBodyWeight(id);
    dashboard = await api.dashboard();
  }

  function logout() {
    token.set(null); user.set(null);
    localStorage.removeItem('token');
    goto('/login');
  }

  function maxMonthStars(person) {
    if (!person?.monthly_stars?.length) return 1;
    return Math.max(1, ...person.monthly_stars.map(m => m.stars));
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
        <button on:click={() => showWeightModal = true}
          class="text-sm text-gray-400 px-3 py-1 rounded-lg border border-gray-700">⚖️ Gewicht</button>
        <button on:click={logout} class="text-sm text-gray-500 px-2 py-1">Logout</button>
      </div>
    </div>

    <!-- Side-by-side cards -->
    <div class="grid grid-cols-2 gap-3">
      {#each [dashboard.marc, dashboard.pia] as person}
        {#if person}
          {@const grid = monthGrid(person.month)}
          <div class="card space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-bold capitalize">{person.username}</span>
              <span class="text-lg leading-none">{todayEmoji(person)}</span>
            </div>

            <!-- Month calendar -->
            <div>
              <!-- Day-of-week header -->
              <div class="grid grid-cols-7 gap-px mb-1">
                {#each DAY_LABELS as lbl}
                  <div class="text-center text-gray-600 text-xs leading-none">{lbl}</div>
                {/each}
              </div>
              <!-- Day cells -->
              <div class="grid grid-cols-7 gap-px">
                {#each grid as cell}
                  {#if cell === null}
                    <div></div>
                  {:else}
                    <div class="flex flex-col items-center gap-0.5">
                      <div class="text-gray-600 text-xs leading-none">{cell.day}</div>
                      <div class="w-full aspect-square rounded-sm {starColor(cell.stars)} flex items-center justify-center overflow-hidden">
                        {#if cell.stars > 0}
                          <span style="font-size:0.65rem;line-height:1">{activityEmoji(cell.subtypes)}</span>
                        {/if}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            </div>

            <!-- 2-week summary -->
            <div class="flex justify-between text-xs text-gray-400 border-t border-gray-700 pt-2">
              <span>⭐ {person.two_week_total_stars}</span>
              <span>📅 {person.two_week_training_days}d</span>
              {#if person.last_weight}
                <span>⚖️ {person.last_weight}kg</span>
              {/if}
            </div>
          </div>
        {/if}
      {/each}
    </div>

    <!-- 6-Monats-Statistik -->
    <div class="card space-y-3">
      <h3 class="text-sm font-semibold text-gray-300">Letzte 6 Monate</h3>
      <div class="grid grid-cols-2 gap-3">
        {#each [dashboard.marc, dashboard.pia] as person}
          {#if person}
            {@const maxS = maxMonthStars(person)}
            <div class="space-y-1">
              <div class="flex items-center gap-1 mb-1.5">
                <span class="text-xs text-gray-500 capitalize font-medium flex-1">{person.username}</span>
                <span class="text-xs text-gray-600 w-4 text-right shrink-0">🏋️</span>
                <span class="text-xs text-gray-600 w-9 text-right shrink-0">🚴</span>
              </div>
              {#each [...person.monthly_stars].reverse() as m}
                <div class="flex items-center gap-1">
                  <span class="text-xs text-gray-500 w-9 shrink-0">{m.label}</span>
                  <div class="flex-1 bg-gray-800 rounded-full h-2.5 overflow-hidden">
                    <div
                      class="h-2.5 rounded-full bg-primary transition-all"
                      style="width: {m.stars > 0 ? Math.max(4, Math.round(m.stars / maxS * 100)) : 0}%"
                    ></div>
                  </div>
                  <span class="text-xs text-gray-400 w-4 text-right shrink-0">{m.stars}</span>
                  <span class="text-xs w-9 text-right shrink-0 {m.cycling_km > 0 ? 'text-blue-400' : 'text-gray-700'}">
                    {m.cycling_km > 0 ? m.cycling_km : '—'}
                  </span>
                </div>
              {/each}
            </div>
          {/if}
        {/each}
      </div>
    </div>

    <!-- Gewichtsverlauf -->
    {#if (dashboard.marc?.weight_history?.length || dashboard.pia?.weight_history?.length)}
      <div class="card">
        <h3 class="text-sm font-semibold text-gray-300 mb-3">Gewichtsverlauf</h3>
        <div class="grid grid-cols-2 gap-3">
          {#each [dashboard.marc, dashboard.pia] as person}
            {#if person?.weight_history?.length}
              <div class="space-y-1.5">
                <div class="text-xs text-gray-500 capitalize font-medium mb-1">{person.username}</div>
                {#each [...person.weight_history].reverse().slice(0, 10) as entry}
                  <div class="flex items-center gap-1 text-xs">
                    <span class="text-gray-400 shrink-0">
                      {new Date(entry.measured_at + 'T00:00:00').toLocaleDateString('de-CH', {day:'numeric', month:'short'})}
                    </span>
                    <span class="font-medium flex-1 text-right">{entry.weight_kg}</span>
                    <button
                      on:click={() => deleteWeight(entry.id)}
                      class="text-gray-600 hover:text-red-400 transition-colors px-1 shrink-0">✕</button>
                  </div>
                {/each}
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {/if}

    <!-- New activity -->
    <button on:click={() => goto('/activities/new')} class="btn-primary w-full text-center text-lg py-4">
      + Aktivität erfassen
    </button>
    <button on:click={() => goto('/activities')} class="w-full text-sm text-gray-500 text-center py-1">
      Alle Aktivitäten →
    </button>
  </div>

  <!-- Weight modal -->
  {#if showWeightModal}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="fixed inset-0 bg-black/70 flex items-center justify-center p-6 z-50"
         on:click|self={() => showWeightModal = false}>
      <div class="card w-full max-w-sm space-y-4">
        <h3 class="font-bold text-lg">Gewicht eintragen</h3>
        <div>
          <label class="label">Datum</label>
          <input bind:value={weightDate} type="date" class="input" />
        </div>
        <div>
          <label class="label">Gewicht (kg)</label>
          <input bind:value={newWeight} type="number" step="0.1" min="20" max="300"
                 class="input text-2xl text-center font-bold" placeholder="78.5" />
        </div>
        {#if weightError}<p class="text-red-400 text-sm">{weightError}</p>{/if}
        <div class="flex gap-3">
          <button on:click={() => showWeightModal = false}
            class="flex-1 py-2 rounded-xl border border-gray-600 text-gray-400">Abbrechen</button>
          <button on:click={submitWeight} class="flex-1 btn-primary">Speichern</button>
        </div>
      </div>
    </div>
  {/if}
{/if}
