import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bot,
  CheckCircle2,
  Eraser,
  FileText,
  Loader2,
  MessageSquarePlus,
  Plus,
  RefreshCw,
  Send,
  Server,
  Trash2,
  Upload,
  User,
} from 'lucide-react';
import './styles.css';

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const API_BASE_URL = rawApiBaseUrl.replace(/\/+$/, '');
const ACTIVE_KEY = 'rag-chat.active-session.v2';

function createSessionState(sessionId = crypto.randomUUID()) {
  return {
    id: sessionId,
    title: 'New chat',
    messages: [],
    isPersisted: false,
  };
}

function formatError(error) {
  if (!error) return 'Request failed';
  if (typeof error.detail === 'string') return error.detail;
  if (Array.isArray(error.detail)) return error.detail.map((item) => item.msg || item.type).join(', ');
  return error.message || 'Request failed';
}

async function readApiResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const text = await response.text();

  if (contentType.includes('application/json')) {
    try {
      return JSON.parse(text);
    } catch {
      throw { detail: 'API returned invalid JSON.' };
    }
  }

  const trimmed = text.trim();
  if (trimmed.startsWith('<!doctype html') || trimmed.startsWith('<html')) {
    throw {
      detail: 'API returned HTML instead of JSON. Check the Vite proxy or VITE_API_BASE_URL.',
    };
  }

  if (trimmed) {
    throw { detail: trimmed };
  }

  throw { detail: 'HTTP ' + response.status };
}

function titleForSession(session) {
  return session.topic || session.last_user_message || session.session_id;
}

