import { Sparkles } from 'lucide-react';
export function BrandMark({ small = false }: { small?: boolean }) {
  return <span className={small ? 'brand-mark brand-mark--small' : 'brand-mark'} aria-hidden="true"><Sparkles size={small ? 16 : 22} strokeWidth={1.9} /></span>;
}
