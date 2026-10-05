<script lang="ts">
  import { Menu, Sun, Moon } from '@lucide/svelte';

  export let threadTitle = 'LegalGPT';
  export let onMenuClick: () => void;
  export let isDarkMode: boolean = true;
  export let onToggleTheme: (() => void) | undefined = undefined;
</script>

<header class="chat-header">
  <div class="chat-header-left">
    <button
      class="icon-btn"
      on:click={onMenuClick}
      aria-label="Open sidebar"
      style="flex-shrink: 0;"
    >
      <Menu size={18} />
    </button>
    <span class="chat-header-title">{threadTitle}</span>
  </div>

  <div class="chat-header-right">
    {#if onToggleTheme}
      <button
        class="icon-btn"
        on:click={onToggleTheme}
        aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {#if isDarkMode}
          <Sun size={16} />
        {:else}
          <Moon size={16} />
        {/if}
      </button>
    {/if}
  </div>
</header>
