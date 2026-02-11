import { Message } from '../types/chat';
import { User, Scale, Paperclip } from 'lucide-react';
import { ThinkingIndicator } from './ThinkingIndicator';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user' || message.role === 'human';

  return (
    <div className={`flex gap-4 p-6 ${isUser ? 'bg-white dark:bg-gray-950' : 'bg-gray-50 dark:bg-gray-900'}`}>
      <div className="flex-shrink-0">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-gradient-to-br from-amber-600 to-orange-600 text-white'
        }`}>
          {isUser ? <User className="w-5 h-5" /> : <Scale className="w-5 h-5" />}
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-semibold text-sm text-gray-900 dark:text-gray-100">
            {isUser ? 'You' : 'LegalGPT'}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-500">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {message.attachments && message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {message.attachments.map((attachment) => (
              <div
                key={attachment.id}
                className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm"
              >
                <Paperclip className="w-4 h-4 text-gray-500" />
                <span className="text-gray-700 dark:text-gray-300">{attachment.name}</span>
                <span className="text-gray-500 dark:text-gray-500">
                  ({(attachment.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            ))}
          </div>
        )}

        {message.thinking && message.thinking.length > 0 && (
          <ThinkingIndicator stages={message.thinking} />
        )}

        {message.isStreaming && !message.content && (
          <ThinkingIndicator stages={[]} isActive={true} />
        )}

        {message.content && (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {/* <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-7">
              {message.content}
            </p> */}
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}