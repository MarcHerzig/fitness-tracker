<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  let type = 'endurance';
  let subtype = 'cycling';
  let activity_date = new Date().toISOString().split('T')[0];
  let distance_km = '';
  let notes = '';
  let loading = false;
  let error = '';

  // Strength
  let templates = [];
  // sets[templateId] = 0|1|2|3
  let sets = {};

  const enduranceSubtypes = [
    { value: 'cycling', label: '🚴 Velo' },
    { value: 'running', label: '🏃 Laufen' },
    { value: 'hiking', label: '🥾 Wandern' },
    { value: 'swimming', label: '🏊 Schwimmen' },
  ];

  onMount(async () => {
    try {
      templates = await api.getExercises();
      sets = Object.fromEntries(templates.map(t => [t.id, 0]));
    } catch (e) {}
  });

  $: subtypeOpts = enduranceSubtypes;
  $: if (type === 'endurance') subtype = 'cycling';

  function toggleSet(templateId, setIndex) {
    // setIndex = 1,2,3 — clicking toggles up to that number or resets
    const current = sets[templateId];
    sets[templateId] = current === setIndex ? setIndex - 1 : setIndex;
    sets = { ...sets };
  }

  $: totalSets = Object.values(sets).reduce((a, b) => a + b, 0);
  $: strengthStars = totalSets >= 18 ? 3 : totalSets >= 10 ? 2 : totalSets >= 3 ? 1 : 0;
  $: enduranceStars = distance_km >= 30 ? 3 : distance_km >= 20 ? 2 : distance_km >= 10 ? 1 : 0;
  $: previewStars = type === 'endurance' ? enduranceStars : strengthStars;

  async function submit() {
    loading = true;
    error = '';
    try {
      const payload = {
        type,
        subtype: type === 'strength' ? 'strength' : subtype,
        activity_date,
        distance_km: type === 'endurance' ? parseFloat(distance_km) : null,
        notes: notes || null,
        exercises: type === 'strength'
          ? templates.filter(t => sets[t.id] > 0).map(t => ({ template_id: t.id, sets_completed: sets[t.id] }))
          : [],
      };
      await api.createActivity(payload);
      goto('/');
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="space-y-4">
  <div class="flex items-center gap-3 mb-2">
    <button on:click={() => goto('/')} class="text-gray-400 text-xl">‹</button>
    <h2 class="text-lg font-bold">Aktivität erfassen</h2>
  </div>

  <form on:submit|preventDefault={submit} class="space-y-4">

    <!-- Typ -->
    <div class="grid grid-cols-2 gap-2">
      {#each [['endurance', '🚴 Ausdauer'], ['strength', '🏋️ Kraft']] as [val, lbl]}
        <button type="button" on:click={() => type = val}
          class="py-3 rounded-xl font-medium transition-colors"
          class:bg-primary={type === val}
          class:text-white={type === val}
          class:bg-gray-800={type !== val}
          class:text-gray-400={type !== val}>
          {lbl}
        </button>
      {/each}
    </div>

    <!-- Datum -->
    <div>
      <label class="label">Datum</label>
      <input bind:value={activity_date} type="date" class="input" required />
    </div>

    <!-- Ausdauer -->
    {#if type === 'endurance'}
      <div>
        <label class="label">Aktivität</label>
        <select bind:value={subtype} class="input">
          {#each enduranceSubtypes as s}
            <option value={s.value}>{s.label}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="label">Kilometer</label>
        <input bind:value={distance_km} type="number" step="0.1" min="0" class="input text-2xl text-center font-bold" placeholder="0.0" required />
      </div>
    {/if}

    <!-- Kraft: Checkboxen -->
    {#if type === 'strength'}
      <div class="space-y-2">
        {#each templates as t}
          <div class="card flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{t.name}</div>
              {#if t.weight_kg}
                <div class="text-xs text-gray-400">{t.weight_kg} kg</div>
              {:else if t.is_duration_based}
                <div class="text-xs text-gray-400">10 min / Satz</div>
              {:else}
                <div class="text-xs text-gray-400">Körpergewicht</div>
              {/if}
            </div>
            <div class="flex gap-2">
              {#each [1, 2, 3] as s}
                <button
                  type="button"
                  on:click={() => toggleSet(t.id, s)}
                  class="w-8 h-8 rounded-full border-2 transition-colors font-bold text-sm
                    {sets[t.id] >= s
                      ? 'border-primary bg-primary text-white'
                      : 'border-gray-600 text-gray-600'}"
                >
                  {s}
                </button>
              {/each}
            </div>
          </div>
        {/each}

        <button type="button" on:click={() => goto('/exercises')} class="w-full text-sm text-gray-500 py-2 text-center">
          + Übungen verwalten
        </button>
      </div>
    {/if}

    <!-- Sterne-Preview -->
    {#if previewStars > 0 || (type === 'endurance' && distance_km) || (type === 'strength' && totalSets > 0)}
      <div class="card text-center">
        <div class="text-3xl mb-1">
          {'★'.repeat(previewStars)}{'☆'.repeat(3 - previewStars)}
        </div>
        <div class="text-xs text-gray-400">
          {#if type === 'endurance'}
            {distance_km || 0} km
          {:else}
            {totalSets} Ausführungen
          {/if}
        </div>
      </div>
    {/if}

    <!-- Notizen -->
    <div>
      <label class="label">Notizen (optional)</label>
      <textarea bind:value={notes} class="input" rows="2" placeholder="Wie war's?"></textarea>
    </div>

    {#if error}
      <p class="text-red-400 text-sm">{error}</p>
    {/if}

    <button type="submit" class="btn-primary w-full py-4 text-lg" disabled={loading}>
      {loading ? 'Speichern...' : 'Speichern'}
    </button>
  </form>
</div>