function App() {
  const [serverSessions, setServerSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(() => createSessionState(localStorage.getItem(ACTIVE_KEY) || undefined));
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [documents, setDocuments] = useState([]);
  const [isRefreshingDocs, setIsRefreshingDocs] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const fileInputRef = useRef(null);
  const transcriptRef = useRef(null);

  const activeSummary = useMemo(
    () => serverSessions.find((session) => session.session_id === activeSession.id),
    [serverSessions, activeSession.id],
  );

  useEffect(() => {
    localStorage.setItem(ACTIVE_KEY, activeSession.id);
  }, [activeSession.id]);

  useEffect(() => {
    checkHealth();
    refreshDocuments();
    refreshServerSessions().then((sessions) => {
      const activeId = localStorage.getItem(ACTIVE_KEY);
      if (activeId && sessions.some((session) => session.session_id === activeId)) {
        loadSession(activeId);
      } else if (sessions[0]) {
        loadSession(sessions[0].session_id);
      }
    });
  }, []);

  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight, behavior: 'smooth' });
  }, [activeSession.messages, isSending]);

  async function checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      setApiStatus(response.ok ? 'online' : 'offline');
    } catch {
      setApiStatus('offline');
    }
  }

  function startSession() {
    setActiveSession(createSessionState());
    setInput('');
  }

  async function refreshServerSessions() {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`);
      const payload = await readApiResponse(response);
      if (!response.ok) throw payload;
      const sessions = payload.sessions || [];
      setServerSessions(sessions);
      return sessions;
    } catch {
      setServerSessions([]);
      return [];
    }
  }

  async function loadSession(sessionId) {
    setIsLoadingSession(true);
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionId)}`);
      const payload = await readApiResponse(response);
      if (!response.ok) throw payload;
      setActiveSession({
        id: payload.session_id,
        title: payload.topic || payload.last_user_message || payload.session_id,
        messages: (payload.messages || []).map((message) => ({
          id: crypto.randomUUID(),
          role: message.role,
          content: message.content,
          sources: [],
        })),
        isPersisted: true,
      });
    } catch (error) {
      setUploadStatus({ type: 'error', text: formatError(error) });
    } finally {
      setIsLoadingSession(false);
    }
  }

  async function clearCurrentSession() {
    if (!activeSession) return;
    await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(activeSession.id)}`, { method: 'DELETE' }).catch(() => null);
    setActiveSession((session) => ({ ...session, messages: [], isPersisted: false }));
    refreshServerSessions();
  }

  async function refreshDocuments() {
    setIsRefreshingDocs(true);
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      const payload = await readApiResponse(response);
      if (!response.ok) throw payload;
      setDocuments(payload.documents || []);
    } catch {
      setDocuments([]);
    } finally {
      setIsRefreshingDocs(false);
    }
  }

  async function deleteDocument(sourceName) {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(sourceName)}`, { method: 'DELETE' });
      const payload = await readApiResponse(response);
      if (!response.ok) throw payload;
      setUploadStatus({ type: 'success', text: payload.message });
      refreshDocuments();
    } catch (error) {
      setUploadStatus({ type: 'error', text: formatError(error) });
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending || !activeSession) return;

    const sessionId = activeSession.id;
    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      sources: [],
    };

    setActiveSession((session) => ({
      ...session,
      title: session.messages.length === 0 ? message.slice(0, 48) : session.title,
      messages: [...session.messages, userMessage],
    }));
    setInput('');
    setIsSending(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId, top_k: 5 }),
      });
      const payload = await readApiResponse(response);
      if (!response.ok) throw payload;

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: payload.answer,
        sources: payload.sources || [],
      };
      setActiveSession((session) => ({
        ...session,
        id: payload.session_id,
        isPersisted: true,
        messages: [...session.messages, assistantMessage],
      }));
      refreshServerSessions();
    } catch (error) {
      setActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: formatError(error),
            sources: [],
            isError: true,
          },
        ],
      }));
    } finally {
      setIsSending(false);
    }
  }

  async function uploadPdf(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData });
      const payload = await readApiResponse(response);
      if (!response.ok) throw payload;
      setUploadStatus({
        type: 'success',
        text: `${payload.filename} ingested: ${payload.pages} pages, ${payload.chunks} chunks`,
      });
      refreshDocuments();
    } catch (error) {
      setUploadStatus({ type: 'error', text: formatError(error) });
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark"><Bot size={22} /></div>
          <div>
            <h1>RAG Chat</h1>
            <p>Document assistant</p>
          </div>
        </div>

        <button className="primary-action" onClick={startSession} type="button">
          <MessageSquarePlus size={18} /> New chat
        </button>

        <div className="side-section server-sessions main-history">
          <div className="section-heading">
            <span>Chat sessions</span>
            <button type="button" onClick={refreshServerSessions} aria-label="Refresh sessions">
              <RefreshCw size={15} />
            </button>
          </div>
          <div className="session-list" aria-label="Chat sessions">
            {serverSessions.length === 0 && !activeSession.isPersisted ? (
              <button className="session-item active" type="button">
                <span>{activeSession.title}</span>
              </button>
            ) : (
              <>
                {!activeSession.isPersisted && (
                  <button className="session-item active" type="button">
                    <span>{activeSession.title}</span>
                  </button>
                )}
                {serverSessions.map((session) => (
                  <button
                    key={session.session_id}
                    className={`session-item ${session.session_id === activeSession.id ? 'active' : ''}`}
                    onClick={() => loadSession(session.session_id)}
                    type="button"
                  >
                    <span>{titleForSession(session)}</span>
                    <small>{session.message_count}</small>
                  </button>
                ))}
              </>
            )}
          </div>
        </div>

        <div className="side-section">
          <div className="section-heading">
            <span>Documents</span>
            <button type="button" onClick={refreshDocuments} aria-label="Refresh documents">
              <RefreshCw className={isRefreshingDocs ? 'spin' : ''} size={15} />
            </button>
          </div>
          <div className="document-list">
            {documents.length === 0 ? (
              <span className="muted-row">No documents</span>
            ) : (
              documents.map((document) => (
                <div key={document} className="document-item">
                  <FileText size={15} />
                  <span>{document}</span>
                  <button type="button" onClick={() => deleteDocument(document)} aria-label={`Delete ${document}`}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div className="status-pill">
            <Server size={16} />
            <span className={`status-dot ${apiStatus}`} />
            {apiStatus}
          </div>

          <div className="upload-zone">
            <button className="secondary-action" onClick={clearCurrentSession} disabled={!activeSession?.messages.length} type="button">
              <Eraser size={18} /> Clear chat
            </button>
            {uploadStatus && (
              <span className={`upload-status ${uploadStatus.type}`}>
                {uploadStatus.type === 'success' ? <CheckCircle2 size={16} /> : <FileText size={16} />}
                {uploadStatus.text}
              </span>
            )}
            <input ref={fileInputRef} type="file" accept="application/pdf,.pdf" onChange={uploadPdf} hidden />
            <button className="secondary-action" onClick={() => fileInputRef.current?.click()} disabled={isUploading} type="button">
              {isUploading ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
              Upload PDF
            </button>
          </div>
        </header>

        <section className="chat-panel">
          <div ref={transcriptRef} className="transcript">
            {isLoadingSession ? (
              <div className="empty-state"><Loader2 className="spin" size={28} /><h2>Loading session</h2></div>
            ) : activeSession?.messages.length === 0 ? (
              <div className="empty-state">
                <Plus size={28} />
                <h2>Upload a PDF, then ask questions.</h2>
              </div>
            ) : (
              activeSession.messages.map((message) => (
                <article key={message.id} className={`message ${message.role} ${message.isError ? 'error' : ''}`}>
                  <div className="avatar">{message.role === 'user' ? <User size={17} /> : <Bot size={17} />}</div>
                  <div className="bubble">
                    <p>{message.content}</p>
                    {message.sources?.length > 0 && (
                      <div className="sources">
                        {message.sources.map((source, index) => (
                          <span key={`${source.source}-${source.page}-${index}`} className="source-chip">
                            <FileText size={14} /> {source.source}{source.page !== null && source.page !== undefined ? ` · p.${source.page}` : ''}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))
            )}
            {isSending && (
              <article className="message assistant">
                <div className="avatar"><Bot size={17} /></div>
                <div className="bubble loading"><Loader2 className="spin" size={18} /> Thinking</div>
              </article>
            )}
          </div>

          <form className="composer" onSubmit={sendMessage}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) sendMessage(event);
              }}
              placeholder={activeSummary ? `Ask in ${titleForSession(activeSummary)}...` : 'Ask about the uploaded documents...'}
              rows={1}
            />
            <button type="submit" disabled={!input.trim() || isSending} aria-label="Send message">
              {isSending ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
