<script lang="ts">
  import { Loader2, Search, Brain, Check } from '@lucide/svelte';
  import type { ThinkingStage } from '../types/chat';

  export let stages: ThinkingStage[] = [];
  export let isActive = false;

  function getLabel(type: ThinkingStage['type']): string {
    switch (type) {
      case 'thinking':
        return 'Thinking';
      case 'searching':
        return 'Searching the web';
      case 'analyzing':
        return 'Analyzing';
      case 'complete':
        return 'Complete';
      default:
        return 'Processing';
    }
  }
</script>

{#if stages.length > 0 || isActive}
  <div class="flex flex-col gap-2 my-3">
    {#each stages as stage (stage.id)}
      <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
        <div class="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800">
          {#if stage.type === 'thinking'}
            <Brain class="w-4 h-4" />
          {:else if stage.type === 'searching'}
            <Search class="w-4 h-4" />
          {:else if stage.type === 'analyzing'}
            <Loader2 class="w-4 h-4 animate-spin" />
          {:else if stage.type === 'complete'}
            <Check class="w-4 h-4" />
          {:else}
            <Loader2 class="w-4 h-4 animate-spin" />
          {/if}
        </div>
        <span>{getLabel(stage.type)}</span>
        {#if stage.content}
          <span class="text-gray-500 dark:text-gray-500">• {stage.content}</span>
        {/if}
      </div>
    {/each}

    {#if isActive && stages.length === 0}
      <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
        <div class="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800">
          <Loader2 class="w-4 h-4 animate-spin text-amber-600 dark:text-amber-400" />
        </div>
        <span class="animate-pulse">Thinking...</span>
      </div>
    {/if}
  </div>
{/if}
