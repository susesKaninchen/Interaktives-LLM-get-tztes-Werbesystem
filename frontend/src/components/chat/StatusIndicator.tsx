import { useChatStore } from "@/store/chatStore";

export function StatusIndicator() {
  const { isThinking, isStreaming, statusText, progress } = useChatStore();

  if (!isThinking && !isStreaming) return null;

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 mb-4 animate-pulse">
      <div className="flex items-center gap-3">
        {/* Loading Spinner */}
        <div className="flex-shrink-0">
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
        </div>
        
        {/* Status Text */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-300 truncate">
            {statusText || "Verarbeite..."}
          </p>
          
          {/* Progress Bar */}
          {progress && (
            <div className="mt-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-400">{progress.message}</span>
                <span className="text-xs text-gray-400">
                  {progress.current}/{progress.total}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div 
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}