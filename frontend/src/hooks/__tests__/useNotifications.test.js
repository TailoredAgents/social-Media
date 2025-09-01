import { renderHook, act } from '@testing-library/react'

// Mock logger before importing useNotifications
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
}))

import { useNotifications } from '../useNotifications'

// Mock window.dispatchEvent
const mockDispatchEvent = jest.fn()
Object.defineProperty(window, 'dispatchEvent', {
  value: mockDispatchEvent
})

describe('useNotifications Hook', () => {
  let result

  beforeEach(() => {
    jest.clearAllMocks()
    const { result: hookResult } = renderHook(() => useNotifications())
    result = hookResult
  })

  describe('Basic toast notifications', () => {
    it('shows success notification', () => {
      act(() => {
        result.current.showSuccess('Operation completed')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'success',
            title: 'Success',
            message: 'Operation completed',
            duration: 5000,
            persistent: false
          })
        })
      )
    })

    it('shows error notification with custom options', () => {
      const customAction = { label: 'Retry', onClick: jest.fn() }
      
      act(() => {
        result.current.showError('Something went wrong', 'Custom Error', {
          duration: 10000,
          action: customAction,
          persistent: true
        })
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'error',
            title: 'Custom Error',
            message: 'Something went wrong',
            duration: 10000,
            action: customAction,
            persistent: true
          })
        })
      )
    })

    it('shows warning notification', () => {
      act(() => {
        result.current.showWarning('This is a warning')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'warning',
            title: 'Warning',
            message: 'This is a warning',
            duration: 6000
          })
        })
      )
    })

    it('shows info notification', () => {
      act(() => {
        result.current.showInfo('Information message')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'info',
            title: 'Info',
            message: 'Information message',
            duration: 5000
          })
        })
      )
    })
  })

  describe('Specific notification types', () => {
    it('notifies goal milestone', () => {
      act(() => {
        result.current.notifyGoalMilestone('My Goal', '50% Complete')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'goalMilestone',
          detail: {
            goalTitle: 'My Goal',
            milestone: '50% Complete'
          }
        })
      )
    })

    it('notifies content published', () => {
      act(() => {
        result.current.notifyContentPublished('My Post', 'Twitter')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'contentPublished',
          detail: {
            title: 'My Post',
            platform: 'Twitter'
          }
        })
      )
    })

    it('notifies workflow completed', () => {
      const workflowResult = { success: true, postsCreated: 3 }
      
      act(() => {
        result.current.notifyWorkflowCompleted('daily', workflowResult)
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'workflowCompleted',
          detail: {
            workflowType: 'daily',
            result: workflowResult
          }
        })
      )
    })

    it('notifies system alert', () => {
      act(() => {
        result.current.notifySystemAlert('System maintenance starting', 'info')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'systemAlert',
          detail: {
            message: 'System maintenance starting',
            severity: 'info'
          }
        })
      )
    })

    it('notifies API error with retry action', () => {
      const retryAction = jest.fn()
      
      act(() => {
        result.current.notifyApiError('Network error occurred', retryAction)
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'apiError',
          detail: {
            message: 'Network error occurred',
            retryAction: retryAction
          }
        })
      )
    })
  })

  describe('Batch operations', () => {
    it('shows batch results with successes only', () => {
      const results = [
        { success: true, operation: 'post1' },
        { success: true, operation: 'post2' }
      ]

      act(() => {
        result.current.showBatchResults(results)
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'success',
            title: 'Batch Operation Complete',
            message: '2 operations completed successfully'
          })
        })
      )
    })

    it('shows batch results with failures only', () => {
      const results = [
        { success: false, operation: 'post1', error: 'Failed to post' },
        { success: false, operation: 'post2', error: 'Network error' }
      ]

      act(() => {
        result.current.showBatchResults(results)
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'error',
            title: 'Some Operations Failed',
            message: '2 operations failed',
            duration: 10000,
            action: expect.objectContaining({
              label: 'View Details'
            })
          })
        })
      )
    })

    it('shows batch results with mixed success and failure', () => {
      const results = [
        { success: true, operation: 'post1' },
        { success: false, operation: 'post2', error: 'Failed' }
      ]

      act(() => {
        result.current.showBatchResults(results)
      })

      expect(mockDispatchEvent).toHaveBeenCalledTimes(2)
      
      // Check success notification
      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'success',
            message: '1 operation completed successfully'
          })
        })
      )

      // Check failure notification
      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'error',
            message: '1 operation failed'
          })
        })
      )
    })
  })

  describe('Progress notifications', () => {
    it('shows progress without percentage', () => {
      act(() => {
        result.current.showProgress('Processing data')
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'info',
            title: 'Processing...',
            message: 'Processing data',
            duration: 2000
          })
        })
      )
    })

    it('shows progress with percentage', () => {
      act(() => {
        result.current.showProgress('Uploading files', 75)
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: expect.objectContaining({
            type: 'info',
            title: 'Processing...',
            message: 'Uploading files (75%)',
            duration: 2000
          })
        })
      )
    })
  })

  describe('Custom toast', () => {
    it('dispatches custom notification event', () => {
      const customNotification = {
        type: 'custom',
        title: 'Custom Title',
        message: 'Custom message',
        duration: 3000
      }

      act(() => {
        result.current.showToast(customNotification)
      })

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'createNotification',
          detail: customNotification
        })
      )
    })
  })
})