import { useState, useEffect, useRef } from 'react';
import '../styles/index.css';

import { Sidebar } from './components/Sidebar';
import { ChatHeader } from './components/ChatHeader';
import { ChatMessage } from './components/ChatMessage';
import { MessageInput } from './components/MessageInput';
import { EmptyState } from './components/EmptyState';
import { AuthModal } from './components/AuthModal';
import { Scale } from 'lucide-react';

import {
  TokenManager,
  getThreads,
  createThread,
  getThreadHistory,
  deleteThread,
  sendMessageStream,
} from './services/api';
import type {
  Message,
  ChatThread,
  Attachment,
  ChatThreadResponse,
  ChatMessageResponse,
} from './types/chat';

const SIDEBAR_W = 280;

export default function App() {
  // Auth
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // UI
  const [isDesktop, setIsDesktop] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 600 : true
  );
  const [isSidebarOpen, setIsSidebarOpen] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 768 : true
  );
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);

  // Resize listener
  useEffect(() => {
    const handleResize = () => {
      const desktop = window.innerWidth >= 600;
      setIsDesktop(desktop);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Data
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  /* ── Boot ── */
  useEffect(() => {
    const token = TokenManager.getToken();
    if (token) {
      setIsAuthenticated(true);
      loadThreads();
    } else {
      setShowAuthModal(true);
    }
    setIsCheckingAuth(false);

    // Apply saved theme
    const saved = localStorage.getItem('legalgpt-theme');
    if (saved === 'light') {
      setIsDarkMode(false);
      document.documentElement.classList.remove('dark');
    } else {
      // default dark
      document.documentElement.classList.add('dark');
    }
  }, []);

  /* ── Theme effect ── */
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('legalgpt-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('legalgpt-theme', 'light');
    }
  }, [isDarkMode]);

  /* ── Auto-scroll ── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /* ── Threads ── */
  const loadThreads = async () => {
    try {
      const fetched = await getThreads();
      setThreads(fetched.map((t: ChatThreadResponse) => ({
        id: t.id,
        title: t.title,
        timestamp: new Date(t.updated_at),
        created_at: t.created_at,
        updated_at: t.updated_at,
      })));
    } catch (err) {
      console.error('loadThreads', err);
      if (err instanceof Error && err.message.includes('401')) handleLogout();
    }
  };

  const loadMessages = async (threadId: string | number) => {
    try {
      setIsLoading(true);
      const history = await getThreadHistory(threadId);
      setMessages(history.messages.map((m: ChatMessageResponse) => ({
        id: m.id,
        role: m.role === 'human' ? 'user' : 'assistant',
        content: m.content,
        timestamp: new Date(m.created_at),
      })));
    } catch (err) {
      console.error('loadMessages', err);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };

  /* ── Auth ── */
  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
    setShowAuthModal(false);
    loadThreads();
  };

  const handleLogout = () => {
    TokenManager.clearToken();
    setIsAuthenticated(false);
    setShowAuthModal(true);
    setThreads([]);
    setMessages([]);
    setActiveThreadId(null);
  };

  /* ── Thread actions ── */
  // "New Chat" only resets local state — no DB thread is created until the
  // user actually sends a message. This prevents empty ghost threads.
  const handleNewChat = () => {
    setActiveThreadId(null);
    setMessages([]);
    setIsSidebarOpen(false);
  };

  const handleThreadSelect = async (id: string | number) => {
    setActiveThreadId(id);
    setIsSidebarOpen(false);
    await loadMessages(id);
  };

  const handleThreadDelete = async (id: string | number) => {
    try {
      await deleteThread(id);
      setThreads((prev) => prev.filter((t) => t.id !== id));
      if (activeThreadId === id) {
        setActiveThreadId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('handleThreadDelete', err);
    }
  };

  /* ── Send message (streaming) ── */
  const handleSendMessage = async (
    content: string,
    attachments: Attachment[],
  ) => {
    let tid = activeThreadId;

    // Auto-create thread if needed (only when conversation actually starts)
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
        setThreads((prev) => [mapped, ...prev]);
        setActiveThreadId(t.id);
        tid = t.id;
      } catch {
        return;
      }
    }

    // Add user message
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: attachments.length ? attachments : undefined,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Placeholder AI message
    const aiId = Date.now() + 1;
    const aiMsg: Message = {
      id: aiId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages((prev) => [...prev, aiMsg]);

    try {
      let acc = '';
      for await (const chunk of sendMessageStream(tid!, content)) {
        if (chunk.type === 'content' && chunk.content) {
          acc += chunk.content;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiId ? { ...m, content: acc, isStreaming: true } : m,
            ),
          );
        } else if (chunk.type === 'error') {
          acc += '\n\n[Error: ' + chunk.content + ']';
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiId ? { ...m, content: acc, isStreaming: false } : m,
            ),
          );
        } else if (chunk.type === 'end') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiId ? { ...m, isStreaming: false } : m,
            ),
          );
        }
      }
      await loadThreads();
    } catch (err) {
      console.error('stream error', err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiId
            ? {
                ...m,
                content:
                  'Sorry, I encountered an error processing your request. Please try again.',
                isStreaming: false,
              }
            : m,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  };

  /* ── Computed ── */
  const activeTitle =
    threads.find((t) => t.id === activeThreadId)?.title ?? 'LegalGPT';

  /* ── Loading splash ── */
  if (isCheckingAuth) {
    return (
      <div className="loading-splash">
        <div className="loading-mark">
          <Scale size={28} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
        </div>
        <p className="loading-text">LOADING LEGALGPT</p>
      </div>
    );
  }

  return (
    <>
      {/* Full-viewport bg video */}
      <video
        className="bg-video"
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260826_124724_bc041163-d651-425f-aea3-2acc1efc2c96.mp4"
        autoPlay
        muted
        loop
        playsInline
        aria-hidden="true"
      />
      <div className="bg-overlay" aria-hidden="true" />

      {/* Auth modal */}
      <AuthModal isOpen={showAuthModal} onSuccess={handleAuthSuccess} />

      {isAuthenticated && (
        <div className="app-root">
          {/* Sidebar */}
          <Sidebar
            threads={threads}
            activeThreadId={activeThreadId}
            onThreadSelect={handleThreadSelect}
            onThreadDelete={handleThreadDelete}
            onNewChat={handleNewChat}
            onLogout={handleLogout}
            isOpen={isSidebarOpen}
            onToggle={() => setIsSidebarOpen((o) => !o)}
          />

          {/* Main */}
          <main className="chat-main">
            {/* Header */}
            <ChatHeader
              threadTitle={activeTitle}
              onMenuClick={() => setIsSidebarOpen((o) => !o)}
              isDarkMode={isDarkMode}
              onToggleTheme={() => setIsDarkMode((d) => !d)}
            />

            {/* Messages */}
            <div className="messages-area">
              <div className="messages-inner">
                {messages.length === 0 ? (
                  <EmptyState onExampleClick={handleSendMessage} />
                ) : (
                  messages.map((msg) => (
                    <ChatMessage key={msg.id} message={msg} />
                  ))
                )}
                <div ref={messagesEndRef} style={{ height: '1px' }} />
              </div>
            </div>

            {/* Composer — pass sidebar width for left offset */}
            <MessageInput
              onSend={handleSendMessage}
              isLoading={isLoading}
              webSearchEnabled={webSearchEnabled}
              onWebSearchToggle={() => setWebSearchEnabled((v) => !v)}
              sidebarWidth={isDesktop && isSidebarOpen ? SIDEBAR_W : 0}
            />
          </main>
        </div>
      )}
    </>
  );
}