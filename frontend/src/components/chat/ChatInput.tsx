import { useState, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export function ChatInput() {
  const [input, setInput] = useState("");
  const { sendMessage, isStreaming, isThinking, activeConversationId } = useChatStore();
  const busy = isStreaming || isThinking;

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || busy || !activeConversationId) return;
    sendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-800 p-4">
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            activeConversationId
              ? "Nachricht eingeben..."
              : "Waehle oder erstelle eine Konversation"
          }
          disabled={!activeConversationId || busy}
          rows={1}
          className="flex-1 resize-none rounded-xl bg-gray-800 border border-gray-700 px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || busy || !activeConversationId}
          className="p-3 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
