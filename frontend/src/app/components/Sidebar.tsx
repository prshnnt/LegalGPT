import { useState } from 'react';
import { MessageSquare, Plus, Menu, X, Scale } from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { ChatThread } from '../types/chat';

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string | null;
  onThreadSelect: (threadId: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export function Sidebar({ 
  threads, 
  activeThreadId, 
  onThreadSelect, 
  onNewChat,
  isOpen,
  onToggle 
}: SidebarProps) {
  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  const groupThreadsByDate = (threads: ChatThread[]) => {
    const groups: { [key: string]: ChatThread[] } = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Older': []
    };

    threads.forEach(thread => {
      const date = formatDate(thread.timestamp);
      if (date === 'Today') groups['Today'].push(thread);
      else if (date === 'Yesterday') groups['Yesterday'].push(thread);
      else if (date.includes('days ago')) groups['Previous 7 Days'].push(thread);
      else groups['Older'].push(thread);
    });

    return groups;
  };

  const groupedThreads = groupThreadsByDate(threads);

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-72 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-transform duration-200 ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 flex items-center justify-center">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <h1 className="font-semibold text-lg">LegalGPT</h1>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="md:hidden"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <Button
            onClick={onNewChat}
            className="w-full justify-start gap-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
          >
            <Plus className="w-4 h-4" />
            New Legal Query
          </Button>
        </div>

        {/* Chat Threads */}
        <ScrollArea className="flex-1 px-3">
          <div className="space-y-6 py-2">
            {Object.entries(groupedThreads).map(([group, groupThreads]) => {
              if (groupThreads.length === 0) return null;
              
              return (
                <div key={group}>
                  <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-500 uppercase tracking-wide mb-2 px-2">
                    {group}
                  </h3>
                  <div className="space-y-1">
                    {groupThreads.map((thread) => (
                      <button
                        key={thread.id}
                        onClick={() => onThreadSelect(thread.id)}
                        className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
                          activeThreadId === thread.id
                            ? 'bg-gray-100 dark:bg-gray-800'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-900'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <MessageSquare className="w-4 h-4 mt-0.5 text-gray-500 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                              {thread.title}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500 truncate mt-0.5">
                              {thread.preview}
                            </p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-500 text-center">
            LegalGPT for Law Students
          </p>
        </div>
      </aside>
    </>
  );
}
