import { ChevronLeft, PanelLeftClose, Plus, Search, Settings, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useChat } from '../context/ChatContext';
import type { ConversationGroup } from '../types';
import { BrandMark } from './BrandMark';
import { DocumentLibrary } from './DocumentLibrary';
import { SidebarConversationItem } from './SidebarConversationItem';

const groups: ConversationGroup[] = ['Hôm nay', '7 ngày trước', '30 ngày trước'];
export function Sidebar() {
  const { conversations, activeId, selectConversation, renameConversation, deleteConversation, newChat, sidebarCollapsed, setSidebarCollapsed, drawerOpen, setDrawerOpen } = useChat();
  const [query, setQuery] = useState('');
  const filtered = useMemo(() => conversations.filter((item) => item.title.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi'))), [conversations, query]);
  return <>
    {drawerOpen && <button className="drawer-scrim" onClick={() => setDrawerOpen(false)} aria-label="Đóng menu" />}
    <aside className={'sidebar ' + (sidebarCollapsed ? 'is-collapsed ' : '') + (drawerOpen ? 'is-open' : '')}>
      <div className="sidebar-top">
        <div className="sidebar-brand"><BrandMark small /><span>Lumen RAG</span><button className="mobile-close" onClick={() => setDrawerOpen(false)} aria-label="Đóng sidebar"><X size={20} /></button></div>
        <button className="new-chat-button" onClick={newChat}><Plus size={19} /><span>Cuộc trò chuyện mới</span></button>
        {!sidebarCollapsed && <label className="search-box"><Search size={17} /><span className="sr-only">Tìm cuộc trò chuyện</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm kiếm" /></label>}
      </div>
      {!sidebarCollapsed && <nav className="conversation-history" aria-label="Lịch sử trò chuyện">{groups.map((group) => {
        const items = filtered.filter((item) => item.group === group); if (!items.length) return null;
        return <section key={group}><h2>{group}</h2>{items.map((item) => <SidebarConversationItem key={item.id} conversation={item} active={item.id === activeId} onSelect={() => void selectConversation(item.id)} onRename={(title) => renameConversation(item.id, title)} onDelete={() => void deleteConversation(item.id)} />)}</section>;
      })}</nav>}
      {!sidebarCollapsed && <DocumentLibrary />}
      <div className="sidebar-footer">
        {!sidebarCollapsed && <button className="account-button"><span className="avatar">Q</span><span><strong>Quyên</strong><small>RAG workspace</small></span><Settings size={18} /></button>}
        <button className="collapse-button" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} aria-label={sidebarCollapsed ? 'Mở rộng sidebar' : 'Thu gọn sidebar'}>{sidebarCollapsed ? <ChevronLeft size={19} className="rotate-180" /> : <><PanelLeftClose size={18} /><span>Thu gọn sidebar</span></>}</button>
      </div>
    </aside>
  </>;
}
