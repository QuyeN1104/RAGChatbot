import type { Message } from '../types';
import { AssistantMessage } from './AssistantMessage';
import { UserMessage } from './UserMessage';
export function MessageItem({ message }: { message: Message }) { return message.role === 'assistant' ? <AssistantMessage message={message} /> : <UserMessage message={message} />; }
