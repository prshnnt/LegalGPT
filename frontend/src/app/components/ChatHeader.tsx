import { Menu, Settings } from 'lucide-react';
import { Button } from './ui/button';

interface ChatHeaderProps {
  threadTitle: string;
  onMenuClick: () => void;
}

export function ChatHeader({ threadTitle, onMenuClick }: ChatHeaderProps) {
  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="md:hidden"
          >
            <Menu className="w-5 h-5" />
          </Button>
          
          <h2 className="font-semibold text-lg text-gray-900 dark:text-gray-100">
            {threadTitle}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Settings className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}