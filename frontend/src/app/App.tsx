import { useState, useRef, useEffect } from 'react';
import { Message, Attachment, ChatSettings, ChatThread } from './types/chat';
import { sendMessage } from './services/api';
import { Sidebar } from './components/Sidebar';
import { ChatHeader } from './components/ChatHeader';
import { ChatMessage } from './components/ChatMessage';
import { MessageInput } from './components/MessageInput';
import { EmptyState } from './components/EmptyState';
import { ScrollArea } from './components/ui/scroll-area';

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState<ChatSettings>({
    webSearchEnabled: false,
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [threads, setThreads] = useState<ChatThread[]>([
    // Mock threads for demonstration
    {
      id: '1',
      title: 'Article 21 - Right to Life',
      preview: 'Explain Article 21 in detail...',
      timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 mins ago
      messageCount: 5
    },
    {
      id: '2',
      title: 'BNS vs IPC differences',
      preview: 'Key differences between BNS and IPC...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
      messageCount: 8
    },
    {
      id: '3',
      title: 'Landmark judgments 2024',
      preview: 'Recent Supreme Court cases...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), // 3 days ago
      messageCount: 12
    },
    {
      id: '4',
      title: 'BNSS procedural changes',
      preview: 'Changes in criminal procedure under BNSS...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10), // 10 days ago
      messageCount: 6
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (content: string, attachments: Attachment[]) => {
    if (!content.trim() && attachments.length === 0) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: attachments.length > 0 ? attachments : undefined,
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Create assistant message with streaming
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    // Add thinking stages if web search is enabled
    if (settings.webSearchEnabled) {
      assistantMessage.thinking = [
        {
          id: '1',
          type: 'searching',
          content: 'Searching legal databases and web...',
          timestamp: new Date(),
        },
      ];
    } else {
      assistantMessage.thinking = [
        {
          id: '1',
          type: 'thinking',
          timestamp: new Date(),
        },
      ];
    }

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Call API (placeholder implementation)
      const stream = await sendMessage(content, attachments, settings, messages);
      const reader = stream.getReader();
      const decoder = new TextDecoder();

      let accumulatedContent = '';

      // Simulate thinking stage completion
      setTimeout(() => {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMessage.id
              ? {
                  ...msg,
                  thinking: [
                    ...(msg.thinking || []),
                    {
                      id: '2',
                      type: 'analyzing',
                      content: 'Analyzing legal context...',
                      timestamp: new Date(),
                    },
                  ],
                }
              : msg
          )
        );
      }, 800);

      // Read the stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = value; // value is already a string
        accumulatedContent += chunk;

        // Update message with streamed content
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMessage.id
              ? {
                  ...msg,
                  content: accumulatedContent,
                  isStreaming: true,
                  thinking: undefined, // Remove thinking indicator once content starts
                }
              : msg
          )
        );
      }

      // Mark streaming as complete
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessage.id
            ? { ...msg, isStreaming: false }
            : msg
        )
      );

      // Update or create thread
      if (!activeThreadId && messages.length === 0) {
        // Create new thread
        const newThread: ChatThread = {
          id: Date.now().toString(),
          title: content.slice(0, 50) + (content.length > 50 ? '...' : ''),
          preview: content.slice(0, 100),
          timestamp: new Date(),
          messageCount: 2
        };
        setThreads(prev => [newThread, ...prev]);
        setActiveThreadId(newThread.id);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setActiveThreadId(null);
    setSidebarOpen(false);
  };

  const handleThreadSelect = (threadId: string) => {
    setActiveThreadId(threadId);
    // In a real app, you would load the messages for this thread
    setMessages([]);
    setSidebarOpen(false);
  };

  const handleWebSearchToggle = () => {
    setSettings(prev => ({ ...prev, webSearchEnabled: !prev.webSearchEnabled }));
  };

  const handleExampleClick = (text: string) => {
    // If example mentions web search, enable it
    if (text.toLowerCase().includes('search the web')) {
      setSettings(prev => ({ ...prev, webSearchEnabled: true }));
    }
    handleSendMessage(text, []);
  };

  return (
    <div className="size-full flex bg-white dark:bg-gray-950">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onThreadSelect={handleThreadSelect}
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatHeader onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
        
        <div className="flex-1 overflow-hidden">
          {messages.length === 0 ? (
            <EmptyState onExampleClick={handleExampleClick} />
          ) : (
            <ScrollArea className="h-full">
              <div className="max-w-4xl mx-auto">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          )}
        </div>

        <MessageInput
          onSend={handleSendMessage}
          isLoading={isLoading}
          webSearchEnabled={settings.webSearchEnabled}
          onWebSearchToggle={handleWebSearchToggle}
        />
      </div>
    </div>
  );
}