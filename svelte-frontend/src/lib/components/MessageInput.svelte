<script lang="ts">
  import { Send, Paperclip, X, Globe } from '@lucide/svelte';
  import type { Attachment } from '../types/chat';
  import { uploadFile } from '../services/api';

  export let onSend: (message: string, attachments: Attachment[]) => void;
  export let isLoading = false;
  export let webSearchEnabled = false;
  export let onWebSearchToggle: () => void;

  let message = '';
  let attachments: Attachment[] = [];
  let isUploading = false;
  let fileInputRef: HTMLInputElement;

  function handleSend() {
    if (!message.trim() && attachments.length === 0) return;
    if (isLoading) return;

    onSend(message, attachments);
    message = '';
    attachments = [];
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  async function handleFileSelect(e: Event) {
    const target = e.target as HTMLInputElement;
    const files = Array.from(target.files || []);
    if (files.length === 0) return;

    isUploading = true;
    try {
      const uploadedFiles = await Promise.all(
        files.map(file => uploadFile(file))
      );
      attachments = [...attachments, ...uploadedFiles];
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      isUploading = false;
    }
  }

  function removeAttachment(id: string) {
    attachments = attachments.filter(att => att.id !== id);
  }
</script>

<div class="fixed bottom-0 left-0 w-full border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 z-30">
  <div class="max-w-4xl mx-auto p-4">
    <!-- Attachments Display -->
    {#if attachments.length > 0}
      <div class="flex flex-wrap gap-2 mb-3 px-2">
        {#each attachments as attachment (attachment.id)}
          <div class="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm">
            <Paperclip class="w-4 h-4 text-gray-500" />
            <span class="text-gray-700 dark:text-gray-300 font-medium">{attachment.name}</span>
            <button
              on:click={() => removeAttachment(attachment.id)}
              class="ml-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 cursor-pointer"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Input Bar -->
    <div class="relative flex items-end gap-2">
      <input
        bind:this={fileInputRef}
        type="file"
        multiple
        class="hidden"
        on:change={handleFileSelect}
        accept="image/*,.pdf,.doc,.docx,.txt"
      />

      <button
        type="button"
        on:click={() => fileInputRef?.click()}
        disabled={isLoading || isUploading}
        class="p-2.5 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 transition-colors flex-shrink-0 cursor-pointer"
        title="Attach documents"
      >
        <Paperclip class="w-5 h-5" />
      </button>

      <button
        type="button"
        on:click={onWebSearchToggle}
        disabled={isLoading}
        class={`p-2.5 rounded-lg transition-colors flex-shrink-0 cursor-pointer ${
          webSearchEnabled
            ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900/60'
            : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800'
        }`}
        title={webSearchEnabled ? 'Web search enabled' : 'Enable web search'}
      >
        <Globe class="w-5 h-5" />
      </button>

      <div class="flex-1 relative">
        <textarea
          bind:value={message}
          on:keydown={handleKeyDown}
          placeholder="Ask about Constitution of India, BNS, BNSS, case laws..."
          rows="2"
          disabled={isLoading}
          class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent min-h-[52px] max-h-[180px] resize-none transition-all text-sm leading-relaxed"
        ></textarea>
      </div>

      <button
        type="button"
        on:click={handleSend}
        disabled={(!message.trim() && attachments.length === 0) || isLoading}
        class="p-3 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white rounded-xl shadow-md shadow-amber-600/20 disabled:opacity-50 transition-all flex-shrink-0 cursor-pointer"
        aria-label="Send message"
      >
        <Send class="w-5 h-5" />
      </button>
    </div>

    <!-- Helper Footnote -->
    <p class="text-xs text-gray-500 dark:text-gray-500 mt-2 px-2">
      Press Enter to send, Shift+Enter for new line
      {#if webSearchEnabled}
        <span class="ml-2 text-amber-600 dark:text-amber-400 font-medium">• Web search enabled</span>
      {/if}
    </p>
  </div>
</div>
