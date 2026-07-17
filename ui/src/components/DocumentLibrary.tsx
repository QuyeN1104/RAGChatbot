import { FileText, RefreshCw, Trash2 } from 'lucide-react';
import { useChat } from '../context/ChatContext';

export function DocumentLibrary() {
  const { documents, refreshDocuments, deleteDocument, isUploading } = useChat();
  return <section className="document-library">
    <div className="document-heading"><span>Tài liệu RAG</span><button onClick={() => void refreshDocuments()} aria-label="Làm mới tài liệu"><RefreshCw size={15} className={isUploading ? 'spin' : ''} /></button></div>
    <div className="document-items">{documents.length ? documents.map((name) => <div className="document-row" key={name}><FileText size={16} /><span title={name}>{name}</span><button onClick={() => void deleteDocument(name)} aria-label={'Xóa ' + name}><Trash2 size={15} /></button></div>) : <p>Chưa có PDF nào</p>}</div>
  </section>;
}
