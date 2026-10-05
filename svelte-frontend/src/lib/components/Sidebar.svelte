<script lang="ts">
  import { MessageSquare, Plus, X, Scale, Trash2, LogOut } from '@lucide/svelte';
  import type { ChatThread } from '../types/chat';

  export let threads: ChatThread[] = [];
  export let activeThreadId: string | number | null = null;
  export let isOpen = false;
  export let onThreadSelect: (threadId: string | number) => void;
  export let onThreadDelete: (threadId: string | number) => void;
  export let onNewChat: () => void;
  export let onLogout: () => void;
  export let onToggle: () => void;

  let hoveredThreadId: string | number | null = null;

  function formatDate(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  }

  function groupThreadsByDate(allThreads: ChatThread[]) {
    const groups: { [key: string]: ChatThread[] } = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Older': []
    };

    allThreads.forEach(thread => {
      const date = thread.timestamp ? formatDate(thread.timestamp) : 'Older';
      if (date === 'Today') groups['Today'].push(thread);
      else if (date === 'Yesterday') groups['Yesterday'].push(thread);
      else if (date.includes('days ago')) groups['Previous 7 Days'].push(thread);
      else groups['Older'].push(thread);
    });

    return groups;
  }

  $: groupedThreads = groupThreadsByDate(threads);

  function handleDelete(e: MouseEvent, threadId: string | number) {
    e.stopPropagation();
    onThreadDelete(threadId);
  }
</script>

<!-- Mobile Overlay -->
{#if isOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="fixed inset-0 bg-black/50 z-40 md:hidden"
    on:click={onToggle}
  ></div>
{/if}

<!-- Sidebar Drawer -->
<aside
  class={`fixed inset-y-0 left-0 z-50 w-72 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-transform duration-200 ${
    isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
  }`}
>
  <!-- Header -->
  <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
    <div class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 flex items-center justify-center shadow-md">
        <Scale class="w-5 h-5 text-white" />
      </div>
      <h1 class="font-semibold text-lg text-gray-900 dark:text-white">LegalGPT</h1>
    </div>
    <button
      on:click={onToggle}
      class="p-1 rounded-md text-gray-500 hover:text-gray-900 dark:hover:text-white md:hidden cursor-pointer"
    >
      <X class="w-5 h-5" />
    </button>
  </div>

  <!-- New Chat Button -->
  <div class="p-3">
    <button
      on:click={onNewChat}
      class="w-full flex items-center justify-start gap-2 px-4 py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white font-medium rounded-lg shadow cursor-pointer transition-all"
    >
      <Plus class="w-4 h-4" />
      New Legal Query
    </button>
  </div>

  <!-- Chat Threads List -->
  <div class="flex-1 overflow-y-auto px-3">
    <div class="space-y-6 py-2">
      {#each Object.entries(groupedThreads) as [group, groupThreads]}
        {#if groupThreads.length > 0}
          <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 px-2">
              {group}
            </h3>
            <div class="space-y-1">
              {#each groupThreads as thread (thread.id)}
                <!-- svelte-ignore a11y-no-static-element-interactions -->
                <div
                  class="relative group"
                  on:mouseenter={() => (hoveredThreadId = thread.id)}
                  on:mouseleave={() => (hoveredThreadId = null)}
                >
                  <button
                    on:click={() => onThreadSelect(thread.id)}
                    class={`w-full text-left px-3 py-2.5 rounded-lg transition-colors cursor-pointer ${
                      activeThreadId === thread.id
                        ? 'bg-gray-100 dark:bg-gray-800'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-900'
                    }`}
                  >
                    <div class="flex items-start gap-2">
                      <MessageSquare class="w-4 h-4 mt-0.5 text-gray-500 flex-shrink-0" />
                      <div class="flex-1 min-w-0 pr-6">
                        <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {thread.title}
                        </p>
                        {#if thread.preview}
                          <p class="text-xs text-gray-500 dark:text-gray-500 truncate mt-0.5">
                            {thread.preview}
                          </p>
                        {/if}
                      </div>
                    </div>
                  </button>
                  {#if hoveredThreadId === thread.id}
                    <button
                      on:click={(e) => handleDelete(e, thread.id)}
                      class="absolute right-2 top-2 p-1.5 rounded-md bg-white dark:bg-gray-800 hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 transition-colors cursor-pointer"
                      title="Delete thread"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                    </button>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
    </div>
  </div>

  <!-- Footer -->
  <div class="border-t border-gray-200 dark:border-gray-800">
    <div class="p-3">
      <button
        on:click={onLogout}
        class="w-full flex items-center justify-start gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors cursor-pointer"
      >
        <LogOut class="w-4 h-4" />
        Logout
      </button>
    </div>
    <div class="px-4 pb-4">
      <p class="text-xs text-gray-500 dark:text-gray-500 text-center">
        LegalGPT for Law Students
      </p>
    </div>
  </div>
</aside>
