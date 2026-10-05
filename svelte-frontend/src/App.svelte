<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { Sun, Moon, Scale } from '@lucide/svelte';

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
    sendMessageStream
  } from './lib/services/api';

  import type {
    Message,
    ChatThread,
    Attachment,
    ChatThreadResponse,
    ChatMessageResponse
  } from './lib/types/chat';

  // Authentication state
  let isAuthenticated = false;
  let showAuthModal = false;
  let isCheckingAuth = true;

  // UI state
  let isSidebarOpen = false;
  let webSearchEnabled = false;
  let isDarkMode = false;

  // Chat state
  let threads: ChatThread[] = [];
  let activeThreadId: string | number | null = null;
  let messages: Message[] = [];
  let isLoading = false;
  let isStreaming = false;

  let messagesEndContainer: HTMLDivElement;

  // Scroll to bottom when messages update
  async function scrollToBottom() {
    await tick();
    if (messagesEndContainer) {
      messagesEndContainer.scrollIntoView({ behavior: 'smooth' });
    }
  }

  $: if (messages) {
    scrollToBottom();
  }

  onMount(() => {
    // Check authentication
    const token = TokenManager.getToken();
    if (token) {
      isAuthenticated = true;
      loadThreads();
    } else {
      showAuthModal = true;
    }
    isCheckingAuth = false;

    // Initialize theme
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      isDarkMode = true;
      document.documentElement.classList.add('dark');
    }
  });

  function toggleTheme() {
    isDarkMode = !isDarkMode;
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }

  // Load threads list from backend
  async function loadThreads() {
    try {
      const fetchedThreads = await getThreads();
      threads = fetchedThreads.map((t: ChatThreadResponse) => ({
        id: t.id,
        title: t.title,
        timestamp: new Date(t.updated_at),
        created_at: t.created_at,
        updated_at: t.updated_at
      }));
    } catch (error) {
      console.error('Failed to load threads:', error);
      if (error instanceof Error && error.message.includes('401')) {
        handleLogout();
      }
    }
  }

  // Load messages for a thread
  async function loadThreadMessages(threadId: string | number) {
    try {
      isLoading = true;
      const history = await getThreadHistory(threadId);
      messages = history.messages.map((msg: ChatMessageResponse) => ({
        id: msg.id,
        role: msg.role === 'human' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: new Date(msg.created_at),
        created_at: msg.created_at
      }));
    } catch (error) {
      console.error('Failed to load messages:', error);
      messages = [];
    } finally {
      isLoading = false;
    }
  }

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

  async function handleNewChat() {
    try {
      const newThread = await createThread('New Legal Query');
      const mappedThread: ChatThread = {
        id: newThread.id,
        title: newThread.title,
        timestamp: new Date(newThread.created_at),
        created_at: newThread.created_at,
        updated_at: newThread.updated_at
      };

      threads = [mappedThread, ...threads];
      activeThreadId = newThread.id;
      messages = [];
      isSidebarOpen = false;
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  }

  async function handleThreadSelect(threadId: string | number) {
    activeThreadId = threadId;
    isSidebarOpen = false;
    await loadThreadMessages(threadId);
  }

  async function handleThreadDelete(threadId: string | number) {
    try {
      await deleteThread(threadId);
      threads = threads.filter(t => t.id !== threadId);

      if (activeThreadId === threadId) {
        activeThreadId = null;
        messages = [];
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
    }
  }

  async function handleSendMessage(content: string, attachments: Attachment[]) {
    let currentThreadId = activeThreadId;

    if (!currentThreadId) {
      try {
        const newThread = await createThread('New Legal Query');
        const mappedThread: ChatThread = {
          id: newThread.id,
          title: newThread.title,
          timestamp: new Date(newThread.created_at),
          created_at: newThread.created_at,
          updated_at: newThread.updated_at
        };
        threads = [mappedThread, ...threads];
        activeThreadId = newThread.id;
        currentThreadId = newThread.id;
      } catch (error) {
        console.error('Failed to create thread for new message:', error);
        return;
      }
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: attachments.length > 0 ? attachments : undefined
    };
    messages = [...messages, userMessage];
    isLoading = true;
    isStreaming = true;

    // Add placeholder assistant message
    const assistantMessageId = Date.now() + 1;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };
    messages = [...messages, assistantMessage];

    try {
      let accumulatedContent = '';

      for await (const chunk of sendMessageStream(currentThreadId, content)) {
        if (chunk.type === 'content' && chunk.content) {
          accumulatedContent += chunk.content;
          messages = messages.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: accumulatedContent, isStreaming: true }
              : msg
          );
        } else if (chunk.type === 'tool_call' && chunk.tool_name) {
          console.log('Tool call:', chunk.tool_name, chunk.tool_input);
        } else if (chunk.type === 'error') {
          console.error('Stream error:', chunk.content);
          accumulatedContent += '\n\n[Error: ' + chunk.content + ']';
          messages = messages.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: accumulatedContent, isStreaming: false }
              : msg
          );
        } else if (chunk.type === 'end') {
          messages = messages.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, isStreaming: false }
              : msg
          );
        }
      }

      await loadThreads();
    } catch (error) {
      console.error('Error sending message:', error);
      messages = messages.map(msg =>
        msg.id === assistantMessageId
          ? {
              ...msg,
              content: 'Sorry, I encountered an error processing your request. Please try again.',
              isStreaming: false
            }
          : msg
      );
    } finally {
      isLoading = false;
      isStreaming = false;
    }
  }

  $: activeTitle = threads.find(t => t.id === activeThreadId)?.title || 'LegalGPT';
