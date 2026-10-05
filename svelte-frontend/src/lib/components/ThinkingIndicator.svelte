<script lang="ts">
  import { Loader2, Search, Brain, Check } from '@lucide/svelte';
  import type { ThinkingStage } from '../types/chat';

  export let stages: ThinkingStage[] = [];
  export let isActive: boolean = false;

  const LABELS: Record<ThinkingStage['type'], string> = {
    thinking: 'Thinking',
    searching: 'Searching the web',
    analyzing: 'Analyzing',
    complete: 'Complete',
  };
</script>

{#if stages.length > 0 || isActive}
  <div class="thinking-wrap">
    {#each stages as stage (stage.id)}
      <div class="thinking-row">
        <div class="thinking-icon-wrap">
          {#if stage.type === 'thinking'}
            <Brain size={12} />
          {:else if stage.type === 'searching'}
            <Search size={12} />
          {:else if stage.type === 'analyzing'}
            <span class="animate-spin flex items-center justify-center">
              <Loader2 size={12} />
            </span>
          {:else if stage.type === 'complete'}
            <Check size={12} />
          {:else}
            <Loader2 size={12} />
          {/if}
        </div>
        <span>{LABELS[stage.type] ?? 'Processing'}</span>
        {#if stage.content}
          <span style="color: rgba(255,255,255,0.30);">• {stage.content}</span>
        {/if}
      </div>
    {/each}

    {#if isActive && stages.length === 0}
      <div class="thinking-row">
        <div class="thinking-icon-wrap">
          <div class="thinking-pulse">
            <span></span><span></span><span></span>
          </div>
        </div>
        <span>Thinking…</span>
      </div>
    {/if}
  </div>
{/if}
