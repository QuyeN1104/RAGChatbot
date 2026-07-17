import { Check, Copy } from 'lucide-react';
import { useState } from 'react';
export function CodeBlock({ language, children }: { language: string; children: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard.writeText(children); setCopied(true); window.setTimeout(() => setCopied(false), 1600); };
  return <div className="code-block"><div className="code-header"><span>{language || 'text'}</span><button onClick={copy}>{copied ? <Check size={15} /> : <Copy size={15} />}{copied ? 'Đã sao chép' : 'Sao chép'}</button></div><pre><code>{children}</code></pre></div>;
}
