<script lang="ts">
  import { Scale } from '@lucide/svelte';
  import { login, register, TokenManager } from '../services/api';

  export let isOpen: boolean = false;
  export let onSuccess: () => void;

  let mode: 'login' | 'register' = 'login';
  let username = '';
  let password = '';
  let error = '';
  let isLoading = false;

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = '';
    isLoading = true;
    try {
      if (mode === 'login') {
        const res = await login({ username, password });
        TokenManager.setToken(res.access_token);
        onSuccess();
      } else {
        await register({ username, password });
        const res = await login({ username, password });
        TokenManager.setToken(res.access_token);
        onSuccess();
      }
    } catch (err: any) {
      error = err.message || 'Authentication failed';
    } finally {
      isLoading = false;
    }
  }

  function toggleMode() {
    mode = mode === 'login' ? 'register' : 'login';
    error = '';
  }
</script>

{#if isOpen}
  <div class="auth-overlay">
    <div class="auth-card">
      <!-- Logo -->
      <div class="auth-logo-wrap">
        <div class="auth-logo">
          <Scale size={28} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
        </div>
      </div>

      <h2 class="auth-title">
        {mode === 'login' ? 'Welcome to LegalGPT' : 'Create Account'}
      </h2>
      <p class="auth-sub">
        {mode === 'login'
          ? 'Sign in to your legal research assistant'
          : 'Start your legal research journey'}
      </p>

      <form on:submit={handleSubmit} class="auth-form">
        <div class="form-field">
          <label class="form-label" for="auth-username">USERNAME</label>
          <input
            id="auth-username"
            type="text"
            class="form-input"
            placeholder="Enter your username"
            bind:value={username}
            required
            disabled={isLoading}
            autocomplete="username"
          />
        </div>

        <div class="form-field">
          <label class="form-label" for="auth-password">PASSWORD</label>
          <input
            id="auth-password"
            type="password"
            class="form-input"
            placeholder="Enter your password"
            bind:value={password}
            required
            disabled={isLoading}
            autocomplete="current-password"
          />
        </div>

        {#if error}
          <div class="auth-error">{error}</div>
        {/if}

        <button
          type="submit"
          class="auth-submit-btn"
          disabled={isLoading || !username || !password}
        >
          {isLoading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Register'}
        </button>
      </form>

      <div class="auth-switch">
        <button
          type="button"
          class="auth-switch-btn"
          on:click={toggleMode}
          disabled={isLoading}
        >
          {mode === 'login'
            ? "Don't have an account? Register"
            : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  </div>
{/if}
