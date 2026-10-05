<script lang="ts">
  import { Scale } from '@lucide/svelte';
  import { login, register, TokenManager } from '../services/api';

  export let isOpen = false;
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
        const response = await login({ username, password });
        TokenManager.setToken(response.access_token);
        onSuccess();
      } else {
        await register({ username, password });
        const response = await login({ username, password });
        TokenManager.setToken(response.access_token);
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
  <div class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl p-6 sm:p-8 animate-in fade-in zoom-in-95 duration-200">
      <!-- Logo Header -->
      <div class="flex flex-col items-center justify-center text-center mb-6">
        <div class="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20 mb-4">
          <Scale class="w-9 h-9 text-white" />
        </div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
          {mode === 'login' ? 'Welcome to LegalGPT' : 'Create Account'}
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {mode === 'login'
            ? 'Sign in to access your legal research assistant'
            : 'Register to start your legal research journey'}
        </p>
      </div>

      <!-- Auth Form -->
      <form on:submit={handleSubmit} class="space-y-4">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Username
          </label>
          <input
            id="username"
            type="text"
            placeholder="Enter your username"
            bind:value={username}
            required
            disabled={isLoading}
            class="w-full px-3.5 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Password
          </label>
          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            bind:value={password}
            required
            disabled={isLoading}
            class="w-full px-3.5 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        {#if error}
          <div class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 p-3 rounded-lg">
            {error}
          </div>
        {/if}

        <button
          type="submit"
          disabled={isLoading}
          class="w-full py-3 px-4 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-medium rounded-lg shadow-md shadow-amber-500/20 disabled:opacity-50 transition-all cursor-pointer"
        >
          {isLoading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Register'}
        </button>

        <div class="text-center text-sm pt-2">
          <button
            type="button"
            on:click={toggleMode}
            disabled={isLoading}
            class="text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-medium hover:underline cursor-pointer"
          >
            {mode === 'login'
              ? "Don't have an account? Register"
              : 'Already have an account? Sign in'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
