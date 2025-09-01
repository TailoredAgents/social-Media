import { info, warn, error as logError } from '../utils/logger.js'

// Use the API base URL to construct WebSocket URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')

class WebSocketService {
  constructor() {
    this.ws = null
    this.userId = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.listeners = new Map()
    this.isConnecting = false
    this.heartbeatInterval = null
  }

  connect(userId, token) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      info('WebSocket already connected')
      return Promise.resolve()
    }

    if (this.isConnecting) {
      info('WebSocket connection already in progress')
      return Promise.resolve()
    }

    this.isConnecting = true
    this.userId = userId
    this.token = token

    return new Promise((resolve, reject) => {
      try {
        // Construct WebSocket URL with user_id parameter
        const wsUrl = `${WS_BASE_URL}/api/notifications/ws?user_id=${userId}`
        
        info(`Connecting to WebSocket: ${wsUrl}`)
        info(`WebSocket base URL derived from: ${API_BASE_URL}`)
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          info('WebSocket connected successfully')
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            logError('Failed to parse WebSocket message', error)
          }
        }

        this.ws.onerror = (error) => {
          logError('WebSocket error', error)
          this.isConnecting = false
          reject(error)
        }

        this.ws.onclose = (event) => {
          info(`WebSocket closed: ${event.code} - ${event.reason}`)
          this.isConnecting = false
          this.stopHeartbeat()
          
          // Attempt to reconnect if not intentionally closed
          if (event.code !== 1000) {
            this.reconnect()
          }
        }

      } catch (error) {
        logError('Failed to create WebSocket connection', error)
        this.isConnecting = false
        reject(error)
      }
    })
  }

  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      warn('Max reconnection attempts reached')
      this.notifyListeners('connection_failed', {
        message: 'Unable to establish WebSocket connection'
      })
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    info(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId)
      }
    }, delay)
  }

  disconnect() {
    if (this.ws) {
      info('Disconnecting WebSocket')
      this.stopHeartbeat()
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
      this.userId = null
      this.reconnectAttempts = 0
    }
  }

  startHeartbeat() {
    this.stopHeartbeat()
    
    // Send ping every 30 seconds to keep connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' })
      }
    }, 30000)
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  handleMessage(data) {
    const { type, data: messageData, timestamp } = data

    switch (type) {
      case 'welcome':
        info('Received welcome message', messageData)
        this.notifyListeners('welcome', messageData)
        break
        
      case 'notification':
        info('Received notification', messageData)
        this.notifyListeners('notification', messageData)
        break
        
      case 'system_notification':
        info('Received system notification', messageData)
        this.notifyListeners('system_notification', messageData)
        break
        
      case 'pong':
        // Heartbeat response - no action needed
        break
        
      case 'marked_read':
        info('Notification marked as read', messageData)
        this.notifyListeners('notification_read', messageData)
        break
        
      case 'error':
        logError('WebSocket error message', messageData)
        this.notifyListeners('error', messageData)
        break
        
      default:
        warn('Unknown message type', type, messageData)
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      warn('WebSocket not connected, cannot send message')
    }
  }

  markNotificationRead(notificationId) {
    this.send({
      type: 'mark_read',
      notification_id: notificationId
    })
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event).add(callback)
    
    // Return unsubscribe function
    return () => this.off(event, callback)
  }

  off(event, callback) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.delete(callback)
      if (callbacks.size === 0) {
        this.listeners.delete(event)
      }
    }
  }

  notifyListeners(event, data) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          logError(`Error in WebSocket listener for ${event}`, error)
        }
      })
    }
  }

  // Connection status
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }

  getConnectionStatus() {
    if (!this.ws) return 'disconnected'
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting'
      case WebSocket.OPEN:
        return 'connected'
      case WebSocket.CLOSING:
        return 'closing'
      case WebSocket.CLOSED:
        return 'closed'
      default:
        return 'unknown'
    }
  }
}

// Create singleton instance
const wsService = new WebSocketService()

export default wsService