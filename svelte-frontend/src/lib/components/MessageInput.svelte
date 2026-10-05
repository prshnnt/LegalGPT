<script lang="ts">
  import { Paperclip, Globe, ChevronDown, X } from '@lucide/svelte';
  import type { Attachment } from '../types/chat';
  import { uploadFile } from '../services/api';

  export let onSend: (message: string, attachments: Attachment[]) => void;
  export let isLoading: boolean = false;
  export let webSearchEnabled: boolean = false;
  export let onWebSearchToggle: () => void;
  export let sidebarWidth: number = 280;

  let message = '';
  let attachments: Attachment[] = [];
  let isUploading = false;
  let fileRef: HTMLInputElement;
  let textareaRef: HTMLTextAreaElement;

  function handleSend() {
    if ((!message.trim() && !attachments.length) || isLoading) return;
    onSend(message, attachments);
    message = '';
    attachments = [];
    if (textareaRef) {
      textareaRef.style.height = 'auto';
    }
  }

  function handleKey(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleResize(e: Event) {
    const el = e.target as HTMLTextAreaElement;
    message = el.value;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
  }

  async function handleFiles(e: Event) {
    const target = e.target as HTMLInputElement;
    const files = Array.from(target.files ?? []);
    if (!files.length) return;
    isUploading = true;
    try {
      const uploaded = await Promise.all(files.map((f) => uploadFile(f)));
      attachments = [...attachments, ...uploaded];
    } catch (err) {
      console.error('Upload error', err);
    } finally {
      isUploading = false;
      target.value = '';
    }
  }

  function removeAttachment(id: string) {
    attachments = attachments.filter((x) => x.id !== id);
  }

  $: canSend = (Boolean(message.trim()) || attachments.length > 0) && !isLoading;
</script>

<div
  class="composer-wrap"
  style="left: {sidebarWidth}px;"
>
  <form class="card" on:submit|preventDefault={handleSend}>
    <!-- Attachment preview -->
    {#if attachments.length > 0}
      <div class="attach-preview">
        {#each attachments as a (a.id)}
          <div class="attachment-chip" style="cursor: default;">
            <Paperclip size={11} />
            <span>{a.name}</span>
            <button
              type="button"
              on:click={() => removeAttachment(a.id)}
              style="margin-left: 4px; color: rgba(255,255,255,0.40); cursor: pointer; background: none; border: none; padding: 0; display: flex;"
              aria-label="Remove attachment"
            >
              <X size={10} />
            </button>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Textarea -->
    <textarea
      bind:this={textareaRef}
      class="card-textarea"
      value={message}
      on:input={handleResize}
      on:keydown={handleKey}
      placeholder="Ask about Constitution of India, BNS, BNSS, case laws…"
      rows={1}
      disabled={isLoading}
      aria-label="Chat message"
    ></textarea>

    <!-- Toolbar strip -->
    <div class="tools">
      <!-- Left: chips -->
      <div class="chips">
        <!-- Web search chip -->
        <button
          type="button"
          class={`chip${webSearchEnabled ? ' active' : ''}`}
          on:click={onWebSearchToggle}
          disabled={isLoading}
          style="--cw: 107; --pl: 12; --ig: 3.7;"
        >
          <Globe size={13} class="chip-icon" />
          <span class="chip-label">Web Search</span>
        </button>

        <!-- Attach file chip -->
        <button
          type="button"
          class="chip"
          on:click={() => fileRef?.click()}
          disabled={isLoading || isUploading}
          style="--cw: 108; --pl: 16; --ig: 3.9;"
        >
          <Paperclip size={12} class="chip-icon" />
          <span class="chip-label">
            {isUploading ? 'Uploading…' : 'Attach File'}
          </span>
        </button>
      </div>

      <!-- Right cluster -->
      <div class="right">
        <!-- Model selector -->
        <button
          type="button"
          class="model-sel"
          tabindex={-1}
          aria-label="Model: LegalGPT"
        >
          <span>LegalGPT</span>
          <ChevronDown
            size={11}
            class="model-chevron"
            style="opacity: 0.55;"
          />
        </button>

        <!-- Attach button -->
        <button
          type="button"
          class="attach-btn"
          on:click={() => fileRef?.click()}
          disabled={isLoading || isUploading}
          aria-label="Attach document"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66L9.41 16.41A2 2 0 016.59 13.6l8.49-8.49" />
          </svg>
        </button>

        <!-- Send circle -->
        <button
          type="submit"
          class="send-btn"
          disabled={!canSend}
          aria-label="Send message"
        >
          <svg
            class="send-icon"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 19V5M5 12l7-7 7 7"
              stroke="rgba(30,15,5,0.90)"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Web search note -->
    {#if webSearchEnabled}
      <div class="search-badge">
        <Globe size={11} />
        Web search enabled
      </div>
    {/if}

    <!-- Hidden file input -->
    <input
      bind:this={fileRef}
      type="file"
      multiple
      class="file-input-hidden"
      on:change={handleFiles}
      accept="image/*,.pdf,.doc,.docx,.txt"
    />
  </form>
</div>
