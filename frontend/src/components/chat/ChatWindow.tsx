import { useChatStore } from "@/store/chatStore";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { PhaseStepper } from "./PhaseStepper";
import { StatusIndicator } from "./StatusIndicator";
import { ErrorDisplay } from "./ErrorDisplay";
import { PanelRight, Sparkles } from "lucide-react";
import { useState } from "react";

interface ChatWindowProps {
  onTogglePanel?: () => void;
}

export function ChatWindow({ onTogglePanel }: ChatWindowProps) {
  const { activeConversationId, conversations } = useChatStore();
  const activeConv = conversations.find((c) => c.id === activeConversationId);
  const [showDynamicFlow, setShowDynamicFlow] = useState(false);

  if (!activeConversationId) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500 bg-gray-900">
        <div className="text-center p-8 max-w-md">
          <Sparkles className="w-20 h-20 mx-auto mb-6 text-blue-500" />
          <h2 className="text-2xl font-bold mb-2 text-gray-400">
            Willkommen beim Werbesystem
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            Erstelle eine neue Konversation oder verwende den dynamischen Flow-Modus
            für eine intelligente, adaptive Dialogsteuerung.
          </p>
          <div className="flex flex-col gap-3">
            <button
              onClick={() => useChatStore.getState().createConversation()}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              🔗 Neue Konversation
            </button>
            <button
              onClick={() => setShowDynamicFlow(true)}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors font-medium"
            >
              🚀 Dynamischer Flow-Modus
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-gray-900">
      {/* Header */}
      <div className="flex items-center border-b border-gray-800 bg-gray-800/50 backdrop-blur sticky top-0 z-10">
        <div className="flex-1">
          <PhaseStepper currentPhase={activeConv?.current_phase ?? "search"} />
        </div>
        <div className="flex items-center gap-1 px-2">
          {/* Toggle for dynamic flow */}
          <button
            onClick={() => setShowDynamicFlow(!showDynamicFlow)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              showDynamicFlow 
                ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white" 
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-700"
            }`}
            title="Dynamischer Flow-Modus"
          >
            <Sparkles size={16} className="inline mr-1" />
            Flow
          </button>
          
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
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <MessageList />
        </div>
      </div>

      {/* Status Indicator */}
      <div className="px-6 pb-2">
        <StatusIndicator />
      </div>

      {/* Input Area - only show in traditional mode */}
      {!showDynamicFlow && (
        <div className="border-t border-gray-800 bg-gray-800/30 backdrop-blur">
          <ChatInput />
        </div>
      )}

      {/* Error Display */}
      <ErrorDisplay />
    </div>
  );
}
