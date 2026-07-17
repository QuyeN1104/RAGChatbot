export type Role = 'user' | 'assistant';
export type ConversationGroup = 'Hôm nay' | '7 ngày trước' | '30 ngày trước';
export interface Attachment { id: string; name: string; type: string; size: number; preview?: string; file?: File; }
export interface Source { source: string; page?: number | string | null; }
export interface Message { id: string; role: Role; content: string; createdAt: string; attachments?: Attachment[]; sources?: Source[]; latencyMs?: number; }
export interface Conversation { id: string; title: string; group: ConversationGroup; messages: Message[]; updatedAt: string; }
export interface ModelChoice { provider: string; model: string; label: string; }
export type Theme = 'light' | 'dark';
