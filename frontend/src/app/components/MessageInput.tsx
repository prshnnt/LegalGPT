import { useState, useRef, type KeyboardEvent, type ChangeEvent } from 'react';
import { ArrowUp, Paperclip, Globe, ChevronDown, X } from 'lucide-react';
import type { Attachment } from '../types/chat';
import { uploadFile } from '../services/api';

interface MessageInputProps {
  onSend: (message: string, attachments: Attachment[]) => void;
  isLoading?: boolean;
  webSearchEnabled: boolean;
  onWebSearchToggle: () => void;
  /** left offset so the card centers correctly when sidebar is visible */
  sidebarWidth?: number;
}

export function MessageInput({
  onSend,
  isLoading,
  webSearchEnabled,
  onWebSearchToggle,
  sidebarWidth = 280,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if ((!message.trim() && !attachments.length) || isLoading) return;
    onSend(message, attachments);
    setMessage('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleResize = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
  };

  const handleFiles = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    setIsUploading(true);
    try {
      const uploaded = await Promise.all(files.map((f) => uploadFile(f)));
      setAttachments((prev) => [...prev, ...uploaded]);
    } catch (err) {
      console.error('Upload error', err);
    } finally {
      setIsUploading(false);
    }
  };

  const canSend = (!!message.trim() || attachments.length > 0) && !isLoading;

  return (
    <div
      className="composer-wrap"
      style={{ left: `${sidebarWidth}px` }}
    >
      {/* Background video behind composer */}
      <form className="card" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
        {/* ── Attachment preview ── */}
        {attachments.length > 0 && (
          <div className="attach-preview">
            {attachments.map((a) => (
              <div key={a.id} className="attachment-chip" style={{ cursor: 'default' }}>
                <Paperclip size={11} />
                <span>{a.name}</span>
                <button
                  type="button"
                  onClick={() => setAttachments((p) => p.filter((x) => x.id !== a.id))}
                  style={{
                    marginLeft: '4px',
                    color: 'rgba(255,255,255,0.40)',
                    cursor: 'pointer',
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    display: 'flex',
                  }}
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* ── Textarea ── */}
        <textarea
          ref={textareaRef}
          className="card-textarea"
          value={message}
          onChange={handleResize}
          onKeyDown={handleKey}
          placeholder="Ask about Constitution of India, BNS, BNSS, case laws…"
          rows={1}
          disabled={isLoading}
          aria-label="Chat message"
        />

        {/* ── Toolbar strip ── */}
        <div className="tools">
          {/* Left: chips */}
          <div className="chips">
            {/* Web search chip */}
            <button
              type="button"
              className={`chip${webSearchEnabled ? ' active' : ''}`}
              onClick={onWebSearchToggle}
              disabled={isLoading}
              style={{ '--cw': '107', '--pl': '12', '--ig': '3.7' } as React.CSSProperties}
            >
              <Globe size={13} className="chip-icon" />
              <span className="chip-label">Web Search</span>
            </button>

            {/* Attach screens chip */}
            <button
              type="button"
              className="chip"
              onClick={() => fileRef.current?.click()}
              disabled={isLoading || isUploading}
              style={{ '--cw': '108', '--pl': '16', '--ig': '3.9' } as React.CSSProperties}
            >
              <Paperclip size={12} className="chip-icon" />
              <span className="chip-label">
                {isUploading ? 'Uploading…' : 'Attach File'}
              </span>
            </button>
          </div>

          {/* Right cluster — absolute on desktop */}
          <div className="right">
            {/* Model selector */}
            <button
              type="button"
              className="model-sel"
              tabIndex={-1}
              aria-label="Model: LegalGPT"
            >
              <span>LegalGPT</span>
              <ChevronDown
                size={11}
                className="model-chevron"
                style={{ opacity: 0.55 }}
              />
            </button>

            {/* Attach button (raw SVG, no padding) */}
            <button
              type="button"
              className="attach-btn"
              onClick={() => fileRef.current?.click()}
              disabled={isLoading || isUploading}
              aria-label="Attach document"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66L9.41 16.41A2 2 0 016.59 13.6l8.49-8.49" />
              </svg>
            </button>

            {/* Send circle */}
            <button
              type="submit"
              className="send-btn"
              disabled={!canSend}
              aria-label="Build it"
            >
              {/* White up-arrow */}
              <svg
                className="send-icon"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 19V5M5 12l7-7 7 7"
                  stroke="rgba(30,15,5,0.90)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Web search note */}
        {webSearchEnabled && (
          <div className="search-badge">
            <Globe size={11} />
            Web search enabled
          </div>
        )}

        {/* Hidden file input */}
        <input
          ref={fileRef}
          type="file"
          multiple
          className="file-input-hidden"
          onChange={handleFiles}
          accept="image/*,.pdf,.doc,.docx,.txt"
        />
      </form>
    </div>
  );
}
