import { Scale, Globe, FileText, BookOpen } from 'lucide-react';
import type { Attachment } from '../types/chat';

const examples = [
  {
    icon: <BookOpen size={16} />,
    text: 'Explain Article 21',
    prompt: 'Can you explain Article 21 of the Constitution of India in detail, including its significance and landmark judgments?',
  },
  {
    icon: <Scale size={16} />,
    text: 'BNS vs IPC differences',
    prompt: 'What are the key differences between Bharatiya Nyaya Sanhita (BNS) and the Indian Penal Code (IPC)?',
  },
  {
    icon: <Globe size={16} />,
    text: 'Recent SC judgments',
    prompt: 'What are some recent important Supreme Court judgments? Please search the web for the latest information.',
  },
  {
    icon: <FileText size={16} />,
    text: 'Analyze a legal document',
    prompt: "I have a legal document that I need help understanding. I'll upload it and need you to explain the key legal points.",
  },
];

interface EmptyStateProps {
  onExampleClick: (text: string, attachments: Attachment[]) => void;
}

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-hero">
        <div className="empty-logo">
          <Scale size={30} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
        </div>
        <h1 className="empty-title">LegalGPT</h1>
        <p className="empty-sub">
          Your AI assistant for studying Indian law —<br />
          Constitution, BNS, BNSS, case laws &amp; more
        </p>
      </div>

      <div className="examples-grid">
        {examples.map((ex, i) => (
          <button
            key={i}
            className="example-card"
            onClick={() => onExampleClick(ex.prompt, [])}
          >
            <div className="example-icon-wrap">{ex.icon}</div>
            <span className="example-text">{ex.text}</span>
          </button>
        ))}
      </div>

      <div className="empty-disclaimer">
        <strong>Note:</strong> LegalGPT is an educational tool for law students.
        Always verify legal information with official sources and consult
        qualified legal professionals for advice.
      </div>
    </div>
  );
}