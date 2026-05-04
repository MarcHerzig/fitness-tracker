<script>
  import { goto } from '$app/navigation';
  import { token, user } from '$lib/stores';
  import { api } from '$lib/api';

  let username = '';
  let email = '';
  let password = '';
  let error = '';
  let loading = false;
  let mode = 'login';

  async function login() {
    loading = true;
    error = '';
    try {
      const res = await api.login(username, password);
      token.set(res.access_token);
      user.set(await api.me());
      goto('/');
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function register() {
    loading = true;
    error = '';
    try {
      await api.register(username, email, password);
      const res = await api.login(username, password);
      token.set(res.access_token);
      user.set(await api.me());
      goto('/');
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center p-6">
  <div class="w-full max-w-sm">
    <div class="text-center mb-8">
      <div class="text-6xl mb-3">🏃</div>
      <h1 class="text-2xl font-bold">Fitness Tracker</h1>
      <p class="text-gray-400 mt-1">{mode === 'login' ? 'Meld dich an' : 'Konto erstellen'}</p>
    </div>

    {#if mode === 'login'}
      <form on:submit|preventDefault={login} class="space-y-4">
        <div>
          <label class="label">Benutzername</label>
          <input bind:value={username} class="input" type="text" autocomplete="username" required />
        </div>
        <div>
          <label class="label">Passwort</label>
          <input bind:value={password} class="input" type="password" autocomplete="current-password" required />
        </div>

        {#if error}
          <p class="text-red-400 text-sm text-center">{error}</p>
        {/if}

        <button type="submit" class="btn-primary w-full" disabled={loading}>
          {loading ? 'Laden...' : 'Anmelden'}
        </button>
        <p class="text-center text-sm text-gray-400">
          Noch kein Konto?
          <button type="button" class="text-blue-400 hover:underline" on:click={() => { mode = 'register'; error = ''; }}>
            Registrieren
          </button>
        </p>
      </form>
    {:else}
      <form on:submit|preventDefault={register} class="space-y-4">
        <div>
          <label class="label">Benutzername</label>
          <input bind:value={username} class="input" type="text" autocomplete="username" required />
        </div>
        <div>
          <label class="label">E-Mail</label>
          <input bind:value={email} class="input" type="email" autocomplete="email" required />
        </div>
        <div>
          <label class="label">Passwort</label>
          <input bind:value={password} class="input" type="password" autocomplete="new-password" required />
        </div>

        {#if error}
          <p class="text-red-400 text-sm text-center">{error}</p>
        {/if}

        <button type="submit" class="btn-primary w-full" disabled={loading}>
          {loading ? 'Laden...' : 'Registrieren'}
        </button>
        <p class="text-center text-sm text-gray-400">
          Bereits ein Konto?
          <button type="button" class="text-blue-400 hover:underline" on:click={() => { mode = 'login'; error = ''; }}>
            Anmelden
          </button>
        </p>
      </form>
    {/if}
  </div>
</div>
