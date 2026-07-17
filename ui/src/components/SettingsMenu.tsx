import { Check, Languages, Settings2 } from 'lucide-react';
import { useState } from 'react';
import { ThemeToggle } from './ThemeToggle';
export function SettingsMenu() {
  const [open, setOpen] = useState(false);
  return <div className="popover-wrap"><button className="icon-button" onClick={() => setOpen(!open)} aria-label="Cài đặt" aria-expanded={open}><Settings2 size={19} /></button>{open && <div className="settings-menu"><div><Languages size={18} /><span>Ngôn ngữ</span><small>Tiếng Việt</small></div><div><Check size={18} /><span>Phản hồi súc tích</span></div><div className="theme-row"><span>Giao diện</span><ThemeToggle /></div></div>}</div>;
}
