import { useEffect, useState } from "react";
import { FileText, Trash2, Mail, Globe, Phone } from "lucide-react";

interface Template {
  id: number;
  name: string;
  category: string;
  content: string;
  created_at: string;
}

const CATEGORY_ICONS: Record<string, typeof Mail> = {
  email: Mail,
  landing_page: Globe,
  phone_script: Phone,
};

const CATEGORY_LABELS: Record<string, string> = {
  email: "E-Mail",
  landing_page: "Landing Page",
  phone_script: "Telefonskript",
};

export function TemplateList() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);

  const loadTemplates = () => {
    fetch("/api/templates")
      .then((r) => r.json())
      .then(setTemplates)
      .catch(() => {});
  };

  useEffect(loadTemplates, []);

  const deleteTemplate = async (id: number) => {
    await fetch(`/api/templates/${id}`, { method: "DELETE" });
    loadTemplates();
  };

  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  if (templates.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-sm text-center">
        Noch keine Vorlagen. Erstelle eine Kontaktanfrage und speichere sie als Vorlage.
      </div>
    );
  }

  return (
    <div className="space-y-2 p-2">
      {templates.map((t) => {
        const Icon = CATEGORY_ICONS[t.category] || FileText;
        return (
          <div key={t.id} className="bg-gray-800 rounded-lg border border-gray-700">
            <div
              className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-gray-750"
              onClick={() => setExpanded(expanded === t.id ? null : t.id)}
            >
              <Icon size={14} className="text-blue-400 shrink-0" />
              <span className="text-sm text-white flex-1 truncate">{t.name}</span>
              <span className="text-xs text-gray-500">{CATEGORY_LABELS[t.category] || t.category}</span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteTemplate(t.id); }}
                className="text-gray-500 hover:text-red-400"
              >
                <Trash2 size={12} />
              </button>
            </div>
            {expanded === t.id && (
              <div className="px-3 pb-3 border-t border-gray-700 mt-1 pt-2">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {t.content}
                </pre>
                <button
                  onClick={() => copyToClipboard(t.content)}
                  className="mt-2 px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded text-white"
                >
                  Kopieren
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
