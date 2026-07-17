import { ChatLayout } from './components/ChatLayout';
import { ChatProvider } from './context/ChatContext';
export default function App() { return <ChatProvider><ChatLayout /></ChatProvider>; }
