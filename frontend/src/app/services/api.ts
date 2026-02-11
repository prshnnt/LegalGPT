// API Service - Backend integration for LegalGPT

import {
  Message,
  Attachment,
  ChatSettings,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
  ChatThreadResponse,
  ChatMessageResponse,
  ChatHistoryResponse,
  StreamChunk,
} from '../types/chat';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Token management
export const TokenManager = {
  getToken(): string | null {
    return localStorage.getItem('token');
  },
  
  setToken(token: string): void {
    localStorage.setItem('token', token);
  },
  
  clearToken(): void {
    localStorage.removeItem('token');
  },
  
  getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  },
};

// ===== AUTH ROUTES =====

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

export async function register(credentials: RegisterRequest): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

// ===== THREAD MANAGEMENT =====

export async function createThread(title: string = 'New Chat'): Promise<ChatThreadResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/threads`, {
    method: 'POST',
    headers: TokenManager.getAuthHeaders(),
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error('Failed to create thread');
  }

  return response.json();
}

export async function getThreads(): Promise<ChatThreadResponse[]> {
  const response = await fetch(`${API_BASE_URL}/chat/threads`, {
    headers: TokenManager.getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch threads');
  }

  return response.json();
}

export async function getThreadHistory(threadId: number | string): Promise<ChatHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/threads/${threadId}`, {
    headers: TokenManager.getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch thread history');
  }

  return response.json();
}

export async function deleteThread(threadId: number | string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/threads/${threadId}`, {
    method: 'DELETE',
    headers: TokenManager.getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete thread');
  }
}

// ===== MESSAGES =====

export async function getMessages(threadId: number | string): Promise<ChatMessageResponse[]> {
  const response = await fetch(`${API_BASE_URL}/chat/threads/${threadId}/messages`, {
    headers: TokenManager.getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch messages');
  }

  return response.json();
}

/**
 * Send a message and stream the response using Server-Sent Events (SSE)
 * Returns an async generator that yields StreamChunk events
 */
export async function* sendMessageStream(
  threadId: number | string,
  content: string
): AsyncGenerator<StreamChunk, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/chat/threads/${threadId}/messages`, {
    method: 'POST',
    headers: TokenManager.getAuthHeaders(),
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events end with double newline
      const events = buffer.split('\n\n');
      buffer = events.pop() || ''; // keep incomplete chunk

      for (const event of events) {
        const line = event.trim();

        if (!line || !line.startsWith('data:')) continue;

        try {
          const jsonStr = line.replace(/^data:\s*/, '');
          const chunk: StreamChunk = JSON.parse(jsonStr);
          yield chunk;
        } catch (e) {
          console.error('Invalid SSE chunk', e, line);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Upload a file to your backend (e.g., legal documents, case files)
 * TODO: Implement file upload endpoint if needed
 */
export async function uploadFile(file: File): Promise<Attachment> {
  // Placeholder implementation - replace with your file upload API
  // Example: const formData = new FormData(); formData.append('file', file);
  // fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData, headers: TokenManager.getAuthHeaders() })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id: Math.random().toString(36).substring(7),
        name: file.name,
        size: file.size,
        type: file.type,
        url: URL.createObjectURL(file) // Temporary URL for preview
      });
    }, 500);
  });
}

/**
 * Perform a web search for legal information
 * TODO: Implement if you have a separate search endpoint
 */
export async function performWebSearch(query: string): Promise<any[]> {
  // Placeholder implementation - this might be handled by your agent's tool calls
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { title: 'Legal Database Result 1', url: 'https://example.com', snippet: 'Replace with real legal search API' },
        { title: 'Case Law Reference', url: 'https://example.com', snippet: 'Integrate your legal search here' }
      ]);
    }, 1000);
  });
}
