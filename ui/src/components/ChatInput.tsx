import { ArrowUp, FilePlus2, Mic, Paperclip, Plus, Square } from 'lucide-react';
import { useEffect, useRef, useState, type ChangeEvent, type DragEvent, type KeyboardEvent } from 'react';
import { useChat } from '../context/ChatContext';
import { fileToAttachment } from '../utils';
import { AttachmentPreview } from './AttachmentPreview';

export function ChatInput() {
  const { input, setInput, attachments, addAttachments, removeAttachment, sendMessage, isGenerating, stopGenerating, selectedModel, apiStatus } = useChat();
  const textarea = useRef<HTMLTextAreaElement>(null); const fileInput = useRef<HTMLInputElement>(null);
  const [mobileMenu, setMobileMenu] = useState(false); const [dragging, setDragging] = useState(false);
  useEffect(() => { if (!textarea.current) return; textarea.current.style.height = 'auto'; textarea.current.style.height = Math.min(textarea.current.scrollHeight, 180) + 'px'; }, [input]);
  useEffect(() => { if (input) textarea.current?.focus(); }, [input]);
  const addFiles = (files: FileList | null) => { if (files) addAttachments(Array.from(files).map(fileToAttachment)); };
  const keyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void sendMessage(); } };
  const drop = (event: DragEvent) => { event.preventDefault(); setDragging(false); addFiles(event.dataTransfer.files); };
  const disabled = (!input.trim() && !attachments.length) || !selectedModel || apiStatus !== 'online';
  return <div className="composer-area"><div className={'chat-input ' + (dragging ? 'is-dragging' : '')} onDragEnter={(e) => { e.preventDefault(); setDragging(true); }} onDragOver={(e) => e.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={drop}>
    {attachments.length > 0 && <div className="attachment-list">{attachments.map((item) => <AttachmentPreview key={item.id} attachment={item} onRemove={() => removeAttachment(item.id)} />)}</div>}
    {dragging && <div className="drop-overlay"><FilePlus2 size={24} />Thả PDF để tải lên RAG</div>}
    <label htmlFor="message" className="sr-only">Nhắn tin cho chatbot</label><textarea id="message" ref={textarea} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={keyDown} rows={1} placeholder={apiStatus === 'online' ? 'Hỏi tài liệu hoặc trò chuyện với chatbot' : 'Đang chờ kết nối backend…'} disabled={apiStatus !== 'online'} />
    <div className="composer-tools"><div className="tool-group">
      <button className="icon-button plus-mobile" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Thêm nội dung"><Plus size={20} /></button>
      <div className={'secondary-tools ' + (mobileMenu ? 'is-open' : '')}><button className="tool-button" onClick={() => fileInput.current?.click()}><Paperclip size={18} /><span>Tải PDF</span></button></div>
    </div><div className="send-group"><button className="icon-button" aria-label="Nhập bằng giọng nói" disabled title="Backend chưa hỗ trợ giọng nói"><Mic size={19} /></button>{isGenerating ? <button className="send-button" onClick={stopGenerating} aria-label="Dừng yêu cầu"><Square size={15} fill="currentColor" /></button> : <button className="send-button" onClick={() => void sendMessage()} disabled={disabled} aria-label="Gửi tin nhắn"><ArrowUp size={19} /></button>}</div></div>
    <input ref={fileInput} hidden type="file" accept=".pdf,application/pdf" multiple onChange={(e: ChangeEvent<HTMLInputElement>) => addFiles(e.target.files)} />
  </div><p className="disclaimer">Câu trả lời có thể mắc lỗi. Hãy đối chiếu nguồn và thông tin quan trọng.</p></div>;
}
