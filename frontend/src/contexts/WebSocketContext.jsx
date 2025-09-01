import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import wsService from '../services/websocket'
import { useAuth } from './AuthContext'
import { info, warn, error as logError } from '../utils/logger'

const WebSocketContext = createContext({})

export const WebSocketProvider = ({ children }) => {
  const { user, isAuthenticated, accessToken } = useAuth()
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  // Connect WebSocket when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user?.id && accessToken) {
      info('Initializing WebSocket connection for user', user.id)
      
      // Connect to WebSocket
      wsService.connect(user.id, accessToken)
        .then(() => {
          setConnectionStatus('connected')
          info('WebSocket connected successfully')
        })
        .catch((error) => {
          logError('Failed to connect WebSocket', error)
          setConnectionStatus('error')
        })

      // Set up event listeners
      const unsubscribers = []

      // Welcome message handler
      unsubscribers.push(
        wsService.on('welcome', (data) => {
          info('Received welcome data', data)
          setUnreadCount(data.unread_notifications || 0)
        })
      )

      // Notification handler
      unsubscribers.push(
        wsService.on('notification', (notification) => {
          info('Received new notification', notification)
          
          // Add to notifications list
          setNotifications(prev => [notification, ...prev])
          
          // Increment unread count
          setUnreadCount(prev => prev + 1)
          
          // Show browser notification if permitted
          if (Notification.permission === 'granted') {
            new Notification(notification.title, {
              body: notification.message,
              icon: '/favicon.ico',
              tag: notification.id
            })
          }
        })
      )

      // System notification handler
      unsubscribers.push(
        wsService.on('system_notification', (notification) => {
          info('Received system notification', notification)
          
          // Add to notifications with system flag
          setNotifications(prev => [
            { ...notification, isSystem: true },
            ...prev
          ])
        })
      )

      // Notification read handler
      unsubscribers.push(
        wsService.on('notification_read', (data) => {
          info('Notification marked as read', data)
          
          // Update notification in list
          setNotifications(prev =>
            prev.map(n =>
              n.id === data.notification_id
                ? { ...n, is_read: true }
                : n
            )
          )
          
          // Decrement unread count
          setUnreadCount(prev => Math.max(0, prev - 1))
        })
      )

      // Connection failed handler
      unsubscribers.push(
        wsService.on('connection_failed', (data) => {
          warn('WebSocket connection failed', data)
          setConnectionStatus('error')
        })
      )

      // Error handler
      unsubscribers.push(
        wsService.on('error', (error) => {
          logError('WebSocket error', error)
          setConnectionStatus('error')
        })
      )

      // Cleanup on unmount or user change
      return () => {
        info('Cleaning up WebSocket connection')
        unsubscribers.forEach(unsub => unsub())
        wsService.disconnect()
        setConnectionStatus('disconnected')
      }
    } else {
      // Disconnect if not authenticated
      if (wsService.isConnected()) {
        info('User not authenticated, disconnecting WebSocket')
        wsService.disconnect()
        setConnectionStatus('disconnected')
      }
    }
  }, [isAuthenticated, user, accessToken])

  // Mark notification as read
  const markAsRead = useCallback((notificationId) => {
    wsService.markNotificationRead(notificationId)
  }, [])

  // Clear all notifications (local only)
  const clearNotifications = useCallback(() => {
    setNotifications([])
    setUnreadCount(0)
  }, [])

  // Remove a specific notification (local only)
  const removeNotification = useCallback((notificationId) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId))
    
    // Decrement unread count if notification was unread
    const notification = notifications.find(n => n.id === notificationId)
    if (notification && !notification.is_read) {
      setUnreadCount(prev => Math.max(0, prev - 1))
    }
  }, [notifications])

  // Request browser notification permission
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission()
      info('Notification permission:', permission)
      return permission
    }
    return Notification.permission
  }, [])

  // Get connection status string
  const getConnectionStatusText = useCallback(() => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'error':
        return 'Connection Error'
      case 'disconnected':
      default:
        return 'Disconnected'
    }
  }, [connectionStatus])

  const value = {
    // State
    connectionStatus,
    notifications,
    unreadCount,
    
    // Actions
    markAsRead,
    clearNotifications,
    removeNotification,
    requestNotificationPermission,
    
    // Helpers
    getConnectionStatusText,
    isConnected: connectionStatus === 'connected'
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

export default WebSocketContext