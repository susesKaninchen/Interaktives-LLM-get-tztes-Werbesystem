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
  progress: { current: number; total: number; message: string } | null;
  error: { message: string; details?: any } | null;
  ws: ChatWebSocket | null;

  loadConversations: () => Promise<void>;
  createConversation: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  deleteConversation: (id: number) => Promise<void>;
  sendMessage: (content: string) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  streamingContent: "",
  isStreaming: false,
  isThinking: false,
  statusText: "",
  progress: null,
  error: null,
  ws: null,

  loadConversations: async () => {
    try {
      const conversations = await api.listConversations();
      set({ conversations });
    } catch (error) {
      set({ 
        error: { 
          message: "Fehler beim Laden der Konversationen", 
          details: error 
        } 
      });
    }
  },

  createConversation: async () => {
    try {
      const conv = await api.createConversation();
      set((s) => ({ conversations: [conv, ...s.conversations] }));
      await get().selectConversation(conv.id);
    } catch (error) {
      set({ 
        error: { 
          message: "Fehler beim Erstellen der Konversation", 
          details: error 
        } 
      });
    }
  },

  selectConversation: async (id: number) => {
    try {
      get().ws?.close();

      const messages = await api.getMessages(id);
      const ws = new ChatWebSocket(id);
      
      ws.onMessage((msg: WsMessage) => {
        switch (msg.type) {
          case "heartbeat":
            // Respond to heartbeat to keep connection alive
            ws.send(JSON.stringify({ type: "heartbeat_ack" }));
            break;
            
          case "status":
            set({ isThinking: true, statusText: msg.content, error: null });
            break;
            
          case "progress":
            set({ 
              isThinking: true, 
              progress: {
                current: msg.content.current,
                total: msg.content.total,
                message: msg.content.message
              }
            });
            break;
            
          case "stream_start":
            set({ 
              isStreaming: true, 
              isThinking: false, 
              statusText: "", 
              streamingContent: "",
              progress: null 
            });
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
              progress: null,
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
            set({ 
              isStreaming: false, 
              isThinking: false, 
              statusText: "", 
              progress: null,
              error: {
                message: msg.content,
                details: msg.details
              }
            });
            break;
        }
      });

      ws.connect();
      set({ activeConversationId: id, messages, ws, error: null });
    } catch (error) {
      set({ 
        error: { 
          message: "Fehler beim Auswählen der Konversation", 
          details: error 
        } 
      });
    }
  },

  deleteConversation: async (id: number) => {
    try {
      await api.deleteConversation(id);
      const { activeConversationId, ws } = get();
      if (activeConversationId === id) {
        ws?.close();
        set({ activeConversationId: null, messages: [], ws: null });
      }
      set((s) => ({
        conversations: s.conversations.filter((c) => c.id !== id),
      }));
    } catch (error) {
      set({ 
        error: { 
          message: "Fehler beim Löschen der Konversation", 
          details: error 
        } 
      });
    }
  },

  sendMessage: (content: string) => {
    const { ws, activeConversationId } = get();
    if (!ws || !activeConversationId) return;

    set((s) => ({
      isThinking: true,
      statusText: "Sende...",
      progress: null,
      error: null,
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

    try {
      ws.send(content);
    } catch (error) {
      set({ 
        isThinking: false, 
        error: { 
          message: "Fehler beim Senden der Nachricht", 
          details: error 
        } 
      });
    }
  },

  clearError: () => set({ error: null }),
}));
