<script lang="ts">
  import { User, Scale, Paperclip } from '@lucide/svelte';
  import { marked } from 'marked';
  import ThinkingIndicator from './ThinkingIndicator.svelte';
  import type { Message } from '../types/chat';

  export let message: Message;

  $: isUser = message.role === 'user' || message.role === 'human';

  $: time = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  $: parsedMarkdown = message.content ? marked.parse(message.content) : '';
</script>

<div class={`message-row${isUser ? ' user-row' : ''}`}>
  <!-- Avatar -->
  <div class={`avatar ${isUser ? 'avatar-user' : 'avatar-ai'}`}>
    {#if isUser}
      <User size={15} color="rgba(255,255,255,0.92)" />
    {:else}
      <Scale size={15} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
    {/if}
  </div>

  <!-- Content -->
  <div class="message-content-wrap">
    <div class="message-meta">
      <span class="message-sender">{isUser ? 'You' : 'LegalGPT'}</span>
      {#if time}
        <span class="message-time">{time}</span>
      {/if}
    </div>

    <!-- Attachments -->
    {#if message.attachments && message.attachments.length > 0}
      <div class="attachments-row">
        {#each message.attachments as a (a.id)}
          <div class="attachment-chip">
            <Paperclip size={11} />
            <span>{a.name}</span>
            <span style="opacity: 0.55; font-size: 10px;">
              {(a.size / 1024).toFixed(1)} KB
            </span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Thinking stages -->
    {#if message.thinking && message.thinking.length > 0}
      <ThinkingIndicator stages={message.thinking} />
    {/if}

    <!-- Message bubble -->
    {#if message.content || message.isStreaming}
      <div class={`message-bubble ${isUser ? 'bubble-user' : 'bubble-ai'}`}>
        {#if message.content}
          <div class="prose">
            <!-- eslint-disable-next-line svelte/no-at-html-tags -->
            {@html parsedMarkdown}
          </div>
        {:else}
          <ThinkingIndicator stages={[]} isActive={true} />
        {/if}
      </div>
    {/if}
  </div>
</div>
