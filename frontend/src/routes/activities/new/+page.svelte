<script>
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  let type = 'endurance';
  let subtype = 'cycling';
  let activity_date = new Date().toISOString().split('T')[0];
  let duration_minutes = 60;
  let notes = '';
  let distance_km = '';
  let exercises = [];
  let loading = false;
  let error = '';

  const enduranceSubtypes = [
    { value: 'cycling', label: '🚴 Velo' },
    { value: 'running', label: '🏃 Laufen' },
    { value: 'hiking', label: '🥾 Wandern' },
    { value: 'swimming', label: '🏊 Schwimmen' },
    { value: 'other', label: '⚡ Anderes' }
  ];

  const strengthSubtypes = [
    { value: 'weightlifting', label: '🏋️ Gewichte' },
    { value: 'calisthenics', label: '💪 Calisthenics' },
    { value: 'yoga', label: '🧘 Yoga' },
    { value: 'other', label: '⚡ Anderes' }
  ];

  $: subtypes = type === 'endurance' ? enduranceSubtypes : strengthSubtypes;
  $: subtype = subtypes[0].value;

  function addExercise() {
    exercises = [...exercises, { name: '', order: exercises.length, sets: [{ set_number: 1, reps: null, weight_kg: null, rest_seconds: null }] }];
  }

  function removeExercise(i) {
    exercises = exercises.filter((_, idx) => idx !== i);
  }

  function addSet(exIdx) {
    const ex = exercises[exIdx];
    ex.sets = [...ex.sets, { set_number: ex.sets.length + 1, reps: null, weight_kg: null, rest_seconds: null }];
    exercises = [...exercises];
  }

  function removeSet(exIdx, setIdx) {
    exercises[exIdx].sets = exercises[exIdx].sets.filter((_, i) => i !== setIdx);
    exercises = [...exercises];
  }

  async function submit() {
    loading = true;
    error = '';
    try {
      const payload = {
        type,
        subtype,
        activity_date,
        duration_minutes: parseInt(duration_minutes),
        notes: notes || null,
        distance_km: type === 'endurance' && distance_km ? parseFloat(distance_km) : null,
        exercises: type === 'strength' ? exercises : []
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
    <button on:click={() => goto('/')} class="text-gray-400">‹</button>
    <h2 class="text-lg font-bold">Aktivität erfassen</h2>
  </div>

  <form on:submit|preventDefault={submit} class="space-y-4">
    <!-- Typ -->
    <div class="card">
      <label class="label">Typ</label>
      <div class="grid grid-cols-2 gap-2">
        {#each [['endurance', '🚴 Ausdauer'], ['strength', '🏋️ Kraft']] as [val, lbl]}
          <button
            type="button"
            on:click={() => type = val}
            class="py-3 rounded-xl font-medium transition-colors"
            class:bg-primary={type === val}
            class:bg-bg={type !== val}
            class:text-white={type === val}
            class:text-gray-400={type !== val}
          >{lbl}</button>
        {/each}
      </div>
    </div>

    <!-- Subtyp -->
    <div>
      <label class="label">Aktivität</label>
      <select bind:value={subtype} class="input">
        {#each subtypes as s}
          <option value={s.value}>{s.label}</option>
        {/each}
      </select>
    </div>

    <!-- Datum + Dauer -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="label">Datum</label>
        <input bind:value={activity_date} type="date" class="input" required />
      </div>
      <div>
        <label class="label">Dauer (Min.)</label>
        <input bind:value={duration_minutes} type="number" min="1" class="input" required />
      </div>
    </div>

    <!-- Distanz (Ausdauer) -->
    {#if type === 'endurance'}
      <div>
        <label class="label">Distanz (km)</label>
        <input bind:value={distance_km} type="number" step="0.1" min="0" class="input" placeholder="z.B. 32.5" />
      </div>
    {/if}

    <!-- Übungen (Kraft) -->
    {#if type === 'strength'}
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <label class="label mb-0">Übungen</label>
          <button type="button" on:click={addExercise} class="text-primary text-sm font-medium">+ Übung</button>
        </div>

        {#each exercises as ex, exIdx}
          <div class="card space-y-3">
            <div class="flex gap-2">
              <input bind:value={ex.name} class="input flex-1" placeholder="Übungsname (z.B. Bankdrücken)" required />
              <button type="button" on:click={() => removeExercise(exIdx)} class="text-red-400 px-2">✕</button>
            </div>

            <div class="space-y-2">
              {#each ex.sets as set, setIdx}
                <div class="grid grid-cols-4 gap-2 items-center">
                  <span class="text-gray-400 text-sm text-center">S{setIdx + 1}</span>
                  <input bind:value={set.reps} type="number" min="0" class="input text-center px-2" placeholder="Wdh." />
                  <input bind:value={set.weight_kg} type="number" step="0.5" min="0" class="input text-center px-2" placeholder="kg" />
                  <button type="button" on:click={() => removeSet(exIdx, setIdx)} class="text-red-400 text-sm">✕</button>
                </div>
              {/each}
              <button type="button" on:click={() => addSet(exIdx)} class="text-primary text-sm w-full text-center py-1">
                + Satz
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Notizen -->
    <div>
      <label class="label">Notizen (optional)</label>
      <textarea bind:value={notes} class="input" rows="3" placeholder="Wie war's?"></textarea>
    </div>

    {#if error}
      <p class="text-red-400 text-sm">{error}</p>
    {/if}

    <button type="submit" class="btn-primary w-full" disabled={loading}>
      {loading ? 'Speichern...' : 'Aktivität speichern'}
    </button>
  </form>
</div>
