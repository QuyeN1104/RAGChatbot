import { ArrowUpRight } from 'lucide-react';
export function SuggestionCard({ title, description, onClick }: { title: string; description: string; onClick: () => void }) {
  return <button className="suggestion-card" onClick={onClick}><span><strong>{title}</strong><small>{description}</small></span><ArrowUpRight size={18} /></button>;
}
