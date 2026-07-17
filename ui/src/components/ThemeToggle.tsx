import { Moon, Sun } from 'lucide-react';
import { useChat } from '../context/ChatContext';
export function ThemeToggle() {
  const { theme, toggleTheme } = useChat();
  return <button className="icon-button" onClick={toggleTheme} aria-label={theme === 'light' ? 'Bật giao diện tối' : 'Bật giao diện sáng'}>{theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}</button>;
}
