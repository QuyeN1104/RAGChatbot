import { useChat } from '../context/ChatContext';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { Notice } from './Notice';
import { Sidebar } from './Sidebar';
import { StartupScreen } from './StartupScreen';
import { TopNavbar } from './TopNavbar';
import { WelcomeScreen } from './WelcomeScreen';

export function ChatLayout() {
  const { active, sidebarCollapsed, apiStatus } = useChat();
  if (apiStatus !== 'online') return <StartupScreen />;
  return <div className={'app-shell ' + (sidebarCollapsed ? 'sidebar-collapsed' : '')}><Sidebar /><main className="chat-workspace"><TopNavbar /><div className="chat-stage">{active.messages.length ? <MessageList /> : <WelcomeScreen />}</div><ChatInput /><Notice /></main></div>;
}
