import { useCallback } from 'react'
import { debug as logDebug } from '../utils/logger.js'

// Custom hook for managing notifications
export const useNotifications = () => {
  
  const showToast = useCallback((notification) => {
    const event = new CustomEvent('createNotification', { detail: notification })
    window.dispatchEvent(event)
  }, [])

  const showSuccess = useCallback((message, title = 'Success', options = {}) => {
    showToast({
      type: 'success',
      title,
      message,
      duration: options.duration || 5000,
      action: options.action,
      persistent: options.persistent || false
    })
  }, [showToast])

  const showError = useCallback((message, title = 'Error', options = {}) => {
    showToast({
      type: 'error',
      title,
      message,
      duration: options.duration || 8000,
      action: options.action,
      persistent: options.persistent || false
    })
  }, [showToast])

  const showWarning = useCallback((message, title = 'Warning', options = {}) => {
    showToast({
      type: 'warning',
      title,
      message,
      duration: options.duration || 6000,
      action: options.action,
      persistent: options.persistent || false
    })
  }, [showToast])

  const showInfo = useCallback((message, title = 'Info', options = {}) => {
    showToast({
      type: 'info',
      title,
      message,
      duration: options.duration || 5000,
      action: options.action,
      persistent: options.persistent || false
    })
  }, [showToast])

  // Specific notification types
  const notifyGoalMilestone = useCallback((goalTitle, milestone) => {
    const event = new CustomEvent('goalMilestone', { 
      detail: { goalTitle, milestone } 
    })
    window.dispatchEvent(event)
  }, [])

  const notifyContentPublished = useCallback((title, platform) => {
    const event = new CustomEvent('contentPublished', { 
      detail: { title, platform } 
    })
    window.dispatchEvent(event)
  }, [])

  const notifyWorkflowCompleted = useCallback((workflowType, result) => {
    const event = new CustomEvent('workflowCompleted', { 
      detail: { workflowType, result } 
    })
    window.dispatchEvent(event)
  }, [])

  const notifySystemAlert = useCallback((message, severity = 'warning') => {
    const event = new CustomEvent('systemAlert', { 
      detail: { message, severity } 
    })
    window.dispatchEvent(event)
  }, [])

  const notifyApiError = useCallback((message, retryAction = null) => {
    const event = new CustomEvent('apiError', { 
      detail: { message, retryAction } 
    })
    window.dispatchEvent(event)
  }, [])

  // Batch notifications for multiple operations
  const showBatchResults = useCallback((results) => {
    const successes = results.filter(r => r.success)
    const failures = results.filter(r => !r.success)

    if (successes.length > 0) {
      showSuccess(
        `${successes.length} operation${successes.length > 1 ? 's' : ''} completed successfully`,
        'Batch Operation Complete'
      )
    }

    if (failures.length > 0) {
      showError(
        `${failures.length} operation${failures.length > 1 ? 's' : ''} failed`,
        'Some Operations Failed',
        {
          duration: 10000,
          action: {
            label: 'View Details',
            onClick: () => logDebug('Failed operations:', failures)
          }
        }
      )
    }
  }, [showSuccess, showError])

  // Progress notifications for long-running operations
  const showProgress = useCallback((message, progress = null) => {
    showInfo(
      progress ? `${message} (${progress}%)` : message,
      'Processing...',
      { duration: 2000 }
    )
  }, [showInfo])

  return {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    notifyGoalMilestone,
    notifyContentPublished,
    notifyWorkflowCompleted,
    notifySystemAlert,
    notifyApiError,
    showBatchResults,
    showProgress
  }
}

export default useNotifications