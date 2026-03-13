import { useEffect, useState } from "react";
import { Lightbulb, Trash2, Tag } from "lucide-react";

interface KnowledgeEntry {
  id: number;
  content: string;
  tags: string[];
  created_at: string;
}

export function KnowledgePanel() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);

  const loadEntries = () => {
    fetch("/api/knowledge")
      .then((r) => r.json())
      .then(setEntries)
      .catch(() => {});
  };

  useEffect(loadEntries, []);

  const deleteEntry = async (id: number) => {
    await fetch(`/api/knowledge/${id}`, { method: "DELETE" });
    loadEntries();
  };

  if (entries.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-sm text-center">
        Noch keine Eintraege. Sage dem Assistenten "merke dir..." um Wissen zu speichern.
      </div>
    );
  }

  return (
    <div className="space-y-2 p-2">
      {entries.map((e) => (
        <div key={e.id} className="bg-gray-800 rounded-lg border border-gray-700 p-3">
          <div className="flex items-start gap-2">
            <Lightbulb size={14} className="text-yellow-400 mt-0.5 shrink-0" />
            <p className="text-sm text-gray-200 flex-1">{e.content}</p>
            <button
              onClick={() => deleteEntry(e.id)}
              className="text-gray-500 hover:text-red-400 shrink-0"
            >
              <Trash2 size={12} />
            </button>
          </div>
          {e.tags.length > 0 && (
            <div className="flex items-center gap-1 mt-2 ml-5">
              <Tag size={10} className="text-gray-500" />
              {e.tags.map((tag, i) => (
                <span key={i} className="px-1.5 py-0.5 bg-gray-700 text-gray-400 rounded text-xs">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
