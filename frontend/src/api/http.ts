const BASE_URL = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Conversation {
  id: number;
  title: string;
  status: string;
  current_phase: string;
  company_profile_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  metadata_json: string | null;
  created_at: string;
}

export const api = {
  listConversations: () => request<Conversation[]>("/conversations"),

  createConversation: (title = "Neue Konversation") =>
    request<Conversation>("/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),

  deleteConversation: (id: number) =>
    request<void>(`/conversations/${id}`, { method: "DELETE" }),

  updateConversation: (id: number, data: { title?: string; status?: string }) =>
    request<Conversation>(`/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getMessages: (conversationId: number) =>
    request<Message[]>(`/conversations/${conversationId}/messages`),
};
