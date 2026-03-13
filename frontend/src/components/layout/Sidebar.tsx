import { useEffect } from "react";
import { Plus, MessageSquare, Trash2, User } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export function Sidebar() {
  const {
    conversations,
    activeConversationId,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
  } = useChatStore();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return (
    <aside className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold text-white">Werbesystem</h1>
      </div>

      <div className="p-3">
        <button
          onClick={createConversation}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm transition-colors"
        >
          <Plus size={16} />
          Neue Konversation
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 space-y-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors ${
              conv.id === activeConversationId
                ? "bg-gray-700 text-white"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            }`}
            onClick={() => selectConversation(conv.id)}
          >
            <MessageSquare size={16} className="shrink-0" />
            <span className="truncate flex-1">{conv.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteConversation(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-opacity"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-gray-800">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-gray-200 cursor-pointer text-sm transition-colors">
          <User size={16} />
          <span>Mein Profil</span>
        </div>
      </div>
    </aside>
  );
}
