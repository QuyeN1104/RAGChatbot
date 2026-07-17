import { Check, ChevronDown, Cpu, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { useChat } from '../context/ChatContext';

export function ModelSelector() {
  const { models, selectedModel, setSelectedModel } = useChat(); const [open, setOpen] = useState(false);
  return <div className="popover-wrap">
    <button className="model-button" onClick={() => setOpen(!open)} aria-expanded={open} disabled={!models.length}>
      <span>{selectedModel?.label || 'Đang tải model…'}</span><ChevronDown size={16} />
    </button>
    {open && <div className="model-menu"><p>Model từ backend</p>{models.map((item) => {
      const active = selectedModel?.provider === item.provider && selectedModel?.model === item.model;
      return <button key={item.provider + ':' + item.model} onClick={() => { setSelectedModel(item); setOpen(false); }}>
        {item.provider === 'ollama' ? <Cpu size={18} /> : <Sparkles size={18} />}
        <span><strong>{item.label}</strong><small>{item.provider} · {item.model}</small></span>{active && <Check size={17} />}
      </button>;
    })}</div>}
  </div>;
}
