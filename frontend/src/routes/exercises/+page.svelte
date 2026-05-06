<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  let exercises = [];
  let loading = true;
  let showAdd = false;
  let newName = '';
  let newWeight = '';
  let newDuration = false;
  let editId = null;
  let editWeight = '';
  let error = '';

  onMount(async () => {
    exercises = await api.getExercises();
    loading = false;
  });

  async function addExercise() {
    error = '';
    if (!newName.trim()) return;
    try {
      await api.createExercise({
        name: newName.trim(),
        weight_kg: newWeight ? parseFloat(newWeight) : null,
        is_duration_based: newDuration,
        sort_order: exercises.length,
      });
      exercises = await api.getExercises();
      newName = ''; newWeight = ''; newDuration = false; showAdd = false;
    } catch (e) { error = e.message; }
  }

  async function saveWeight(id) {
    const kg = parseFloat(editWeight);
    await api.updateExercise(id, { weight_kg: isNaN(kg) ? null : kg });
    exercises = await api.getExercises();
    editId = null;
  }

  async function remove(id) {
    await api.deleteExercise(id);
    exercises = exercises.filter(e => e.id !== id);
  }

  async function move(index, dir) {
    const target = index + dir;
    if (target < 0 || target >= exercises.length) return;
    const arr = [...exercises];
    [arr[index], arr[target]] = [arr[target], arr[index]];
    exercises = arr;
    await api.reorderExercises(arr.map(e => e.id));
  }
</script>

<div class="space-y-4">
  <div class="flex items-center gap-3">
    <button on:click={() => goto('/activities/new')} class="text-gray-400 text-xl">‹</button>
    <h2 class="text-lg font-bold">Meine Übungen</h2>
  </div>

  {#if loading}
    <div class="text-center text-gray-500 py-8">Laden...</div>
  {:else}
    <div class="space-y-2">
      {#each exercises as ex, i}
        <div class="card">
          <div class="flex items-center gap-2">
            <!-- Sort buttons -->
            <div class="flex flex-col gap-0.5">
              <button on:click={() => move(i, -1)}
                class="text-gray-600 hover:text-gray-300 text-xs leading-none px-1 disabled:opacity-20"
                disabled={i === 0}>▲</button>
              <button on:click={() => move(i, 1)}
                class="text-gray-600 hover:text-gray-300 text-xs leading-none px-1 disabled:opacity-20"
                disabled={i === exercises.length - 1}>▼</button>
            </div>

            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{ex.name}</div>
              <div class="text-xs text-gray-400">
                {ex.is_duration_based ? '10 min / Satz' : ex.weight_kg ? `${ex.weight_kg} kg` : 'Körpergewicht'}
              </div>
            </div>

            {#if !ex.is_duration_based}
              {#if editId === ex.id}
                <input
                  bind:value={editWeight}
                  type="number" step="0.5" min="0"
                  class="input w-20 text-center px-2 py-1"
                  placeholder="kg"
                />
                <button on:click={() => saveWeight(ex.id)} class="text-primary font-medium text-sm">✓</button>
                <button on:click={() => editId = null} class="text-gray-500 text-sm">✕</button>
              {:else}
                <button on:click={() => { editId = ex.id; editWeight = ex.weight_kg?.toString() || ''; }}
                  class="text-xs text-gray-400 border border-gray-600 px-2 py-1 rounded-lg">
                  {ex.weight_kg ? `${ex.weight_kg} kg` : 'Gewicht'}
                </button>
              {/if}
            {/if}

            <button on:click={() => remove(ex.id)} class="text-red-400 text-sm px-1">✕</button>
          </div>
        </div>
      {/each}
    </div>

    {#if showAdd}
      <div class="card space-y-3">
        <input bind:value={newName} class="input" placeholder="Übungsname" />
        <div class="flex items-center gap-3">
          <input bind:value={newWeight} type="number" step="0.5" min="0" class="input flex-1" placeholder="Gewicht (kg, optional)" />
        </div>
        <label class="flex items-center gap-2 text-sm text-gray-400">
          <input type="checkbox" bind:checked={newDuration} />
          Zeitbasiert (10 min / Satz, z.B. Laufen)
        </label>
        {#if error}<p class="text-red-400 text-sm">{error}</p>{/if}
        <div class="flex gap-2">
          <button on:click={() => showAdd = false} class="flex-1 py-2 rounded-xl border border-gray-600 text-gray-400">Abbrechen</button>
          <button on:click={addExercise} class="flex-1 btn-primary">Hinzufügen</button>
        </div>
      </div>
    {:else}
      <button on:click={() => showAdd = true} class="w-full py-3 rounded-xl border border-dashed border-gray-600 text-gray-400 text-sm">
        + Neue Übung
      </button>
    {/if}
  {/if}
</div>
