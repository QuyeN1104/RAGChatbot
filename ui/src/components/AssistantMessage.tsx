import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import { FileText } from 'lucide-react';
import type { Message } from '../types';
import { useChat } from '../context/ChatContext';
import { BrandMark } from './BrandMark';
import { CodeBlock } from './CodeBlock';
import { MessageActions } from './MessageActions';

const components: Components = {
  code({ className, children }) {
    const language = /language-(\w+)/.exec(className || '')?.[1];
    const content = String(children).replace(/\n$/, '');
    return language ? <CodeBlock language={language}>{content}</CodeBlock> : <code className="inline-code">{children}</code>;
  },
};
export function AssistantMessage({ message }: { message: Message }) {
  const { regenerate, editMessage, active } = useChat();
  const relatedUser = [...active.messages.slice(0, active.messages.findIndex((item) => item.id === message.id))].reverse().find((item) => item.role === 'user');
  return <div className="assistant-message"><div className="assistant-avatar"><BrandMark small /></div><div className="assistant-content">
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>{message.content}</ReactMarkdown>
    {!!message.sources?.length && <div className="source-list"><p>Nguồn tham chiếu</p>{message.sources.map((source, index) => <span key={source.source + ':' + source.page + ':' + index}><FileText size={14} />{source.source}{source.page !== null && source.page !== undefined ? ' · trang ' + source.page : ''}</span>)}</div>}
    {message.latencyMs !== undefined && <p className="response-latency">Server latency: {(message.latencyMs / 1000).toFixed(2)} giây</p>}
    <MessageActions content={message.content} onRegenerate={() => void regenerate(message.id)} onEdit={() => relatedUser && editMessage(relatedUser.id)} />
  </div></div>;
}
