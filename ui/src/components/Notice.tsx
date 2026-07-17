import { AlertCircle, CheckCircle2, X } from 'lucide-react';
import { useEffect } from 'react';
import { useChat } from '../context/ChatContext';
export function Notice() {
  const { notice, clearNotice } = useChat();
  useEffect(() => { if (!notice) return; const timer = window.setTimeout(clearNotice, 6000); return () => window.clearTimeout(timer); }, [notice, clearNotice]);
  if (!notice) return null;
  return <div className={'notice ' + notice.type} role="status">{notice.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}<span>{notice.text}</span><button onClick={clearNotice} aria-label="Đóng thông báo"><X size={17} /></button></div>;
}
