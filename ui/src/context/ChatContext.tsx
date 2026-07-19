import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { api } from '../api';
import type { Attachment, Conversation, Message, ModelChoice, Theme } from '../types';
import { id } from '../utils';

const THEME_KEY = 'lumen-chat.theme.v1';
const MODEL_KEY = 'lumen-chat.model.v1';
const ALIAS_KEY = 'lumen-chat.session-aliases.v1';

type ApiStatus = 'checking' | 'online' | 'offline';
type Notice = { type: 'success' | 'error'; text: string } | null;

interface ChatState {
  conversations: Conversation[]; active: Conversation; activeId: string;
  input: string; setInput: (value: string) => void; attachments: Attachment[];
  addAttachments: (items: Attachment[]) => void; removeAttachment: (id: string) => void;
  isGenerating: boolean; isLoadingSession: boolean; isUploading: boolean;
  theme: Theme; toggleTheme: () => void; sidebarCollapsed: boolean; setSidebarCollapsed: (value: boolean) => void;
  drawerOpen: boolean; setDrawerOpen: (value: boolean) => void;
  models: ModelChoice[]; selectedModel: ModelChoice | null; setSelectedModel: (value: ModelChoice) => void;
  documents: string[]; refreshDocuments: () => Promise<void>; deleteDocument: (name: string) => Promise<void>;
  apiStatus: ApiStatus; startupTimings: Record<string, number>; notice: Notice; clearNotice: () => void;
  newChat: () => void; selectConversation: (id: string) => Promise<void>;
  renameConversation: (id: string, title: string) => void; deleteConversation: (id: string) => Promise<void>;
  sendMessage: (content?: string) => Promise<void>; stopGenerating: () => void;
  editMessage: (id: string) => void; regenerate: (id?: string) => Promise<void>;
}

const blankConversation = (sessionId = id()): Conversation => ({
  id: sessionId, title: 'Cuộc trò chuyện mới', group: 'Hôm nay', messages: [], updatedAt: new Date().toISOString(),
});
const ChatContext = createContext<ChatState | null>(null);

function aliases(): Record<string, string> {
  try { return JSON.parse(localStorage.getItem(ALIAS_KEY) || '{}'); } catch { return {}; }
}
function groupFor(date?: string): Conversation['group'] {
  if (!date) return '30 ngày trước';
  const days = (Date.now() - new Date(date).getTime()) / 86400000;
  return days < 1 ? 'Hôm nay' : days <= 7 ? '7 ngày trước' : '30 ngày trước';
}
function errorText(error: unknown) { return error instanceof Error ? error.message : 'Đã xảy ra lỗi không xác định.'; }

