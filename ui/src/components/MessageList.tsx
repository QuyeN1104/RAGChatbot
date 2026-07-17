import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { BrandMark } from './BrandMark';
import { MessageItem } from './MessageItem';
export function MessageList() {
  const { active, isGenerating, isLoadingSession, isUploading } = useChat(); const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [active.messages, isGenerating]);
  return <div className="message-scroll"><div className="message-list">{isLoadingSession && !active.messages.length ? <div className="session-loading"><Loader2 size={22} className="spin" />Đang tải lịch sử…</div> : active.messages.map((message) => <MessageItem key={message.id} message={message} />)}{isGenerating && <div className="assistant-message typing-row" role="status" aria-label="Chatbot đang trả lời"><div className="assistant-avatar"><BrandMark small /></div><div className="typing-indicator"><span /><span /><span /></div><small className="generation-label">{isUploading ? 'Đang xử lý PDF…' : 'Đang truy vấn RAG…'}</small></div>}<div ref={end} /></div></div>;
}