</script>

{#if isCheckingAuth}
  <!-- Loading Splash -->
  <div class="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-950">
    <div class="text-center">
      <div class="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mx-auto mb-4 animate-bounce">
        <Scale class="w-9 h-9 text-white" />
      </div>
      <p class="text-gray-600 dark:text-gray-400 font-medium">Loading LegalGPT...</p>
    </div>
  </div>
{:else}
  <AuthModal isOpen={showAuthModal} onSuccess={handleAuthSuccess} />

  {#if isAuthenticated}
    <div class="flex h-screen bg-gray-50 dark:bg-gray-950 overflow-hidden">
      <!-- Sidebar -->
      <Sidebar
        {threads}
        {activeThreadId}
        isOpen={isSidebarOpen}
        onThreadSelect={handleThreadSelect}
        onThreadDelete={handleThreadDelete}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        onToggle={() => (isSidebarOpen = !isSidebarOpen)}
      />

      <!-- Main Chat Container -->
      <div class="flex-1 flex flex-col min-w-0 h-full relative">
        <!-- Header -->
        <div class="relative z-20">
          <ChatHeader
            threadTitle={activeTitle}
            onMenuClick={() => (isSidebarOpen = true)}
          />
          <div class="absolute right-4 top-1/2 -translate-y-1/2 z-30">
            <button
              on:click={toggleTheme}
              class="p-2 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
              title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {#if isDarkMode}
                <Sun class="w-5 h-5" />
              {:else}
                <Moon class="w-5 h-5" />
              {/if}
            </button>
          </div>
        </div>

        <!-- Scrollable Messages Area -->
        <div class="flex-1 overflow-y-auto pb-36">
          <div class="max-w-4xl mx-auto p-4 space-y-6">
            {#if messages.length === 0}
              <EmptyState onExampleClick={handleSendMessage} />
            {:else}
              {#each messages as message (message.id)}
                <ChatMessage {message} />
              {/each}
            {/if}
            <div bind:this={messagesEndContainer} class="h-4"></div>
          </div>
        </div>

        <!-- Sticky Bottom Message Input -->
        <MessageInput
          onSend={handleSendMessage}
          {isLoading}
          {webSearchEnabled}
          onWebSearchToggle={() => (webSearchEnabled = !webSearchEnabled)}
        />
      </div>
    </div>
  {/if}
{/if}
