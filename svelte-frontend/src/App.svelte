<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { Scale } from '@lucide/svelte';

  import Sidebar from './lib/components/Sidebar.svelte';
  import ChatHeader from './lib/components/ChatHeader.svelte';
  import ChatMessage from './lib/components/ChatMessage.svelte';
  import MessageInput from './lib/components/MessageInput.svelte';
  import EmptyState from './lib/components/EmptyState.svelte';
  import AuthModal from './lib/components/AuthModal.svelte';

  import {
    TokenManager,
    getThreads,
    createThread,
    getThreadHistory,
    deleteThread,
    sendMessageStream,
  } from './lib/services/api';
  import type {
    Message,
    ChatThread,
    Attachment,
    ChatThreadResponse,
    ChatMessageResponse,
  } from './lib/types/chat';

  const SIDEBAR_W = 280;

  // Auth
  let isAuthenticated = false;
  let showAuthModal = false;
  let isCheckingAuth = true;

  // UI
  let isDesktop = typeof window !== 'undefined' ? window.innerWidth >= 600 : true;
  let isSidebarOpen = typeof window !== 'undefined' ? window.innerWidth >= 768 : true;
  let webSearchEnabled = false;
  let isDarkMode = true;

  // Data
  let threads: ChatThread[] = [];
  let activeThreadId: string | number | null = null;
  let messages: Message[] = [];
  let isLoading = false;

  let messagesEndRef: HTMLDivElement;

  async function scrollToBottom() {
    await tick();
    if (messagesEndRef) {
      messagesEndRef.scrollIntoView({ behavior: 'smooth' });
    }
  }

  $: if (messages) {
    scrollToBottom();
  }

  onMount(() => {
    const handleResize = () => {
      isDesktop = window.innerWidth >= 600;
    };
    window.addEventListener('resize', handleResize);

    const token = TokenManager.getToken();
    if (token) {
      isAuthenticated = true;
      loadThreads();
    } else {
      showAuthModal = true;
    }
    isCheckingAuth = false;

    // Apply saved theme
    const saved = localStorage.getItem('legalgpt-theme');
    if (saved === 'light') {
      isDarkMode = false;
      document.documentElement.classList.remove('dark');
    } else {
      isDarkMode = true;
      document.documentElement.classList.add('dark');
    }

    return () => window.removeEventListener('resize', handleResize);
  });

  function toggleTheme() {
    isDarkMode = !isDarkMode;
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('legalgpt-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('legalgpt-theme', 'light');
    }
  }

  /* ── Threads ── */
  async function loadThreads() {
    try {
      const fetched = await getThreads();
      threads = fetched.map((t: ChatThreadResponse) => ({
        id: t.id,
        title: t.title,
        timestamp: new Date(t.updated_at),
        created_at: t.created_at,
        updated_at: t.updated_at,
      }));
    } catch (err) {
      console.error('loadThreads', err);
      if (err instanceof Error && err.message.includes('401')) {
        handleLogout();
      }
    }
  }

  async function loadMessages(threadId: string | number) {
    try {
      isLoading = true;
      const history = await getThreadHistory(threadId);
      messages = history.messages.map((m: ChatMessageResponse) => ({
        id: m.id,
        role: m.role === 'human' ? 'user' : 'assistant',
        content: m.content,
        timestamp: new Date(m.created_at),
      }));
    } catch (err) {
      console.error('loadMessages', err);
      messages = [];
    } finally {
      isLoading = false;
    }
  }

  /* ── Auth ── */
  function handleAuthSuccess() {
    isAuthenticated = true;
    showAuthModal = false;
    loadThreads();
  }

  function handleLogout() {
    TokenManager.clearToken();
    isAuthenticated = false;
    showAuthModal = true;
    threads = [];
    messages = [];
    activeThreadId = null;
  }

  /* ── Thread actions ── */
  function handleNewChat() {
    activeThreadId = null;
    messages = [];
    if (!isDesktop) {
      isSidebarOpen = false;
    }
  }

  async function handleThreadSelect(id: string | number) {
    activeThreadId = id;
    if (!isDesktop) {
      isSidebarOpen = false;
    }
    await loadMessages(id);
  }

  async function handleThreadDelete(id: string | number) {
    try {
      await deleteThread(id);
      threads = threads.filter((t) => t.id !== id);
      if (activeThreadId === id) {
        activeThreadId = null;
        messages = [];
      }
    } catch (err) {
      console.error('handleThreadDelete', err);
    }
  }

  /* ── Send message (streaming) ── */
  async function handleSendMessage(content: string, attachments: Attachment[]) {
    let tid = activeThreadId;

    if (!tid) {
      try {
        const title = content.trim().slice(0, 32) || 'Legal Query';
        const t = await createThread(title);
        const mapped: ChatThread = {
          id: t.id,
          title: t.title,
          timestamp: new Date(t.created_at),
          created_at: t.created_at,
          updated_at: t.updated_at,
        };
        threads = [mapped, ...threads];
        activeThreadId = t.id;
        tid = t.id;
      } catch {
        return;
      }
    }

    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: attachments.length ? attachments : undefined,
    };
    messages = [...messages, userMsg];
    isLoading = true;

    const aiId = Date.now() + 1;
    const aiMsg: Message = {
      id: aiId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    messages = [...messages, aiMsg];

    try {
      let acc = '';
      for await (const chunk of sendMessageStream(tid!, content)) {
        if (chunk.type === 'content' && chunk.content) {
          acc += chunk.content;
          messages = messages.map((m) =>
            m.id === aiId ? { ...m, content: acc, isStreaming: true } : m
          );
        } else if (chunk.type === 'error') {
          acc += '\n\n[Error: ' + chunk.content + ']';
          messages = messages.map((m) =>
            m.id === aiId ? { ...m, content: acc, isStreaming: false } : m
          );
        } else if (chunk.type === 'end') {
          messages = messages.map((m) =>
            m.id === aiId ? { ...m, isStreaming: false } : m
          );
        }
      }
      await loadThreads();
    } catch (err) {
      console.error('stream error', err);
      messages = messages.map((m) =>
        m.id === aiId
          ? {
              ...m,
              content:
                'Sorry, I encountered an error processing your request. Please try again.',
              isStreaming: false,
            }
          : m
      );
    } finally {
      isLoading = false;
    }
  }

  $: activeTitle =
    threads.find((t) => t.id === activeThreadId)?.title ?? 'LegalGPT';
