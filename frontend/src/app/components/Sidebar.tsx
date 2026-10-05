import { useState } from 'react';
import {
  MessageSquare, Plus, X, Scale, Trash2, LogOut
} from 'lucide-react';
import type { ChatThread } from '../types/chat';

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string | number | null;
  onThreadSelect: (id: string | number) => void;
  onThreadDelete?: (id: string | number) => void;
  onNewChat: () => void;
  onLogout?: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

const formatDate = (date: Date): string => {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / 86_400_000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  return date.toLocaleDateString();
};

const groupThreads = (threads: ChatThread[]) => {
  const groups: Record<string, ChatThread[]> = {
    Today: [],
    Yesterday: [],
    'Previous 7 Days': [],
    Older: [],
  };
  for (const t of threads) {
    const d = t.timestamp ? formatDate(t.timestamp) : 'Older';
    if (d === 'Today') groups.Today.push(t);
    else if (d === 'Yesterday') groups.Yesterday.push(t);
    else if (d.includes('days ago')) groups['Previous 7 Days'].push(t);
    else groups.Older.push(t);
  }
  return groups;
};

export function Sidebar({
  threads,
  activeThreadId,
  onThreadSelect,
  onThreadDelete,
  onNewChat,
  onLogout,
  isOpen,
  onToggle,
}: SidebarProps) {
  const [hoveredId, setHoveredId] = useState<string | number | null>(null);
  const grouped = groupThreads(threads);

  return (
    <>
      {/* Mobile overlay - strictly hidden on desktop via CSS */}
      <div
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={onToggle}
        aria-hidden="true"
      />

      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        {/* Header */}
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="sidebar-mark">
              <Scale size={16} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
            </div>
            <span className="sidebar-wordmark">LegalGPT</span>
          </div>
          <button
            onClick={onToggle}
            className="icon-btn"
            style={{ display: 'none' }}
            id="sidebar-close-btn"
            aria-label="Close sidebar"
          >
            <X size={16} />
          </button>
        </div>

        {/* New Chat */}
        <button className="sidebar-new-btn" onClick={onNewChat}>
          <Plus size={15} strokeWidth={2.2} />
          <span>New Legal Query</span>
        </button>

        {/* Thread list */}
        <nav className="sidebar-threads">
          {Object.entries(grouped).map(([group, items]) => {
            if (!items.length) return null;
            return (
              <div key={group}>
                <div className="sidebar-section-label">{group}</div>
                {items.map((thread) => (
                  <div
                    key={thread.id}
                    className={`thread-item${activeThreadId === thread.id ? ' active' : ''}`}
                    onClick={() => onThreadSelect(thread.id)}
                    onMouseEnter={() => setHoveredId(thread.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  >
                    <MessageSquare size={14} className="thread-icon" />
                    <span className="thread-title">{thread.title}</span>
                    {onThreadDelete && hoveredId === thread.id && (
                      <button
                        className="thread-delete"
                        onClick={(e) => {
                          e.stopPropagation();
                          onThreadDelete(thread.id);
                        }}
                        aria-label="Delete thread"
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            );
          })}

          {threads.length === 0 && (
            <div style={{
              padding: '32px 8px',
              textAlign: 'center',
              color: 'rgba(255,255,255,0.22)',
              fontSize: '13px',
              lineHeight: '1.6',
            }}>
              No conversations yet.<br />Start a new legal query.
            </div>
          )}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          {onLogout && (
            <button className="sidebar-logout-btn" onClick={onLogout}>
              <LogOut size={14} />
              <span>Logout</span>
            </button>
          )}
          <div style={{
            marginTop: '10px',
            fontSize: '10px',
            color: 'rgba(255,255,255,0.18)',
            textAlign: 'center',
            letterSpacing: '0.04em',
          }}>
            LegalGPT for Law Students
          </div>
        </div>
      </aside>

      {/* CSS to show close btn on mobile */}
      <style>{`
        @media (max-width:599px), (max-height:599px) and (max-width:1180px) {
          #sidebar-close-btn { display: flex !important; }
        }
      `}</style>
    </>
  );
}