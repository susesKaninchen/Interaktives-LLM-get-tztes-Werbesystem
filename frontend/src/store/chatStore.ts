import { create } from "zustand";
import { api, type Conversation, type Message } from "@/api/http";
import { ChatWebSocket, type WsMessage } from "@/api/websocket";

interface ChatStore {
  conversations: Conversation[];
  activeConversationId: number | null;
  messages: Message[];
  streamingContent: string;
  isStreaming: boolean;
  isThinking: boolean;
  statusText: string;
  ws: ChatWebSocket | null;

  loadConversations: () => Promise<void>;
  createConversation: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  deleteConversation: (id: number) => Promise<void>;
  sendMessage: (content: string) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  streamingContent: "",
  isStreaming: false,
  isThinking: false,
  statusText: "",
  ws: null,

  loadConversations: async () => {
    const conversations = await api.listConversations();
    set({ conversations });
  },

  createConversation: async () => {
    const conv = await api.createConversation();
    set((s) => ({ conversations: [conv, ...s.conversations] }));
    await get().selectConversation(conv.id);
  },

  selectConversation: async (id: number) => {
    get().ws?.close();

    const messages = await api.getMessages(id);
    const ws = new ChatWebSocket(id);

    ws.onMessage((msg: WsMessage) => {
      switch (msg.type) {
        case "status":
          set({ isThinking: true, statusText: msg.content });
          break;
        case "stream_start":
          set({ isStreaming: true, isThinking: false, statusText: "", streamingContent: "" });
          break;
        case "stream_token":
          set((s) => ({
            streamingContent: s.streamingContent + msg.content,
          }));
          break;
        case "stream_end": {
          set((s) => ({
            isStreaming: false,
            isThinking: false,
            statusText: "",
            streamingContent: "",
            messages: [
              ...s.messages,
              {
                id: Date.now(),
                conversation_id: id,
                role: "assistant",
                content: msg.content,
                metadata_json: null,
                created_at: new Date().toISOString(),
              },
            ],
            conversations: msg.phase
              ? s.conversations.map((c) =>
                  c.id === id ? { ...c, current_phase: msg.phase! } : c
                )
              : s.conversations,
          }));
          break;
        }
        case "error":
          set({ isStreaming: false, isThinking: false, statusText: "" });
          break;
      }
    });

    ws.connect();
    set({ activeConversationId: id, messages, ws });
  },

  deleteConversation: async (id: number) => {
    await api.deleteConversation(id);
    const { activeConversationId, ws } = get();
    if (activeConversationId === id) {
      ws?.close();
      set({ activeConversationId: null, messages: [], ws: null });
    }
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
    }));
  },

  sendMessage: (content: string) => {
    const { ws, activeConversationId } = get();
    if (!ws || !activeConversationId) return;

    set((s) => ({
      isThinking: true,
      statusText: "Sende...",
      messages: [
        ...s.messages,
        {
          id: Date.now(),
          conversation_id: activeConversationId,
          role: "user",
          content,
          metadata_json: null,
          created_at: new Date().toISOString(),
        },
      ],
    }));

    ws.send(content);
  },
}));
