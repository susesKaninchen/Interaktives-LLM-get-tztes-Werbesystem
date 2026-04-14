export interface WsMessage {
  type: "message" | "stream_start" | "stream_token" | "stream_end" | "error" | "status";
  content: string;
  conversation_id?: number;
  phase?: string;
}

export type WsHandler = (msg: WsMessage) => void;

// Vite's HMR patches the global WebSocket. Grab the native one.
const NativeWebSocket = globalThis.WebSocket;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private handlers: WsHandler[] = [];
  private conversationId: number;

  constructor(conversationId: number) {
    this.conversationId = conversationId;
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/chat/${this.conversationId}`;

    this.ws = new NativeWebSocket(url);

    this.ws.onopen = () => {
      console.log("WebSocket connected:", url);
    };

    this.ws.onmessage = (event: MessageEvent) => {
      const msg: WsMessage = JSON.parse(event.data);
      this.handlers.forEach((h) => h(msg));
    };

    this.ws.onerror = () => {
      this.handlers.forEach((h) =>
        h({ type: "error", content: "WebSocket connection error" })
      );
    };

    this.ws.onclose = () => {
      this.ws = null;
    };
  }

  send(content: string) {
    if (this.ws?.readyState === NativeWebSocket.OPEN) {
      this.ws.send(JSON.stringify({ content }));
    }
  }

  onMessage(handler: WsHandler) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  close() {
    if (this.ws && typeof this.ws.close === "function") {
      this.ws.close();
    }
    this.ws = null;
    this.handlers = [];
  }

  get connected() {
    return this.ws?.readyState === NativeWebSocket.OPEN;
  }
}
