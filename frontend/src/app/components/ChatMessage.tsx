import { User, Scale, Paperclip } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ThinkingIndicator } from './ThinkingIndicator';
import type { Message } from '../types/chat';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user' || message.role === 'human';

  const time = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className={`message-row${isUser ? ' user-row' : ''}`}>
      {/* Avatar */}
      <div className={`avatar ${isUser ? 'avatar-user' : 'avatar-ai'}`}>
        {isUser
          ? <User size={15} color="rgba(255,255,255,0.92)" />
          : <Scale size={15} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
        }
      </div>

      {/* Content */}
      <div className="message-content-wrap">
        <div className="message-meta">
          <span className="message-sender">{isUser ? 'You' : 'LegalGPT'}</span>
          {time && <span className="message-time">{time}</span>}
        </div>

        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="attachments-row">
            {message.attachments.map((a) => (
              <div key={a.id} className="attachment-chip">
                <Paperclip size={11} />
                <span>{a.name}</span>
                <span style={{ opacity: 0.55, fontSize: '10px' }}>
                  {(a.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Thinking stages (tool calls / explicit stages) */}
        {message.thinking && message.thinking.length > 0 && (
          <ThinkingIndicator stages={message.thinking} />
        )}

        {/* Message bubble */}
        {(message.content || message.isStreaming) && (
          <div className={`message-bubble ${isUser ? 'bubble-user' : 'bubble-ai'}`}>
            {message.content ? (
              <div className="prose">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              /* empty bubble while streaming but no content yet */
              <ThinkingIndicator stages={[]} isActive />
            )}
          </div>
        )}
      </div>
    </div>
  );
}