import { Scale, Globe, FileText, BookOpen } from 'lucide-react';

interface EmptyStateProps {
  onExampleClick: (text: string) => void;
}

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  const examples = [
    {
      icon: <BookOpen className="w-5 h-5" />,
      text: "Explain Article 21 of Constitution",
      prompt: "Can you explain Article 21 of the Constitution of India in detail, including its significance and landmark judgments?"
    },
    {
      icon: <Scale className="w-5 h-5" />,
      text: "Difference between BNS and IPC",
      prompt: "What are the key differences between Bharatiya Nyaya Sanhita (BNS) and Indian Penal Code (IPC)?"
    },
    {
      icon: <Globe className="w-5 h-5" />,
      text: "Recent Supreme Court judgments",
      prompt: "What are some recent important Supreme Court judgments? Please search the web for latest information."
    },
    {
      icon: <FileText className="w-5 h-5" />,
      text: "Analyze legal document",
      prompt: "I have a legal document that I need help understanding. I'll upload it and need you to explain the key legal points."
    }
  ];

  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-3xl w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-600 to-orange-600 flex items-center justify-center">
            <Scale className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-semibold mb-2 text-gray-900 dark:text-gray-100">
            Welcome to LegalGPT
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Your AI assistant for studying Indian law - Constitution, BNS, BNSS, case laws & more
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => onExampleClick(example.prompt)}
              className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-amber-500 dark:hover:border-amber-500 hover:bg-gray-50 dark:hover:bg-gray-900 transition-all text-left group"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 group-hover:bg-amber-100 dark:group-hover:bg-amber-900/30 flex items-center justify-center transition-colors">
                <div className="text-gray-600 dark:text-gray-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                  {example.icon}
                </div>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {example.text}
                </p>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-8 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-sm text-amber-900 dark:text-amber-200">
            <strong>Note:</strong> LegalGPT is an educational tool for law students. Always verify legal information with official sources and consult qualified legal professionals for legal advice.
          </p>
        </div>
      </div>
    </div>
  );
}
