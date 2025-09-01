import React, { useEffect } from 'react'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { useAuth } from '../../contexts/AuthContext'
import NotificationToast from './NotificationToast'

const RealTimeNotificationContainer = () => {
  const { isAuthenticated } = useAuth()
  const { 
    notifications, 
    unreadCount,
    connectionStatus, 
    markAsRead, 
    removeNotification,
    requestNotificationPermission 
  } = useWebSocket()

  // Request browser notification permission on mount
  useEffect(() => {
    requestNotificationPermission()
  }, [requestNotificationPermission])

  const handleDismiss = (notificationId) => {
    // Mark as read via WebSocket and remove locally
    markAsRead(notificationId)
    removeNotification(notificationId)
  }

  const getNotificationType = (notification) => {
    // Map notification priority to toast type
    switch (notification.priority) {
      case 'urgent':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'success'
      case 'low':
      default:
        return 'info'
    }
  }

  const getNotificationDuration = (notification) => {
    // Different durations based on priority and type
    switch (notification.priority) {
      case 'urgent':
        return 10000 // 10 seconds for urgent
      case 'high':
        return 8000  // 8 seconds for high priority
      case 'medium':
        return 5000  // 5 seconds for medium
      case 'low':
      default:
        return 4000  // 4 seconds for low priority
    }
  }

  // Only show recent notifications (last 5) to avoid UI clutter
  const recentNotifications = notifications.slice(0, 5)

  return (
    <div className="fixed top-0 right-0 z-50 p-4 space-y-4">
      {/* Connection Status Indicator (only show if authenticated and not connected) */}
      {isAuthenticated && connectionStatus !== 'connected' && (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-2 rounded-md shadow-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
            </div>
            <div className="ml-2 text-sm">
              Real-time notifications {connectionStatus}
            </div>
          </div>
        </div>
      )}

      {/* Notification Toasts (only show for authenticated users) */}
      {isAuthenticated && recentNotifications.map(notification => (
        <NotificationToast
          key={notification.id}
          id={notification.id}
          type={getNotificationType(notification)}
          title={notification.title}
          message={notification.message}
          duration={getNotificationDuration(notification)}
          onDismiss={() => handleDismiss(notification.id)}
          showProgress={notification.priority === 'urgent' || notification.priority === 'high'}
          isSystem={notification.isSystem}
          metadata={notification.metadata}
        />
      ))}

      {/* Unread Count Badge (only show for authenticated users) */}
      {isAuthenticated && unreadCount > 0 && recentNotifications.length === 0 && (
        <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium shadow-lg">
          {unreadCount} new notifications
        </div>
      )}
    </div>
  )
}

export default RealTimeNotificationContainer