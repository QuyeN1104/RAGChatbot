import { Check, MoreHorizontal, Pencil, Trash2, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { Conversation } from '../types';

interface Props { conversation: Conversation; active: boolean; onSelect: () => void; onRename: (title: string) => void; onDelete: () => void; }
export function SidebarConversationItem({ conversation, active, onSelect, onRename, onDelete }: Props) {
  const [menuOpen, setMenuOpen] = useState(false); const [renaming, setRenaming] = useState(false); const [title, setTitle] = useState(conversation.title); const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { const close = (event: MouseEvent) => { if (!ref.current?.contains(event.target as Node)) setMenuOpen(false); }; document.addEventListener('mousedown', close); return () => document.removeEventListener('mousedown', close); }, []);
  const save = () => { onRename(title); setRenaming(false); setMenuOpen(false); };
  if (renaming) return <div className="conversation-edit"><input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') save(); if (e.key === 'Escape') setRenaming(false); }} aria-label="Tên cuộc trò chuyện" /><button onClick={save} aria-label="Lưu"><Check size={16} /></button><button onClick={() => setRenaming(false)} aria-label="Hủy"><X size={16} /></button></div>;
  return <div ref={ref} className={'conversation-item ' + (active ? 'is-active' : '')}>
    <button className="conversation-select" onClick={onSelect}><span>{conversation.title}</span></button>
    <button className="more-button" onClick={() => setMenuOpen((value) => !value)} aria-label={'Tùy chọn cho ' + conversation.title} aria-expanded={menuOpen}><MoreHorizontal size={18} /></button>
    {menuOpen && <div className="context-menu"><button onClick={() => setRenaming(true)}><Pencil size={16} />Đổi tên</button><button className="danger" onClick={onDelete}><Trash2 size={16} />Xóa</button></div>}
  </div>;
}
