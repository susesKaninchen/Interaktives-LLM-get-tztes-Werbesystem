import { Sidebar } from "@/components/layout/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <ChatWindow />
    </div>
  );
}
