<script lang="ts">
  import { MessageSquare, Plus, X, Scale, Trash2, LogOut } from '@lucide/svelte';
  import type { ChatThread } from '../types/chat';

  export let threads: ChatThread[] = [];
  export let activeThreadId: string | number | null = null;
  export let onThreadSelect: (id: string | number) => void;
  export let onThreadDelete: ((id: string | number) => void) | undefined = undefined;
  export let onNewChat: () => void;
  export let onLogout: (() => void) | undefined = undefined;
  export let isOpen: boolean = true;
  export let onToggle: () => void;

  let hoveredId: string | number | null = null;

  function formatDate(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / 86_400_000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  }

  function groupThreads(allThreads: ChatThread[]) {
    const groups: Record<string, ChatThread[]> = {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      Older: [],
    };
    for (const t of allThreads) {
      const d = t.timestamp ? formatDate(t.timestamp) : 'Older';
      if (d === 'Today') groups.Today.push(t);
      else if (d === 'Yesterday') groups.Yesterday.push(t);
      else if (d.includes('days ago')) groups['Previous 7 Days'].push(t);
      else groups.Older.push(t);
    }
    return groups;
  }

  $: grouped = groupThreads(threads);
</script>

<!-- Mobile overlay - strictly hidden on desktop via CSS -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
  class="sidebar-overlay {isOpen ? 'open' : ''}"
  on:click={onToggle}
  aria-hidden="true"
></div>

<aside class="sidebar {isOpen ? 'open' : 'closed'}">
  <!-- Header -->
  <div class="sidebar-header">
    <div class="sidebar-brand">
      <div class="sidebar-mark">
        <Scale size={16} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
      </div>
      <span class="sidebar-wordmark">LegalGPT</span>
    </div>
    <button
      on:click={onToggle}
      class="icon-btn"
      style="display: none;"
      id="sidebar-close-btn"
      aria-label="Close sidebar"
    >
      <X size={16} />
    </button>
  </div>

  <!-- New Chat -->
  <button class="sidebar-new-btn" on:click={onNewChat}>
    <Plus size={15} strokeWidth={2.2} />
    <span>New Legal Query</span>
  </button>

  <!-- Thread list -->
  <nav class="sidebar-threads">
    {#each Object.entries(grouped) as [group, items]}
      {#if items.length > 0}
        <div>
          <div class="sidebar-section-label">{group}</div>
          {#each items as thread (thread.id)}
            <!-- svelte-ignore a11y-click-events-have-key-events -->
            <!-- svelte-ignore a11y-no-static-element-interactions -->
            <div
              class="thread-item {activeThreadId === thread.id ? 'active' : ''}"
              on:click={() => onThreadSelect(thread.id)}
              on:mouseenter={() => (hoveredId = thread.id)}
              on:mouseleave={() => (hoveredId = null)}
            >
              <MessageSquare size={14} class="thread-icon" />
              <span class="thread-title">{thread.title}</span>
              {#if onThreadDelete && hoveredId === thread.id}
                <button
                  type="button"
                  class="thread-delete"
                  on:click={(e) => {
                    e.stopPropagation();
                    onThreadDelete?.(thread.id);
                  }}
                  aria-label="Delete thread"
                >
                  <Trash2 size={12} />
                </button>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    {/each}

    {#if threads.length === 0}
      <div style="padding: 32px 8px; text-align: center; color: rgba(255,255,255,0.22); font-size: 13px; line-height: 1.6;">
        No conversations yet.<br />Start a new legal query.
      </div>
    {/if}
  </nav>

  <!-- Footer -->
  <div class="sidebar-footer">
    {#if onLogout}
      <button type="button" class="sidebar-logout-btn" on:click={onLogout}>
        <LogOut size={14} />
        <span>Logout</span>
      </button>
    {/if}
    <div style="margin-top: 10px; font-size: 10px; color: rgba(255,255,255,0.18); text-align: center; letter-spacing: 0.04em;">
      LegalGPT for Law Students
    </div>
  </div>
</aside>

<style>
  @media (max-width: 599px), (max-height: 599px) and (max-width: 1180px) {
    #sidebar-close-btn {
      display: flex !important;
    }
  }
</style>
