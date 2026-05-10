import { useState, useEffect } from "react";
import { ChevronRight, ChevronLeft, RefreshCw, SkipForward, Sparkles, ArrowUpDown } from "lucide-react";
import { api } from "@/api/http";

interface FlowSuggestion {
  action: string;
  target_step: string;
  confidence: number;
  reasoning: string;
  skipable?: boolean;
  iterable?: boolean;
}

interface FlowAction {
  type: string;
  target_step: string;
  user_friendly: string;
  is_recommended: boolean;
}

interface DynamicFlowProps {
  onExecuteAction?: (action: string, targetStep?: string) => void;
  onAIResponse?: (response: string) => void;
}

export function DynamicFlow({ onExecuteAction, onAIResponse }: DynamicFlowProps) {
  const [flowState, setFlowState] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<FlowSuggestion[]>([]);
  const [availableActions, setAvailableActions] = useState<FlowAction[]>([]);
  const [conversationProgress, setConversationProgress] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userMessage, setUserMessage] = useState("");

  useEffect(() => {
    initializeFlow();
  }, []);

  const initializeFlow = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/dynamic/conversation/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experience_level: "beginner"
        })
      });
      
      const data = await response.json();
      setFlowState(data.flow_state);
      setSuggestions(data.suggestions);
      setAvailableActions(data.available_actions);
      setConversationProgress(data.conversation_progress);
      
      if (onAIResponse) {
        onAIResponse(data.welcome_message);
      }
    } catch (error) {
      console.error("Failed to initialize flow:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserMessage = async (message: string) => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/dynamic/conversation/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      
      const data = await response.json();
      setFlowState(data.flow_state);
      setSuggestions(data.flow_suggestions);
      setAvailableActions(data.available_actions);
      setConversationProgress(data.conversation_progress);
      
      if (onAIResponse) {
        onAIResponse(data.ai_response);
      }
      
      setUserMessage("");
    } catch (error) {
      console.error("Failed to process message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFlowAction = async (action: string, targetStep?: string) => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/dynamic/flow/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, target_step: targetStep })
      });
      
      const data = await response.json();
      setFlowState(data.flow_state);
      setSuggestions(data.suggestions);
      setAvailableActions(data.available_actions);
      setConversationProgress(data.conversation_progress);
      
      if (onAIResponse && data.transition_message) {
        onAIResponse(data.transition_message);
      }
      
      if (onExecuteAction) {
        onExecuteAction(action, targetStep);
      }
    } catch (error) {
      console.error("Failed to execute flow action:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "forward": return <ChevronRight size={16} />;
      case "backward": return <ChevronLeft size={16} />;
      case "iterate": return <RefreshCw size={16} />;
      case "skip": return <SkipForward size={16} />;
      default: return <Sparkles size={16} />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case "forward": return "bg-blue-600 hover:bg-blue-700";
      case "backward": return "bg-gray-600 hover:bg-gray-700";
      case "iterate": return "bg-green-600 hover:bg-green-700";
      case "skip": return "bg-purple-600 hover:bg-purple-700";
      default: return "bg-indigo-600 hover:bg-indigo-700";
    }
  };

  if (!flowState) {
    return <div className="text-gray-500">Lade Flow...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Flow Progress */}
      {conversationProgress && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Fortschritt</span>
            <span className="text-sm font-medium text-gray-200">
              {conversationProgress.completed_steps} / {conversationProgress.total_steps} Schritte
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${conversationProgress.percentage}%` }}
            />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Aktueller Schritt: {flowState.current_step}
          </div>
        </div>
      )}

      {/* AI Suggestions */}
      {suggestions.length > 0 && (
        <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-medium text-blue-300">KI-Vorschläge</h3>
          </div>
          <div className="space-y-2">
            {suggestions.slice(0, 3).map((suggestion, index) => (
              <div
                key={index}
                className="bg-gray-800/50 border border-gray-700 rounded-lg p-3 hover:bg-gray-800 transition-colors cursor-pointer"
                onClick={() => handleFlowAction(suggestion.action, suggestion.target_step)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getActionIcon(suggestion.action)}
                    <span className="text-sm text-gray-200">
                      {suggestion.action} → {suggestion.target_step}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">
                      {Math.round(suggestion.confidence * 100)}% relevant
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">{suggestion.reasoning}</p>
                {suggestion.iterable && (
                  <span className="inline-flex items-center gap-1 mt-2 text-xs text-green-400">
                    <RefreshCw size={12} />
                    Wiederholbar
                  </span>
                )}
                {suggestion.skipable && (
                  <span className="inline-flex items-center gap-1 mt-2 ml-2 text-xs text-purple-400">
                    <SkipForward size={12} />
                    Überspringbar
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Actions */}
      {availableActions.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <ArrowUpDown className="w-4 h-4 text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">Verfügbare Aktionen</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {availableActions.map((action, index) => (
              <button
                key={index}
                onClick={() => handleFlowAction(action.type, action.target_step)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  action.is_recommended 
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700" 
                    : getActionColor(action.type)
                }`}
                disabled={isLoading}
              >
                {getActionIcon(action.type)}
                <span>{action.user_friendly}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Input */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <textarea
          value={userMessage}
          onChange={(e) => setUserMessage(e.target.value)}
          placeholder="Was möchtest du tun? Sag es einfach in ganzen Sätzen..."
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
          rows={3}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleUserMessage(userMessage);
            }
          }}
        />
        <button
          onClick={() => handleUserMessage(userMessage)}
          disabled={!userMessage.trim() || isLoading}
          className="mt-2 w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {isLoading ? "Verarbeite..." : "Senden"}
        </button>
      </div>

      {/* Conversation History Summary */}
      {flowState.completed_steps.length > 0 && (
        <div className="bg-gray-800/30 border border-gray-700/50 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-2">Erledigte Schritte:</div>
          <div className="flex flex-wrap gap-1">
            {flowState.completed_steps.map((step, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-green-900/30 border border-green-700/50 rounded text-xs text-green-400"
              >
                <span>✓</span>
                {step}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}