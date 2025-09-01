import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import NotificationContainer from '../NotificationContainer'

// Mock the NotificationToast component
jest.mock('../NotificationToast', () => {
  return jest.fn(({ notification, onDismiss }) => (
    <div data-testid={`notification-${notification.id}`}>
      <h3>{notification.title}</h3>
      <p>{notification.message}</p>
      <span>{notification.type}</span>
      <button onClick={() => onDismiss(notification.id)}>Dismiss</button>
    </div>
  ))
})

describe('NotificationContainer', () => {
  beforeEach(() => {
    // Clear any existing event listeners
    document.removeEventListener('createNotification', jest.fn())
    document.removeEventListener('goalMilestone', jest.fn())
    document.removeEventListener('contentPublished', jest.fn())
    document.removeEventListener('workflowCompleted', jest.fn())
    document.removeEventListener('apiError', jest.fn())
    document.removeEventListener('connectionError', jest.fn())
  })

  it('renders without crashing', () => {
    render(<NotificationContainer />)
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('displays notifications when createNotification event is fired', async () => {
    render(<NotificationContainer />)
    
    const notificationData = {
      type: 'success',
      title: 'Test Success',
      message: 'This is a test notification',
      duration: 5000
    }
    
    act(() => {
      const event = new CustomEvent('createNotification', { detail: notificationData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Test Success')).toBeInTheDocument()
      expect(screen.getByText('This is a test notification')).toBeInTheDocument()
      expect(screen.getByText('success')).toBeInTheDocument()
    })
  })

  it('handles goal milestone notifications', async () => {
    render(<NotificationContainer />)
    
    const goalData = {
      goalTitle: 'Increase Followers',
      milestone: {
        description: 'Reached 1000 followers'
      }
    }
    
    act(() => {
      const event = new CustomEvent('goalMilestone', { detail: goalData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Goal Milestone Reached!')).toBeInTheDocument()
      expect(screen.getByText('Increase Followers: Reached 1000 followers')).toBeInTheDocument()
      expect(screen.getByText('success')).toBeInTheDocument()
    })
  })

  it('handles content published notifications', async () => {
    render(<NotificationContainer />)
    
    const contentData = {
      title: 'My Amazing Post',
      platform: 'LinkedIn'
    }
    
    act(() => {
      const event = new CustomEvent('contentPublished', { detail: contentData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Content Published')).toBeInTheDocument()
      expect(screen.getByText('"My Amazing Post" has been published to LinkedIn')).toBeInTheDocument()
      expect(screen.getByText('success')).toBeInTheDocument()
    })
  })

  it('handles workflow completed notifications with success', async () => {
    render(<NotificationContainer />)
    
    const workflowData = {
      workflowType: 'Content Generation',
      result: { success: true }
    }
    
    act(() => {
      const event = new CustomEvent('workflowCompleted', { detail: workflowData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Workflow Complete')).toBeInTheDocument()
      expect(screen.getByText('Content Generation workflow has completed successfully')).toBeInTheDocument()
      expect(screen.getByText('success')).toBeInTheDocument()
    })
  })

  it('handles workflow completed notifications with warnings', async () => {
    render(<NotificationContainer />)
    
    const workflowData = {
      workflowType: 'Analytics Sync',
      result: { success: false }
    }
    
    act(() => {
      const event = new CustomEvent('workflowCompleted', { detail: workflowData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Workflow Complete')).toBeInTheDocument()
      expect(screen.getByText('Analytics Sync workflow has completed with warnings')).toBeInTheDocument()
      expect(screen.getByText('warning')).toBeInTheDocument()
    })
  })

  it('handles API error notifications', async () => {
    render(<NotificationContainer />)
    
    const errorData = {
      message: 'Failed to fetch user data',
      statusCode: 500
    }
    
    act(() => {
      const event = new CustomEvent('apiError', { detail: errorData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument()
      expect(screen.getByText('Failed to fetch user data (Status: 500)')).toBeInTheDocument()
      expect(screen.getByText('error')).toBeInTheDocument()
    })
  })

  it('handles connection error notifications', async () => {
    render(<NotificationContainer />)
    
    const connectionData = {
      service: 'Analytics API'
    }
    
    act(() => {
      const event = new CustomEvent('connectionError', { detail: connectionData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Connection Issue')).toBeInTheDocument()
      expect(screen.getByText('Lost connection to Analytics API. Retrying...')).toBeInTheDocument()
      expect(screen.getByText('warning')).toBeInTheDocument()
    })
  })

  it('allows dismissing notifications', async () => {
    render(<NotificationContainer />)
    
    const notificationData = {
      type: 'info',
      title: 'Dismissible',
      message: 'This can be dismissed'
    }
    
    act(() => {
      const event = new CustomEvent('createNotification', { detail: notificationData })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Dismissible')).toBeInTheDocument()
    })
    
    const dismissButton = screen.getByRole('button', { name: /dismiss/i })
    
    act(() => {
      dismissButton.click()
    })
    
    await waitFor(() => {
      expect(screen.queryByText('Dismissible')).not.toBeInTheDocument()
    })
  })

  it('handles multiple notifications simultaneously', async () => {
    render(<NotificationContainer />)
    
    // Create multiple notifications
    const notifications = [
      { type: 'success', title: 'Success 1', message: 'First success' },
      { type: 'error', title: 'Error 1', message: 'First error' },
      { type: 'warning', title: 'Warning 1', message: 'First warning' }
    ]
    
    notifications.forEach(notification => {
      act(() => {
        const event = new CustomEvent('createNotification', { detail: notification })
        document.dispatchEvent(event)
      })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Success 1')).toBeInTheDocument()
      expect(screen.getByText('Error 1')).toBeInTheDocument()
      expect(screen.getByText('Warning 1')).toBeInTheDocument()
    })
    
    // Should have 3 notifications
    const notificationElements = screen.getAllByTestId(/notification-/)
    expect(notificationElements).toHaveLength(3)
  })

  it('generates unique IDs for notifications', async () => {
    render(<NotificationContainer />)
    
    const notificationData = {
      type: 'info',
      title: 'Test',
      message: 'Testing unique IDs'
    }
    
    // Create two identical notifications
    act(() => {
      const event1 = new CustomEvent('createNotification', { detail: notificationData })
      const event2 = new CustomEvent('createNotification', { detail: notificationData })
      document.dispatchEvent(event1)
      document.dispatchEvent(event2)
    })
    
    await waitFor(() => {
      const notifications = screen.getAllByTestId(/notification-/)
      expect(notifications).toHaveLength(2)
      
      // Check that they have different IDs
      const id1 = notifications[0].getAttribute('data-testid')
      const id2 = notifications[1].getAttribute('data-testid')
      expect(id1).not.toBe(id2)
    })
  })

  it('positions notifications correctly in the container', () => {
    render(<NotificationContainer />)
    
    const container = screen.getByTestId('notification-container')
    expect(container).toHaveClass('fixed', 'top-4', 'right-4', 'z-50')
  })

  it('maintains proper notification order (newest first)', async () => {
    render(<NotificationContainer />)
    
    // Create notifications in sequence
    const notifications = [
      { type: 'info', title: 'First', message: 'First notification' },
      { type: 'info', title: 'Second', message: 'Second notification' },
      { type: 'info', title: 'Third', message: 'Third notification' }
    ]
    
    for (const notification of notifications) {
      act(() => {
        const event = new CustomEvent('createNotification', { detail: notification })
        document.dispatchEvent(event)
      })
      
      // Small delay to ensure order
      await new Promise(resolve => setTimeout(resolve, 10))
    }
    
    await waitFor(() => {
      const notificationElements = screen.getAllByTestId(/notification-/)
      expect(notificationElements).toHaveLength(3)
      
      // Check order - newest should be first
      expect(notificationElements[0]).toHaveTextContent('Third')
      expect(notificationElements[1]).toHaveTextContent('Second')
      expect(notificationElements[2]).toHaveTextContent('First')
    })
  })

  it('handles edge cases gracefully', async () => {
    render(<NotificationContainer />)
    
    // Test with minimal data
    act(() => {
      const event = new CustomEvent('createNotification', { 
        detail: { title: 'Minimal' } 
      })
      document.dispatchEvent(event)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Minimal')).toBeInTheDocument()
    })
    
    // Test with empty event detail
    act(() => {
      const event = new CustomEvent('createNotification', { detail: {} })
      document.dispatchEvent(event)
    })
    
    // Should not crash
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('cleans up event listeners on unmount', () => {
    const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener')
    
    const { unmount } = render(<NotificationContainer />)
    
    unmount()
    
    expect(removeEventListenerSpy).toHaveBeenCalledWith('createNotification', expect.any(Function))
    expect(removeEventListenerSpy).toHaveBeenCalledWith('goalMilestone', expect.any(Function))
    expect(removeEventListenerSpy).toHaveBeenCalledWith('contentPublished', expect.any(Function))
    expect(removeEventListenerSpy).toHaveBeenCalledWith('workflowCompleted', expect.any(Function))
    expect(removeEventListenerSpy).toHaveBeenCalledWith('apiError', expect.any(Function))
    expect(removeEventListenerSpy).toHaveBeenCalledWith('connectionError', expect.any(Function))
    
    removeEventListenerSpy.mockRestore()
  })
})