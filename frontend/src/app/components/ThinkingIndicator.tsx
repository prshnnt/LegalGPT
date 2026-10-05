import { Loader2, Search, Brain, Check } from 'lucide-react';
import type { ThinkingStage } from '../types/chat';

interface ThinkingIndicatorProps {
  stages: ThinkingStage[];
  isActive?: boolean;
}

const ICONS: Record<ThinkingStage['type'], React.ReactNode> = {
  thinking: <Brain size={12} />,
  searching: <Search size={12} />,
  analyzing: <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />,
  complete: <Check size={12} />,
};

const LABELS: Record<ThinkingStage['type'], string> = {
  thinking: 'Thinking',
  searching: 'Searching the web',
  analyzing: 'Analyzing',
  complete: 'Complete',
};

export function ThinkingIndicator({ stages, isActive }: ThinkingIndicatorProps) {
  if (!stages.length && !isActive) return null;

  return (
    <>
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
      <div className="thinking-wrap">
        {stages.map((s) => (
          <div key={s.id} className="thinking-row">
            <div className="thinking-icon-wrap">{ICONS[s.type] ?? <Loader2 size={12} />}</div>
            <span>{LABELS[s.type] ?? 'Processing'}</span>
            {s.content && (
              <span style={{ color: 'rgba(255,255,255,0.30)' }}>• {s.content}</span>
            )}
          </div>
        ))}

        {isActive && stages.length === 0 && (
          <div className="thinking-row">
            <div className="thinking-icon-wrap">
              <div className="thinking-pulse">
                <span /><span /><span />
              </div>
            </div>
            <span>Thinking…</span>
          </div>
        )}
      </div>
    </>
  );
}