export function ChatProvider({ children }: { children: ReactNode }) {
  const first = useRef(blankConversation());
  const [conversations, setConversations] = useState<Conversation[]>([first.current]);
  const [activeId, setActiveId] = useState(first.current.id);
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem(THEME_KEY) as Theme) || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [models, setModels] = useState<ModelChoice[]>([]);
  const [selectedModel, setSelectedModelState] = useState<ModelChoice | null>(null);
  const [documents, setDocuments] = useState<string[]>([]);
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking');
  const [startupTimings, setStartupTimings] = useState<Record<string, number>>({});
  const [notice, setNotice] = useState<Notice>(null);
  const abortRef = useRef<AbortController | null>(null);

  const active = useMemo(() => conversations.find((item) => item.id === activeId) || conversations[0] || first.current, [conversations, activeId]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.style.colorScheme = theme; localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const controller = new AbortController();
    const wait = () => new Promise<void>((resolve) => window.setTimeout(resolve, 1500));

    async function bootstrap() {
      while (!controller.signal.aborted) {
        try {
          const readiness = await api.ready(controller.signal);
          setStartupTimings(readiness.timings_ms);
          if (!readiness.ready) {
            setApiStatus(readiness.status === 'failed' ? 'offline' : 'checking');
            if (readiness.error) setNotice({ type: 'error', text: 'Warmup thất bại: ' + readiness.error });
            await wait(); continue;
          }

          const [modelData, sessionData] = await Promise.all([api.models(), api.sessions()]);
          setModels(modelData.models);
          const saved = localStorage.getItem(MODEL_KEY);
          setSelectedModelState(modelData.models.find((item) => item.provider + ':' + item.model === saved)
            || modelData.models.find((item) => item.provider === modelData.default_provider && item.model === modelData.default_model)
            || modelData.models[0] || null);
          const names = aliases();
          const serverItems = sessionData.sessions.map((item): Conversation => ({
            id: item.session_id,
            title: names[item.session_id] || item.topic || item.last_user_message || item.session_id,
            group: groupFor(item.last_accessed), messages: [], updatedAt: item.last_accessed || new Date().toISOString(),
          }));
          setApiStatus('online');
          if (serverItems.length) {
            setConversations(serverItems); setActiveId(serverItems[0].id); void loadSession(serverItems[0].id);
          }
          return;
        } catch (error) {
          if ((error as Error).name === 'AbortError') return;
          setApiStatus('checking');
          await wait();
        }
      }
    }

    void bootstrap();
    return () => controller.abort();
  }, []);

  const update = (conversationId: string, fn: (item: Conversation) => Conversation) =>
    setConversations((items) => items.map((item) => item.id === conversationId ? fn(item) : item));

  async function loadSession(sessionId: string) {
    setIsLoadingSession(true);
    try {
      const detail = await api.session(sessionId);
      const names = aliases();
      const messages: Message[] = detail.messages.map((message) => ({
        id: id(), role: message.role === 'user' ? 'user' : 'assistant', content: message.content, createdAt: detail.last_accessed || new Date().toISOString(),
      }));
      update(sessionId, (item) => ({ ...item, title: names[sessionId] || detail.topic || detail.last_user_message || item.title, messages }));
    } catch (error) { setNotice({ type: 'error', text: 'Không tải được hội thoại: ' + errorText(error) }); }
    finally { setIsLoadingSession(false); }
  }

  async function refreshSessions(preferredId?: string) {
    const data = await api.sessions(); const names = aliases();
    setConversations((current) => {
      const draft = current.find((item) => item.id === preferredId);
      const next = data.sessions.map((item): Conversation => {
        const local = current.find((candidate) => candidate.id === item.session_id);
        return { id: item.session_id, title: names[item.session_id] || item.topic || item.last_user_message || item.session_id, group: groupFor(item.last_accessed), messages: local?.messages || [], updatedAt: item.last_accessed || new Date().toISOString() };
      });
      if (draft && !next.some((item) => item.id === draft.id)) next.unshift(draft);
      return next.length ? next : current;
    });
  }

  function newChat() {
    stopGenerating(); const conversation = blankConversation();
    setConversations((items) => [conversation, ...items]); setActiveId(conversation.id); setInput(''); setAttachments([]); setDrawerOpen(false);
  }
  async function selectConversation(conversationId: string) { setActiveId(conversationId); setDrawerOpen(false); await loadSession(conversationId); }
  function renameConversation(conversationId: string, title: string) {
    if (!title.trim()) return; const names = aliases(); names[conversationId] = title.trim(); localStorage.setItem(ALIAS_KEY, JSON.stringify(names));
    update(conversationId, (item) => ({ ...item, title: title.trim() }));
  }
  async function deleteConversation(conversationId: string) {
    try { await api.deleteSession(conversationId); }
    catch (error) { if (!conversations.find((item) => item.id === conversationId)?.messages.length) { /* unsaved draft */ } else { setNotice({ type: 'error', text: 'Không xóa được hội thoại: ' + errorText(error) }); return; } }
    const next = conversations.filter((item) => item.id !== conversationId);
    if (next.length) { setConversations(next); setActiveId(next[0].id); if (next[0].messages.length === 0) void loadSession(next[0].id); }
    else newChat();
  }

  async function refreshDocuments() {
    try { setDocuments((await api.documents()).documents); }
    catch (error) { setNotice({ type: 'error', text: 'Không tải được tài liệu: ' + errorText(error) }); }
  }
  async function deleteDocument(name: string) {
    try { await api.deleteDocument(name); await refreshDocuments(); setNotice({ type: 'success', text: 'Đã xóa tài liệu ' + name }); }
    catch (error) { setNotice({ type: 'error', text: 'Không xóa được tài liệu: ' + errorText(error) }); }
  }
  function setSelectedModel(value: ModelChoice) { setSelectedModelState(value); localStorage.setItem(MODEL_KEY, value.provider + ':' + value.model); }

  async function sendMessage(content = input) {
    const value = content.trim();
    if ((!value && !attachments.length) || isGenerating || !active || !selectedModel) return;
    const invalid = attachments.find((item) => !item.name.toLowerCase().endsWith('.pdf'));
    if (invalid) { setNotice({ type: 'error', text: 'Backend hiện chỉ hỗ trợ tải lên tệp PDF.' }); return; }
    const conversationId = active.id; const sentAttachments = [...attachments];
    const user: Message = { id: id(), role: 'user', content: value || 'Hãy phân tích tài liệu vừa tải lên.', attachments: sentAttachments, createdAt: new Date().toISOString() };
    update(conversationId, (item) => ({ ...item, title: item.messages.length ? item.title : (value || sentAttachments[0]?.name || '').slice(0, 42), messages: [...item.messages, user], updatedAt: new Date().toISOString() }));
    setInput(''); setAttachments([]); setIsGenerating(true); abortRef.current = new AbortController();
    try {
      if (sentAttachments.length) {
        setIsUploading(true);
        for (const attachment of sentAttachments) if (attachment.file) await api.upload(attachment.file);
        await refreshDocuments(); setIsUploading(false);
      }
      const result = await api.chat({ message: user.content, session_id: conversationId, provider: selectedModel.provider, model: selectedModel.model, top_k: 5 }, abortRef.current.signal);
      const assistant: Message = { id: id(), role: 'assistant', content: result.answer, sources: result.sources, latencyMs: result.latency_ms, createdAt: new Date().toISOString() };
      update(conversationId, (item) => ({ ...item, messages: [...item.messages, assistant], updatedAt: new Date().toISOString() }));
      setApiStatus('online'); await refreshSessions(conversationId);
    } catch (error) {
      if ((error as Error).name !== 'AbortError') { setNotice({ type: 'error', text: 'Gửi tin nhắn thất bại: ' + errorText(error) }); }
    } finally { setIsGenerating(false); setIsUploading(false); abortRef.current = null; }
  }

  function stopGenerating() { abortRef.current?.abort(); abortRef.current = null; setIsGenerating(false); setIsUploading(false); }
  function editMessage(messageId: string) { const message = active.messages.find((item) => item.id === messageId); if (message) setInput(message.content); }
  async function regenerate(messageId?: string) {
    const index = messageId ? active.messages.findIndex((item) => item.id === messageId) : active.messages.length;
    const prompt = [...active.messages.slice(0, index < 0 ? undefined : index)].reverse().find((item) => item.role === 'user')?.content;
    if (prompt) await sendMessage(prompt);
  }

  const value: ChatState = {
    conversations, active, activeId, input, setInput, attachments,
    addAttachments: (items) => setAttachments((current) => [...current, ...items]),
    removeAttachment: (attachmentId) => setAttachments((items) => items.filter((item) => item.id !== attachmentId)),
    isGenerating, isLoadingSession, isUploading, theme, toggleTheme: () => setTheme((value) => value === 'light' ? 'dark' : 'light'),
    sidebarCollapsed, setSidebarCollapsed, drawerOpen, setDrawerOpen, models, selectedModel, setSelectedModel,
    documents, refreshDocuments, deleteDocument, apiStatus, startupTimings, notice, clearNotice: () => setNotice(null),
    newChat, selectConversation, renameConversation, deleteConversation, sendMessage, stopGenerating, editMessage, regenerate,
  };
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const value = useContext(ChatContext); if (!value) throw new Error('useChat must be used inside ChatProvider'); return value;
}
