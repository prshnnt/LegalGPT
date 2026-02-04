import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Paperclip, X, Globe } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Attachment } from '../types/chat';
import { uploadFile } from '../services/api';

interface MessageInputProps {
  onSend: (message: string, attachments: Attachment[]) => void;
  isLoading?: boolean;
  webSearchEnabled: boolean;
  onWebSearchToggle: () => void;
}

export function MessageInput({ 
  onSend, 
  isLoading,
  webSearchEnabled,
  onWebSearchToggle 
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!message.trim() && attachments.length === 0) return;
    if (isLoading) return;

    onSend(message, attachments);
    setMessage('');
    setAttachments([]);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setIsUploading(true);
    try {
      const uploadedFiles = await Promise.all(
        files.map(file => uploadFile(file))
      );
      setAttachments(prev => [...prev, ...uploadedFiles]);
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
      <div className="max-w-4xl mx-auto p-4">
        {/* Attachments Display */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3 px-2">
            {attachments.map((attachment) => (
              <div
                key={attachment.id}
                className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm"
              >
                <Paperclip className="w-4 h-4 text-gray-500" />
                <span className="text-gray-700 dark:text-gray-300">{attachment.name}</span>
                <button
                  onClick={() => removeAttachment(attachment.id)}
                  className="ml-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="relative flex items-end gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            accept="image/*,.pdf,.doc,.docx,.txt"
          />
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || isUploading}
            className="flex-shrink-0"
          >
            <Paperclip className="w-5 h-5" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={onWebSearchToggle}
            disabled={isLoading}
            className={`flex-shrink-0 ${
              webSearchEnabled 
                ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50' 
                : ''
            }`}
            title={webSearchEnabled ? 'Web search enabled' : 'Enable web search'}
          >
            <Globe className="w-5 h-5" />
          </Button>

          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about Constitution of India, BNS, BNSS, case laws..."
              className="min-h-[60px] max-h-[200px] resize-none pr-12"
              disabled={isLoading}
            />
          </div>

          <Button
            onClick={handleSend}
            disabled={(!message.trim() && attachments.length === 0) || isLoading}
            size="icon"
            className="flex-shrink-0 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>

        {/* Helper Text */}
        <p className="text-xs text-gray-500 dark:text-gray-500 mt-2 px-2">
          Press Enter to send, Shift+Enter for new line
          {webSearchEnabled && <span className="ml-2 text-amber-600 dark:text-amber-400">• Web search enabled</span>}
        </p>
      </div>
    </div>
  );
}
