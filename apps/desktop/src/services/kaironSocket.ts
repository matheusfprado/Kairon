import type { ClientEvent, ServerEvent } from "../types/kairon";

type EventHandler = (event: ServerEvent) => void;
type StatusHandler = (connected: boolean) => void;

export class KaironSocket {
  private socket: WebSocket | null = null;
  private retryTimer: number | null = null;
  private reconnectEnabled = true;

  constructor(
    private readonly url: string,
    private readonly onEvent: EventHandler,
    private readonly onStatus: StatusHandler,
  ) {}

  connect(): void {
    if (!this.reconnectEnabled) {
      return;
    }

    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.onopen = () => {
      this.onStatus(true);
    };

    socket.onmessage = (message) => {
      const event = JSON.parse(message.data as string) as ServerEvent;
      this.onEvent(event);
    };

    socket.onclose = () => {
      if (this.socket !== socket) {
        return;
      }
      this.socket = null;
      this.onStatus(false);
      this.scheduleReconnect();
    };

    socket.onerror = () => {
      this.onStatus(false);
    };
  }

  send(event: ClientEvent): boolean {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(event));
      return true;
    }
    return false;
  }

  disconnect(): void {
    this.reconnectEnabled = false;
    if (this.retryTimer !== null) {
      window.clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
    const socket = this.socket;
    this.socket = null;
    if (socket !== null) {
      socket.onclose = null;
      socket.onerror = null;
      socket.close();
    }
    this.onStatus(false);
  }

  private scheduleReconnect(): void {
    if (!this.reconnectEnabled || this.retryTimer !== null) {
      return;
    }

    this.retryTimer = window.setTimeout(() => {
      this.retryTimer = null;
      this.connect();
    }, 1500);
  }
}
