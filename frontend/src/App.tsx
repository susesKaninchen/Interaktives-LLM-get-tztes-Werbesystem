import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { RightPanel } from "@/components/layout/RightPanel";

export default function App() {
  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <ChatWindow onTogglePanel={() => setRightPanelOpen(!rightPanelOpen)} />
      {rightPanelOpen && <RightPanel onClose={() => setRightPanelOpen(false)} />}
    </div>
  );
}