</script>

{#if isCheckingAuth}
  <div class="loading-splash">
    <div class="loading-mark">
      <Scale size={28} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
    </div>
    <p class="loading-text">LOADING LEGALGPT</p>
  </div>
{:else}
  <!-- Full-viewport bg video -->
  <video
    class="bg-video"
    src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260826_124724_bc041163-d651-425f-aea3-2acc1efc2c96.mp4"
    autoplay
    muted
    loop
    playsinline
    aria-hidden="true"
  ></video>
  <div class="bg-overlay" aria-hidden="true"></div>

  <!-- Auth modal -->
  <AuthModal isOpen={showAuthModal} onSuccess={handleAuthSuccess} />

  {#if isAuthenticated}
    <div class="app-root">
      <!-- Sidebar -->
      <Sidebar
        {threads}
        {activeThreadId}
        onThreadSelect={handleThreadSelect}
        onThreadDelete={handleThreadDelete}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        isOpen={isSidebarOpen}
        onToggle={() => (isSidebarOpen = !isSidebarOpen)}
      />

      <!-- Main -->
      <main class="chat-main">
        <!-- Header -->
        <ChatHeader
          threadTitle={activeTitle}
          onMenuClick={() => (isSidebarOpen = !isSidebarOpen)}
          {isDarkMode}
          onToggleTheme={toggleTheme}
        />

        <!-- Messages -->
        <div class="messages-area">
          <div class="messages-inner">
            {#if messages.length === 0}
              <EmptyState onExampleClick={handleSendMessage} />
            {:else}
              {#each messages as msg (msg.id)}
                <ChatMessage message={msg} />
              {/each}
            {/if}
            <div bind:this={messagesEndRef} style="height: 1px;"></div>
          </div>
        </div>

        <!-- Composer -->
        <MessageInput
          onSend={handleSendMessage}
          {isLoading}
          {webSearchEnabled}
          onWebSearchToggle={() => (webSearchEnabled = !webSearchEnabled)}
          sidebarWidth={isDesktop && isSidebarOpen ? SIDEBAR_W : 0}
        />
      </main>
    </div>
  {/if}
{/if}
