// Chat message types for LegalGPT

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: Attachment[];
  thinking?: ThinkingStage[];
  isStreaming?: boolean;
}

export interface Attachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
}

export interface ThinkingStage {
  id: string;
  type: 'thinking' | 'searching' | 'analyzing' | 'complete';
  content?: string;
  timestamp: Date;
}

export interface ChatSettings {
  webSearchEnabled: boolean;
  model?: string;
}

export interface ChatThread {
  id: string;
  title: string;
  preview: string;
  timestamp: Date;
  messageCount: number;
}
