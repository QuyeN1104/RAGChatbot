import { Menu, Share2, TimerReset } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { ModelSelector } from './ModelSelector';
import { SettingsMenu } from './SettingsMenu';
export function TopNavbar() {
  const { setDrawerOpen, newChat, apiStatus } = useChat();
  const share = async () => { await navigator.clipboard?.writeText(location.href); };
  return <header className="top-navbar"><div className="nav-leading"><button className="icon-button sidebar-trigger" onClick={() => setDrawerOpen(true)} aria-label="Mở sidebar"><Menu size={20} /></button><ModelSelector /><span className={'api-indicator ' + apiStatus} title={'API: ' + apiStatus}><i />{apiStatus === 'online' ? 'Đã kết nối' : apiStatus === 'checking' ? 'Đang kết nối' : 'Mất kết nối'}</span></div><div className="nav-actions"><button className="nav-text-button" onClick={share}><Share2 size={18} /><span>Chia sẻ</span></button><button className="icon-button" onClick={newChat} aria-label="Tạo cuộc trò chuyện mới" title="Cuộc trò chuyện mới"><TimerReset size={19} /></button><SettingsMenu /></div></header>;
}
