import { Copy, Pencil, RotateCcw, ThumbsDown, ThumbsUp, Volume2 } from 'lucide-react';
import { useState } from 'react';
export function MessageActions({ content, onRegenerate, onEdit }: { content: string; onRegenerate: () => void; onEdit: () => void }) {
  const [reaction, setReaction] = useState<'up' | 'down' | null>(null);
  const actions = [
    { label: 'Sao chép', icon: Copy, action: () => navigator.clipboard.writeText(content) },
    { label: 'Thích', icon: ThumbsUp, action: () => setReaction('up'), active: reaction === 'up' },
    { label: 'Không thích', icon: ThumbsDown, action: () => setReaction('down'), active: reaction === 'down' },
    { label: 'Đọc thành tiếng', icon: Volume2, action: () => { speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance(content)); } },
    { label: 'Tạo lại', icon: RotateCcw, action: onRegenerate },
    { label: 'Chỉnh sửa yêu cầu', icon: Pencil, action: onEdit },
  ];
  return <div className="message-actions">{actions.map(({ label, icon: Icon, action, active }) => <button key={label} onClick={action} className={active ? 'is-active' : ''} aria-label={label} title={label}><Icon size={17} /></button>)}</div>;
}
