import { useState, useEffect } from 'react'
import NotificationToast from './NotificationToast'

const NotificationContainer = () => {
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    // Listen for notification events
    const handleCreateNotification = (event) => {
      const notification = {
        id: Date.now() + Math.random(),
        ...event.detail
      }
      
      setNotifications(prev => [...prev, notification])
    }

    // Listen for specific notification types
    const handleGoalMilestone = (event) => {
      const { goalTitle, milestone } = event.detail
      const notification = {
        id: Date.now() + Math.random(),
        type: 'success',
        title: 'Goal Milestone Reached!',
        message: `${goalTitle}: ${milestone.description}`,
        duration: 8000
      }
      setNotifications(prev => [...prev, notification])
    }

    const handleContentPublished = (event) => {
      const { title, platform } = event.detail
      const notification = {
        id: Date.now() + Math.random(),
        type: 'success',
        title: 'Content Published',
        message: `"${title}" has been published to ${platform}`,
        duration: 5000
      }
      setNotifications(prev => [...prev, notification])
    }

    const handleWorkflowCompleted = (event) => {
      const { workflowType, result } = event.detail
      const notification = {
        id: Date.now() + Math.random(),
        type: result.success ? 'success' : 'warning',
        title: 'Workflow Complete',
        message: `${workflowType} workflow has ${result.success ? 'completed successfully' : 'completed with warnings'}`,
        duration: 6000
      }
      setNotifications(prev => [...prev, notification])
    }

    const handleSystemAlert = (event) => {
      const { message, severity } = event.detail
      const notification = {
        id: Date.now() + Math.random(),
        type: severity,
        title: 'System Alert',
        message,
        duration: severity === 'error' ? 10000 : 6000,
        persistent: severity === 'error'
      }
      setNotifications(prev => [...prev, notification])
    }

    const handleApiError = (event) => {
      const { message, retryAction } = event.detail
      const notification = {
        id: Date.now() + Math.random(),
        type: 'error',
        title: 'API Error',
        message,
        duration: 8000,
        action: retryAction ? {
          label: 'Retry',
          onClick: retryAction
        } : null
      }
      setNotifications(prev => [...prev, notification])
    }

    // Add event listeners
    window.addEventListener('createNotification', handleCreateNotification)
    window.addEventListener('goalMilestone', handleGoalMilestone)
    window.addEventListener('contentPublished', handleContentPublished)
    window.addEventListener('workflowCompleted', handleWorkflowCompleted)
    window.addEventListener('systemAlert', handleSystemAlert)
    window.addEventListener('apiError', handleApiError)

    // Cleanup
    return () => {
      window.removeEventListener('createNotification', handleCreateNotification)
      window.removeEventListener('goalMilestone', handleGoalMilestone)
      window.removeEventListener('contentPublished', handleContentPublished)
      window.removeEventListener('workflowCompleted', handleWorkflowCompleted)
      window.removeEventListener('systemAlert', handleSystemAlert)
      window.removeEventListener('apiError', handleApiError)
    }
  }, [])

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const dismissAll = () => {
    setNotifications([])
  }

  return (
    <div className="fixed top-0 right-0 z-50 p-6 space-y-4 pointer-events-none">
      {notifications.length > 3 && (
        <div className="pointer-events-auto">
          <button
            onClick={dismissAll}
            className="mb-2 text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Dismiss all ({notifications.length})
          </button>
        </div>
      )}
      
      {notifications.slice(-5).map((notification) => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onDismiss={dismissNotification}
        />
      ))}
    </div>
  )
}

export default NotificationContainer