import { Menu, Sun, Moon } from 'lucide-react';

interface ChatHeaderProps {
  threadTitle: string;
  onMenuClick: () => void;
  isDarkMode?: boolean;
  onToggleTheme?: () => void;
}

export function ChatHeader({
  threadTitle,
  onMenuClick,
  isDarkMode,
  onToggleTheme,
}: ChatHeaderProps) {
  return (
    <header className="chat-header">
      <div className="chat-header-left">
        <button
          className="icon-btn"
          onClick={onMenuClick}
          aria-label="Open sidebar"
          style={{ flexShrink: 0 }}
        >
          <Menu size={18} />
        </button>
        <span className="chat-header-title">{threadTitle}</span>
      </div>

      <div className="chat-header-right">
        {onToggleTheme && (
          <button
            className="icon-btn"
            onClick={onToggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode
              ? <Sun size={16} />
              : <Moon size={16} />
            }
          </button>
        )}
      </div>
    </header>
  );
}