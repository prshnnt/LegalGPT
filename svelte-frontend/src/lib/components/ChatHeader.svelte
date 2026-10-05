<script lang="ts">
  import { Menu, Settings } from '@lucide/svelte';

  export let threadTitle = 'LegalGPT';
  export let onMenuClick: () => void;
</script>

<header class="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
  <div class="flex items-center justify-between px-4 py-3">
    <div class="flex items-center gap-3">
      <button
        on:click={onMenuClick}
        class="p-1.5 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 md:hidden cursor-pointer"
        aria-label="Open sidebar menu"
      >
        <Menu class="w-5 h-5" />
      </button>

      <h2 class="font-semibold text-lg text-gray-900 dark:text-gray-100">
        {threadTitle}
      </h2>
    </div>

    <div class="flex items-center gap-2">
      <button
        class="p-1.5 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
        aria-label="Settings"
      >
        <Settings class="w-5 h-5" />
      </button>
    </div>
  </div>
</header>
