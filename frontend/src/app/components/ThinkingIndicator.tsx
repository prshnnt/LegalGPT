import { Loader2, Search, Brain, Check } from 'lucide-react';
import { ThinkingStage } from '../types/chat';

interface ThinkingIndicatorProps {
  stages: ThinkingStage[];
  isActive?: boolean;
}

export function ThinkingIndicator({ stages, isActive }: ThinkingIndicatorProps) {
  if (!stages.length && !isActive) return null;

  const getIcon = (type: ThinkingStage['type']) => {
    switch (type) {
      case 'thinking':
        return <Brain className="w-4 h-4" />;
      case 'searching':
        return <Search className="w-4 h-4" />;
      case 'analyzing':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'complete':
        return <Check className="w-4 h-4" />;
      default:
        return <Loader2 className="w-4 h-4 animate-spin" />;
    }
  };

  const getLabel = (type: ThinkingStage['type']) => {
    switch (type) {
      case 'thinking':
        return 'Thinking';
      case 'searching':
        return 'Searching the web';
      case 'analyzing':
        return 'Analyzing';
      case 'complete':
        return 'Complete';
      default:
        return 'Processing';
    }
  };

  return (
    <div className="flex flex-col gap-2 my-3">
      {stages.map((stage) => (
        <div
          key={stage.id}
          className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
        >
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800">
            {getIcon(stage.type)}
          </div>
          <span>{getLabel(stage.type)}</span>
          {stage.content && (
            <span className="text-gray-500 dark:text-gray-500">• {stage.content}</span>
          )}
        </div>
      ))}
      {isActive && stages.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800">
            <Loader2 className="w-4 h-4 animate-spin" />
          </div>
          <span>Thinking...</span>
        </div>
      )}
    </div>
  );
}
