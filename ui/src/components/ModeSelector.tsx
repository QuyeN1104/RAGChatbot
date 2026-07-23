import { FileText, MessageCircle } from "lucide-react";
import { useChat } from "../context/ChatContext";

export function ModeSelector() {
  const { chatMode, setChatMode } = useChat();
  return <div className="mode-selector" role="group" aria-label="Chế độ trò chuyện">
    <button type="button" className={chatMode === "general" ? "is-active" : ""} aria-pressed={chatMode === "general"} onClick={() => setChatMode("general")} title="Trò chuyện thông thường">
      <MessageCircle size={15} /><span>General</span>
    </button>
    <button type="button" className={chatMode === "rag" ? "is-active" : ""} aria-pressed={chatMode === "rag"} onClick={() => setChatMode("rag")} title="Hỏi đáp tài liệu">
      <FileText size={15} /><span>Document</span>
    </button>
  </div>;
}
