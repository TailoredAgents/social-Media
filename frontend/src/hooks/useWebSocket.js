import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export const useWebSocket = () => {
  const { user } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const [connectionError, setConnectionError] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const heartbeatIntervalRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 1000 // Start with 1 second

  // Message handlers
  const messageHandlersRef = useRef(new Map())

  const connect = useCallback(() => {
    if (!user?.id || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const wsUrl = `${WS_BASE_URL}/api/inbox/ws/${user.id}`
      console.log('Connecting to WebSocket:', wsUrl)
      
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setConnectionError(null)
        reconnectAttemptsRef.current = 0

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'heartbeat',
              timestamp: new Date().toISOString()
            }))
          }
        }, 30000) // Send heartbeat every 30 seconds
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('WebSocket message received:', message)
          
          setLastMessage(message)
          
          // Call registered handlers
          const handler = messageHandlersRef.current.get(message.type)
          if (handler) {
            handler(message)
          }
          
          // Call global handler if it exists
          const globalHandler = messageHandlersRef.current.get('*')
          if (globalHandler) {
            globalHandler(message)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        setIsConnected(false)
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }

        // Attempt to reconnect unless it was a manual close
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current)
          console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionError('Max reconnection attempts reached')
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionError('WebSocket connection error')
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionError('Failed to create connection')
    }
  }, [user?.id])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setIsConnected(false)
    setConnectionError(null)
    reconnectAttemptsRef.current = 0
  }, [])

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    } else {
      console.warn('WebSocket not connected, message not sent:', message)
      return false
    }
  }, [])

  const addMessageHandler = useCallback((messageType, handler) => {
    messageHandlersRef.current.set(messageType, handler)
    
    // Return cleanup function
    return () => {
      messageHandlersRef.current.delete(messageType)
    }
  }, [])

  const removeMessageHandler = useCallback((messageType) => {
    messageHandlersRef.current.delete(messageType)
  }, [])

  // Auto-connect when user is available
  useEffect(() => {
    if (user?.id) {
      connect()
    } else {
      disconnect()
    }

    // Cleanup on unmount
    return () => {
      disconnect()
    }
  }, [user?.id, connect, disconnect])

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden - reduce activity
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }
      } else {
        // Page is visible - resume activity
        if (wsRef.current?.readyState === WebSocket.OPEN && !heartbeatIntervalRef.current) {
          heartbeatIntervalRef.current = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({
                type: 'heartbeat',
                timestamp: new Date().toISOString()
              }))
            }
          }, 30000)
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  return {
    isConnected,
    lastMessage,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    addMessageHandler,
    removeMessageHandler
  }
}

// Specialized hook for social inbox
export const useSocialInboxWebSocket = () => {
  const webSocket = useWebSocket()
  const [newInteractions, setNewInteractions] = useState([])
  const [interactionUpdates, setInteractionUpdates] = useState([])
  const [responseGenerated, setResponseGenerated] = useState(null)
  const [responseSent, setResponseSent] = useState(null)

  useEffect(() => {
    if (!webSocket.isConnected) return

    // Handle new interactions
    const removeNewInteractionHandler = webSocket.addMessageHandler('new_interaction', (message) => {
      console.log('New interaction received:', message)
      setNewInteractions(prev => [message.data.interaction, ...prev])
    })

    // Handle interaction updates
    const removeUpdateHandler = webSocket.addMessageHandler('interaction_update', (message) => {
      console.log('Interaction updated:', message)
      setInteractionUpdates(prev => [message.data, ...prev])
    })

    // Handle response generation
    const removeResponseGeneratedHandler = webSocket.addMessageHandler('response_generated', (message) => {
      console.log('Response generated:', message)
      setResponseGenerated(message.data)
    })

    // Handle response sent
    const removeResponseSentHandler = webSocket.addMessageHandler('interaction_responded', (message) => {
      console.log('Response sent:', message)
      setResponseSent(message.data)
    })

    // Handle notifications
    const removeNotificationHandler = webSocket.addMessageHandler('notification', (message) => {
      console.log('Notification received:', message)
      // Could integrate with a toast notification system
    })

    // Handle errors
    const removeErrorHandler = webSocket.addMessageHandler('error', (message) => {
      console.error('WebSocket error:', message)
    })

    return () => {
      removeNewInteractionHandler()
      removeUpdateHandler()
      removeResponseGeneratedHandler()
      removeResponseSentHandler()
      removeNotificationHandler()
      removeErrorHandler()
    }
  }, [webSocket])

  // Clear arrays periodically to prevent memory leaks
  useEffect(() => {
    const interval = setInterval(() => {
      setNewInteractions(prev => prev.slice(0, 50)) // Keep only last 50
      setInteractionUpdates(prev => prev.slice(0, 50))
    }, 60000) // Every minute

    return () => clearInterval(interval)
  }, [])

  return {
    ...webSocket,
    newInteractions,
    interactionUpdates,
    responseGenerated,
    responseSent,
    clearNewInteractions: () => setNewInteractions([]),
    clearInteractionUpdates: () => setInteractionUpdates([]),
    clearResponseGenerated: () => setResponseGenerated(null),
    clearResponseSent: () => setResponseSent(null)
  }
}