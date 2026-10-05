<script lang="ts">
  import { User, Scale, Paperclip } from '@lucide/svelte';
  import { marked } from 'marked';
  import type { Message } from '../types/chat';
  import ThinkingIndicator from './ThinkingIndicator.svelte';

  export let message: Message;

  $: isUser = message.role === 'user' || message.role === 'human';

  $: formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  $: parsedMarkdown = message.content ? marked.parse(message.content) : '';
</script>

<div class={`flex gap-4 p-6 ${isUser ? 'bg-white dark:bg-gray-950' : 'bg-gray-50 dark:bg-gray-900'} rounded-xl transition-colors`}>
  <div class="flex-shrink-0">
    <div
      class={`w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
        isUser
          ? 'bg-blue-600 text-white'
          : 'bg-gradient-to-br from-amber-600 to-orange-600 text-white'
      }`}
    >
      {#if isUser}
        <User class="w-5 h-5" />
      {:else}
        <Scale class="w-5 h-5" />
      {/if}
    </div>
  </div>

  <div class="flex-1 min-w-0">
    <div class="flex items-center gap-2 mb-2">
      <span class="font-semibold text-sm text-gray-900 dark:text-gray-100">
        {isUser ? 'You' : 'LegalGPT'}
      </span>
      {#if formattedTime}
        <span class="text-xs text-gray-500 dark:text-gray-500">
          {formattedTime}
        </span>
      {/if}
    </div>

    <!-- Attachments -->
    {#if message.attachments && message.attachments.length > 0}
      <div class="flex flex-wrap gap-2 mb-3">
        {#each message.attachments as attachment (attachment.id)}
          <div class="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm">
            <Paperclip class="w-4 h-4 text-gray-500" />
            <span class="text-gray-700 dark:text-gray-300 font-medium">{attachment.name}</span>
            <span class="text-gray-500 dark:text-gray-500 text-xs">
              ({(attachment.size / 1024).toFixed(1)} KB)
            </span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Thinking stages -->
    {#if message.thinking && message.thinking.length > 0}
      <ThinkingIndicator stages={message.thinking} />
    {/if}

    <!-- Loading / Streaming indicator -->
    {#if message.isStreaming && !message.content}
      <ThinkingIndicator stages={[]} isActive={true} />
    {/if}

    <!-- Content Markdown -->
    {#if message.content}
      <div class="prose prose-sm dark:prose-invert max-w-none text-gray-800 dark:text-gray-200 leading-relaxed overflow-x-auto">
        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
        {@html parsedMarkdown}
      </div>
    {/if}
  </div>
</div>
