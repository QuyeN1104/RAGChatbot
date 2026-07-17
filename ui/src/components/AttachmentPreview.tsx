import { File, X } from 'lucide-react';
import type { Attachment } from '../types';
import { formatBytes } from '../utils';
export function AttachmentPreview({ attachment, onRemove }: { attachment: Attachment; onRemove?: () => void }) {
  return <div className="attachment-preview">{attachment.preview ? <img src={attachment.preview} alt={'Xem trước ' + attachment.name} /> : <span className="file-icon"><File size={20} /></span>}<span className="attachment-name"><strong>{attachment.name}</strong><small>{formatBytes(attachment.size)}</small></span>{onRemove && <button onClick={onRemove} aria-label={'Xóa ' + attachment.name}><X size={15} /></button>}</div>;
}
