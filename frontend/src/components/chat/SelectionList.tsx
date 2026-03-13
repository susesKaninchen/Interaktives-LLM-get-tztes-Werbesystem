interface SelectionItem {
  title: string;
  url: string;
  description: string;
}

interface SelectionListProps {
  items: SelectionItem[];
  onSelect: (item: SelectionItem, index: number) => void;
}

export function SelectionList({ items, onSelect }: SelectionListProps) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-2 my-2">
      {items.map((item, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(item, idx)}
          className="w-full text-left p-3 rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 transition-colors"
        >
          <div className="font-medium text-sm text-white">{idx + 1}. {item.title}</div>
          {item.url && (
            <div className="text-xs text-blue-400 mt-0.5 truncate">{item.url}</div>
          )}
          {item.description && (
            <div className="text-xs text-gray-400 mt-1 line-clamp-2">{item.description}</div>
          )}
        </button>
      ))}
    </div>
  );
}
