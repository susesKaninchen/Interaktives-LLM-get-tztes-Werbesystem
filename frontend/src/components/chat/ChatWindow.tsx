import { useChatStore } from "@/store/chatStore";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { PhaseStepper } from "./PhaseStepper";
import { PanelRight } from "lucide-react";

interface ChatWindowProps {
  onTogglePanel?: () => void;
}

export function ChatWindow({ onTogglePanel }: ChatWindowProps) {
  const { activeConversationId, conversations } = useChatStore();
  const activeConv = conversations.find((c) => c.id === activeConversationId);

  if (!activeConversationId) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p className="text-lg mb-2">Willkommen beim Werbesystem</p>
          <p className="text-sm">
            Erstelle eine neue Konversation, um loszulegen.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex items-center border-b border-gray-800">
        <div className="flex-1">
          <PhaseStepper currentPhase={activeConv?.current_phase ?? "search"} />
        </div>
        {onTogglePanel && (
          <button
            onClick={onTogglePanel}
            className="px-3 py-3 text-gray-500 hover:text-gray-300 transition-colors"
            title="Vorlagen & Wissen"
          >
            <PanelRight size={18} />
          </button>
        )}
      </div>
      <MessageList />
      <ChatInput />
    </div>
  );
}
