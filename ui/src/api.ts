import type { ModelChoice, Source } from './types';

const rawBase = import.meta.env.VITE_API_BASE_URL || '/api';
const API_BASE = rawBase.replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(message: string, public status?: number) { super(message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE + path, init);
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : { detail: await response.text() };
  if (!response.ok) {
    const detail = payload?.detail;
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((item) => item.msg || item.type).join(', ') : 'HTTP ' + response.status;
    throw new ApiError(message, response.status);
  }
  return payload as T;
}

export interface SessionSummary { session_id: string; topic?: string; last_user_message?: string; last_accessed?: string; message_count: number; }
export interface SessionDetail { session_id: string; topic?: string; last_user_message?: string; last_accessed?: string; messages: Array<{ role: string; content: string }>; }
export interface ChatResult { answer: string; sources: Source[]; session_id: string; provider: string; model: string; latency_ms?: number; }
export interface ReadinessResult { status: string; ready: boolean; total_ms: number; timings_ms: Record<string, number>; error?: string; }

export const api = {
  health: (signal?: AbortSignal) => request<{ status: string; version: string }>('/health', { signal }),
  ready: (signal?: AbortSignal) => request<ReadinessResult>('/ready', { signal }),
  models: () => request<{ default_provider: string; default_model: string; models: ModelChoice[] }>('/models'),
  sessions: () => request<{ sessions: SessionSummary[] }>('/sessions'),
  session: (id: string) => request<SessionDetail>('/sessions/' + encodeURIComponent(id)),
  deleteSession: (id: string) => request<{ message: string }>('/sessions/' + encodeURIComponent(id), { method: 'DELETE' }),
  documents: () => request<{ documents: string[] }>('/documents'),
  deleteDocument: (name: string) => request<{ message: string }>('/documents/' + encodeURIComponent(name), { method: 'DELETE' }),
  upload: (file: File) => {
    const form = new FormData(); form.append('file', file);
    return request<{ filename: string; pages: number; chunks: number; message: string }>('/upload', { method: 'POST', body: form });
  },
  chat: (body: { message: string; session_id: string; provider: string; model: string; mode: 'general' | 'rag'; top_k?: number }, signal: AbortSignal) =>
    request<ChatResult>('/chat', { method: 'POST', signal, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
};
