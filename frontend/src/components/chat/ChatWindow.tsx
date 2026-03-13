import { useChatStore } from "@/store/chatStore";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { PhaseStepper } from "./PhaseStepper";

export function ChatWindow() {
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
      <PhaseStepper currentPhase={activeConv?.current_phase ?? "search"} />
      <MessageList />
      <ChatInput />
    </div>
  );
}
