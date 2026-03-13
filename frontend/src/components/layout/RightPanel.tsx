import { useState } from "react";
import { X, FileText, Lightbulb } from "lucide-react";
import { TemplateList } from "@/components/templates/TemplateList";
import { KnowledgePanel } from "@/components/knowledge/KnowledgePanel";

interface RightPanelProps {
  onClose: () => void;
}

type Tab = "templates" | "knowledge";

export function RightPanel({ onClose }: RightPanelProps) {
  const [tab, setTab] = useState<Tab>("templates");

  return (
    <aside className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col h-full">
      <div className="flex items-center justify-between p-3 border-b border-gray-800">
        <div className="flex gap-1">
          <button
            onClick={() => setTab("templates")}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              tab === "templates"
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            <FileText size={12} /> Vorlagen
          </button>
          <button
            onClick={() => setTab("knowledge")}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              tab === "knowledge"
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            <Lightbulb size={12} /> Wissen
          </button>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "templates" ? <TemplateList /> : <KnowledgePanel />}
      </div>
    </aside>
  );
}
