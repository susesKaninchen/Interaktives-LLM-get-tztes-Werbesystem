import { AlertCircle, X } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export function ErrorDisplay() {
  const { error, clearError } = useChatStore();

  if (!error) return null;

  return (
    <div className="fixed bottom-4 right-4 max-w-md bg-red-900 border border-red-700 rounded-lg shadow-lg p-4 z-50 animate-slide-in">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-red-200 mb-1">Fehler aufgetreten</h4>
          <p className="text-sm text-red-300">{error.message}</p>
          {error.details && (
            <details className="mt-2 text-xs text-red-400">
              <summary className="cursor-pointer hover:text-red-300">
                Details anzeigen
              </summary>
              <pre className="mt-1 overflow-auto max-h-32 whitespace-pre-wrap">
                {typeof error.details === 'string' ? error.details : JSON.stringify(error.details, null, 2)}
              </pre>
            </details>
          )}
        </div>
        <button
          onClick={clearError}
          className="text-red-400 hover:text-red-300 transition-colors flex-shrink-0"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
}