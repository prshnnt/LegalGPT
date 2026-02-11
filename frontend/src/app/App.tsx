import { useState, useEffect, useRef } from 'react';
import '../styles/index.css';
import { Sidebar } from './components/Sidebar';
import { ChatHeader } from './components/ChatHeader';
import { ChatMessage } from './components/ChatMessage';
import { MessageInput } from './components/MessageInput';
import { EmptyState } from './components/EmptyState';
import { AuthModal } from './components/AuthModal';
import { ThinkingIndicator } from './components/ThinkingIndicator';
import { Menu } from 'lucide-react';
import { Button } from './components/ui/button';
import { ScrollArea } from './components/ui/scroll-area';
import { 
  TokenManager, 
  getThreads, 
  createThread, 
  getThreadHistory,
  deleteThread,
  sendMessageStream 
} from './services/api';
import { 
  Message, 
  ChatThread, 
  Attachment, 
  ChatThreadResponse,
  ChatMessageResponse 
} from './types/chat';

export default function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // UI state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);

  // Chat state
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check authentication on mount
  useEffect(() => {
    console.log('[LegalGPT] Checking authentication...');
    const token = TokenManager.getToken();
    console.log('[LegalGPT] Token present:', !!token);
    
    if (token) {
      setIsAuthenticated(true);
      loadThreads();
    } else {
      setShowAuthModal(true);
    }
    setIsCheckingAuth(false);
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load all threads from backend
  const loadThreads = async () => {
    try {
      const fetchedThreads = await getThreads();
      const mappedThreads: ChatThread[] = fetchedThreads.map((t: ChatThreadResponse) => ({
        id: t.id,
        title: t.title,
        timestamp: new Date(t.updated_at),
        created_at: t.created_at,
        updated_at: t.updated_at
      }));
      setThreads(mappedThreads);
    } catch (error) {
      console.error('Failed to load threads:', error);
      // If authentication fails (401), logout
      if (error instanceof Error && error.message.includes('401')) {
        handleLogout();
      }
    }
  };

  // Load messages for a specific thread
  const loadThreadMessages = async (threadId: string | number) => {
    try {
      setIsLoading(true);
      const history = await getThreadHistory(threadId);
      
      const mappedMessages: Message[] = history.messages.map((msg: ChatMessageResponse) => ({
        id: msg.id,
        role: msg.role === 'human' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: new Date(msg.created_at),
        created_at: msg.created_at
      }));
      
      setMessages(mappedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle authentication success
  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
    setShowAuthModal(false);
    loadThreads();
  };

  // Handle logout
  const handleLogout = () => {
    TokenManager.clearToken();
    setIsAuthenticated(false);
    setShowAuthModal(true);
    setThreads([]);
    setMessages([]);
    setActiveThreadId(null);
  };

  // Create new thread
  const handleNewChat = async () => {
    try {
      const newThread = await createThread('New Legal Query');
      const mappedThread: ChatThread = {
        id: newThread.id,
        title: newThread.title,
        timestamp: new Date(newThread.created_at),
        created_at: newThread.created_at,
        updated_at: newThread.updated_at
      };
      
      setThreads(prev => [mappedThread, ...prev]);
      setActiveThreadId(newThread.id);
      setMessages([]);
      setIsSidebarOpen(false);
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  };

  // Select a thread
  const handleThreadSelect = async (threadId: string | number) => {
    setActiveThreadId(threadId);
    setIsSidebarOpen(false);
    await loadThreadMessages(threadId);
  };

  // Delete a thread
  const handleThreadDelete = async (threadId: string | number) => {
    try {
      await deleteThread(threadId);
      setThreads(prev => prev.filter(t => t.id !== threadId));
      
      if (activeThreadId === threadId) {
        setActiveThreadId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
    }
  };

  // Send message with streaming support
  const handleSendMessage = async (content: string, attachments: Attachment[]) => {
    if (!activeThreadId) {
      // Create a new thread if none exists
      await handleNewChat();
      // Wait for state to update, then retry
      setTimeout(() => handleSendMessage(content, attachments), 100);
      return;
    }

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: attachments.length > 0 ? attachments : undefined
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsStreaming(true);

    // Create placeholder for assistant response
    const assistantMessageId = Date.now() + 1;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Stream the response
      let accumulatedContent = '';
      
      for await (const chunk of sendMessageStream(activeThreadId, content)) {
        if (chunk.type === 'content' && chunk.content) {
          accumulatedContent += chunk.content;
          
          // Update the assistant message with accumulated content
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, content: accumulatedContent, isStreaming: true }
              : msg
          ));
        } else if (chunk.type === 'tool_call' && chunk.tool_name) {
          // Handle tool calls (web search, etc.)
          console.log('Tool call:', chunk.tool_name, chunk.tool_input);
        } else if (chunk.type === 'error') {
          console.error('Stream error:', chunk.content);
          accumulatedContent += '\n\n[Error: ' + chunk.content + ']';
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, content: accumulatedContent, isStreaming: false }
              : msg
          ));
        } else if (chunk.type === 'end') {
          // Mark streaming as complete
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, isStreaming: false }
              : msg
          ));
        }
      }

      // Refresh thread list to update timestamps
      await loadThreads();
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { 
              ...msg, 
              content: 'Sorry, I encountered an error processing your request. Please try again.', 
              isStreaming: false 
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  // Show loading screen while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">⚖️</span>
          </div>
          <p className="text-gray-600 dark:text-gray-400">Loading LegalGPT...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <AuthModal isOpen={showAuthModal} onSuccess={handleAuthSuccess} />
      
      {isAuthenticated && (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
          {/* Sidebar */}
          <Sidebar
            threads={threads}
            activeThreadId={activeThreadId}
            onThreadSelect={handleThreadSelect}
            onThreadDelete={handleThreadDelete}
            onNewChat={handleNewChat}
            onLogout={handleLogout}
            isOpen={isSidebarOpen}
            onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          />

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Header */}
            <ChatHeader
              threadTitle={threads.find(t => t.id === activeThreadId)?.title || 'LegalGPT'}
              onMenuClick={() => setIsSidebarOpen(true)}
            />

            {/* Messages Area */}
            <ScrollArea className="flex-1">
              <div className="max-w-4xl mx-auto p-4 space-y-6">
                {messages.length === 0 ? (
                  <EmptyState onExampleClick={handleSendMessage} />
                ) : (
                  <>
                    {messages.map((message) => (
                      <ChatMessage key={message.id} message={message} />
                    ))}
                    {isStreaming && messages[messages.length - 1]?.isStreaming && (
                      <ThinkingIndicator stages={[]} isActive={true} />
                    )}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input Area */}
            <MessageInput
              onSend={handleSendMessage}
              isLoading={isLoading}
              webSearchEnabled={webSearchEnabled}
              onWebSearchToggle={() => setWebSearchEnabled(!webSearchEnabled)}
            />
          </div>
        </div>
      )}
    </>
  );
}