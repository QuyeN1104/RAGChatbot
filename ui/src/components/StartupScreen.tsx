import { CheckCircle2, Database, Loader2, Orbit, ServerCog } from 'lucide-react';
import { BrandMark } from './BrandMark';
import { useChat } from '../context/ChatContext';

const labels: Record<string, string> = {
  memory_load: 'Lịch sử hội thoại',
  embedding_and_chroma_load: 'Embedding và vector database',
  embedding_inference: 'Embedding warmup',
  model_configuration: 'Cấu hình API models',
  default_llm_client: 'LLM client',
  langgraph_compile: 'Agent graph',
  default_llm_inference: 'LLM warmup',
};

export function StartupScreen() {
  const { startupTimings, apiStatus } = useChat();
  const stages = Object.entries(startupTimings);
  return <main className="startup-screen" aria-live="polite">
    <div className="startup-card"><BrandMark /><div><p className="eyebrow">Lumen RAG</p><h1>Đang chuẩn bị workspace</h1><p>Embedding, model và database phải sẵn sàng trước khi bạn bắt đầu.</p></div>
      <div className="startup-progress"><span><Loader2 className="spin" size={18} />{apiStatus === 'offline' ? 'Warmup gặp lỗi, đang thử lại…' : 'Đang kết nối backend…'}</span>
        {stages.map(([name, duration]) => <span key={name}><CheckCircle2 size={17} />{labels[name] || name}<small>{Math.round(duration)} ms</small></span>)}
      </div>
      <div className="startup-icons"><Database size={18} /><Orbit size={18} /><ServerCog size={18} /></div>
    </div>
  </main>;
}
