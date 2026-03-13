import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chatStore";
import { Bot, User } from "lucide-react";

export function MessageList() {
  const { messages, streamingContent, isStreaming } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.length === 0 && !isStreaming && (
        <div className="flex items-center justify-center h-full text-gray-500">
          <p>Starte eine Konversation, um Kunden zu finden und zu analysieren.</p>
        </div>
      )}

      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
        >
          {msg.role !== "user" && (
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
              <Bot size={16} />
            </div>
          )}
          <div
            className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-100"
            }`}
          >
            {msg.content}
          </div>
          {msg.role === "user" && (
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center shrink-0">
              <User size={16} />
            </div>
          )}
        </div>
      ))}

      {isStreaming && streamingContent && (
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
            <Bot size={16} />
          </div>
          <div className="max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed bg-gray-800 text-gray-100">
            {streamingContent}
            <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
