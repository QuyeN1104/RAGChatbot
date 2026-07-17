import type { Message } from '../types';
import { AttachmentPreview } from './AttachmentPreview';
export function UserMessage({ message }: { message: Message }) {
  return <div className="user-message-wrap"><div className="user-message">{message.attachments?.length ? <div className="sent-attachments">{message.attachments.map((item) => <AttachmentPreview key={item.id} attachment={item} />)}</div> : null}<p>{message.content}</p></div></div>;
}
