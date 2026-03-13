import { Check } from "lucide-react";

const PHASES = [
  { key: "search", label: "Suche" },
  { key: "select", label: "Auswahl" },
  { key: "profile", label: "Steckbrief" },
  { key: "matching", label: "Matching" },
  { key: "contact", label: "Kontakt" },
  { key: "outreach", label: "Anfrage" },
];

interface PhaseStepperProps {
  currentPhase: string;
}

export function PhaseStepper({ currentPhase }: PhaseStepperProps) {
  const currentIdx = PHASES.findIndex((p) => p.key === currentPhase);

  return (
    <div className="flex items-center gap-1 px-4 py-3 bg-gray-900 border-b border-gray-800 overflow-x-auto">
      {PHASES.map((phase, idx) => {
        const isComplete = idx < currentIdx;
        const isCurrent = idx === currentIdx;

        return (
          <div key={phase.key} className="flex items-center">
            {idx > 0 && (
              <div
                className={`w-6 h-px mx-1 ${
                  isComplete ? "bg-blue-500" : "bg-gray-700"
                }`}
              />
            )}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                isCurrent
                  ? "bg-blue-600 text-white"
                  : isComplete
                    ? "bg-blue-600/20 text-blue-400"
                    : "bg-gray-800 text-gray-500"
              }`}
            >
              {isComplete && <Check size={12} />}
              {isCurrent && (
                <span className="w-1.5 h-1.5 rounded-full bg-white" />
              )}
              {phase.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}
