import { suggestions } from '../data/sampleData';
import { useChat } from '../context/ChatContext';
import { BrandMark } from './BrandMark';
import { SuggestionCard } from './SuggestionCard';
export function WelcomeScreen() {
  const { setInput } = useChat();
  return <section className="welcome-screen"><BrandMark /><div><p className="eyebrow">Trợ lý AI của bạn</p><h1>Hôm nay tôi có thể giúp gì cho bạn?</h1><p className="welcome-copy">Bắt đầu với một gợi ý hoặc đặt bất kỳ câu hỏi nào bạn đang nghĩ tới.</p></div><div className="suggestion-grid">{suggestions.map((item) => <SuggestionCard key={item.title} title={item.title} description={item.description} onClick={() => setInput(item.prompt)} />)}</div></section>;
}
