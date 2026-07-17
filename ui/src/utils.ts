import type { Attachment } from './types';
export const id = () => crypto.randomUUID();
export function fileToAttachment(file: File): Attachment { return { id: id(), name: file.name, type: file.type || 'application/octet-stream', size: file.size, file, preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined }; }
export const formatBytes = (bytes: number) => bytes < 1048576 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1048576).toFixed(1)} MB`;
