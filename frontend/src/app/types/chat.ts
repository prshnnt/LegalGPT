// Chat message types for LegalGPT

export interface Message {
  id: string | number;
  role: 'user' | 'assistant' | 'human' | 'ai';
  content: string;
  timestamp: Date;
  created_at?: string;
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
  id: string | number;
  title: string;
  preview?: string;
  timestamp?: Date;
  created_at?: string;
  updated_at?: string;
  messageCount?: number;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  created_at: string;
}

// Backend response types
export interface ChatThreadResponse {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageResponse {
  id: number;
  role: 'human' | 'ai';
  content: string;
  created_at: string;
}

export interface ChatHistoryResponse {
  thread: ChatThreadResponse;
  messages: ChatMessageResponse[];
}

// SSE Stream event types
export interface StreamChunk {
  type: 'content' | 'tool_call' | 'tool_result' | 'error' | 'start' | 'end';
  content?: string;
  tool_name?: string;
  tool_input?: any;
  tool_output?: string;
  session_id?: number;
  checkpointer_metadata?: any;
}