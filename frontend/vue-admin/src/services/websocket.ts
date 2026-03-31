type MessageHandler = (data: any) => void
type ConnectionHandler = () => void

interface WebSocketOptions {
  url: string
  onMessage?: MessageHandler
  onOpen?: ConnectionHandler
  onClose?: ConnectionHandler
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private onMessage: MessageHandler
  private onOpen: ConnectionHandler
  private onClose: ConnectionHandler
  private onError: (error: Event) => void
  private reconnectInterval: number
  private maxReconnectAttempts: number
  private reconnectAttempts: number = 0
  private isConnecting: boolean = false
  private shouldReconnect: boolean = true
  private messageQueue: any[] = []

  constructor(options: WebSocketOptions) {
    this.url = options.url
    this.onMessage = options.onMessage || (() => {})
    this.onOpen = options.onOpen || (() => {})
    this.onClose = options.onClose || (() => {})
    this.onError = options.onError || (() => {})
    this.reconnectInterval = options.reconnectInterval || 3000
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5
  }

  connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      this.isConnecting = true
      this.shouldReconnect = true

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = this.url.startsWith('ws') ? this.url : `${protocol}//${host}${this.url}`

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.flushMessageQueue()
        this.onOpen()
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.onMessage(data)
        } catch (e) {
          this.onMessage(event.data)
        }
      }

      this.ws.onclose = (event) => {
        this.isConnecting = false
        this.ws = null
        this.onClose()
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        this.isConnecting = false
        this.onError(error)
        reject(error)
      }
    })
  }

  private attemptReconnect() {
    if (!this.shouldReconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return
    }

    this.reconnectAttempts++
    setTimeout(() => {
      this.connect().catch(() => {})
    }, this.reconnectInterval)
  }

  private flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()
      this.ws!.send(JSON.stringify(message))
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      this.messageQueue.push(data)
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export function createWebSocket(options: WebSocketOptions): WebSocketManager {
  return new WebSocketManager(options)
}

export type { WebSocketOptions, WebSocketManager }
