import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import NotificationSystem from '../NotificationSystem'

// Mock the enhanced API hook
jest.mock('../../hooks/useEnhancedApi', () => ({
  useEnhancedApi: jest.fn(() => ({
    notifications: {
      create: jest.fn(),
      markAsRead: jest.fn(),
      clear: jest.fn()
    }
  }))
}))

// Mock the notifications hook
const mockNotifications = []
const mockAddNotification = jest.fn()
const mockRemoveNotification = jest.fn()
const mockClearNotifications = jest.fn()
const mockMarkAsRead = jest.fn()

jest.mock('../../hooks/useNotifications', () => ({
  useNotifications: jest.fn(() => ({
    notifications: mockNotifications,
    addNotification: mockAddNotification,
    removeNotification: mockRemoveNotification,
    clearNotifications: mockClearNotifications,
    markAsRead: mockMarkAsRead
  }))
}))

// Mock portal creation
jest.mock('react-dom', () => ({
  ...jest.requireActual('react-dom'),
  createPortal: jest.fn((element) => element)
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn()
}))

describe('NotificationSystem', () => {
  let queryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    })
    jest.clearAllMocks()
    
    // Reset mock notifications
    mockNotifications.length = 0
  })

  const renderWithProvider = (component) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('renders without crashing when no notifications', () => {
    renderWithProvider(<NotificationSystem />)
    
    // Should render notification container
    expect(screen.getByTestId('notification-system')).toBeInTheDocument()
  })

  it('displays notifications when they exist', () => {
    mockNotifications.push(
      {
        id: '1',
        type: 'success',
        title: 'Success!',
        message: 'Operation completed',
        duration: 5000,
        timestamp: Date.now()
      },
      {
        id: '2',
        type: 'error',
        title: 'Error!',
        message: 'Something went wrong',
        duration: 0,
        timestamp: Date.now()
      }
    )

    renderWithProvider(<NotificationSystem />)
    
    expect(screen.getByText('Success!')).toBeInTheDocument()
    expect(screen.getByText('Operation completed')).toBeInTheDocument()
    expect(screen.getByText('Error!')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('shows different icons for different notification types', () => {
    mockNotifications.push(
      { id: '1', type: 'success', title: 'Success', message: 'Success message' },
      { id: '2', type: 'error', title: 'Error', message: 'Error message' },
      { id: '3', type: 'warning', title: 'Warning', message: 'Warning message' },
      { id: '4', type: 'info', title: 'Info', message: 'Info message' }
    )

    renderWithProvider(<NotificationSystem />)
    
    // Check that all notifications are rendered
    expect(screen.getByText('Success')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Warning')).toBeInTheDocument()
    expect(screen.getByText('Info')).toBeInTheDocument()
  })

  it('allows closing notifications manually', async () => {
    mockNotifications.push({
      id: '1',
      type: 'info',
      title: 'Test',
      message: 'Test message',
      duration: 0
    })

    renderWithProvider(<NotificationSystem />)
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    await waitFor(() => {
      expect(mockRemoveNotification).toHaveBeenCalledWith('1')
    })
  })

  it('auto-dismisses notifications with duration', async () => {
    jest.useFakeTimers()
    
    mockNotifications.push({
      id: '1',
      type: 'success',
      title: 'Auto-dismiss',
      message: 'This will auto-dismiss',
      duration: 1000
    })

    renderWithProvider(<NotificationSystem />)
    
    expect(screen.getByText('Auto-dismiss')).toBeInTheDocument()
    
    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(1300) // duration + animation time
    })
    
    await waitFor(() => {
      expect(mockRemoveNotification).toHaveBeenCalledWith('1')
    })
    
    jest.useRealTimers()
  })

  it('handles notification actions when provided', () => {
    const mockAction = jest.fn()
    
    mockNotifications.push({
      id: '1',
      type: 'info',
      title: 'Action Test',
      message: 'Click the action',
      actions: [
        {
          label: 'Test Action',
          action: mockAction,
          style: 'primary'
        }
      ]
    })

    renderWithProvider(<NotificationSystem />)
    
    const actionButton = screen.getByRole('button', { name: /test action/i })
    fireEvent.click(actionButton)
    
    expect(mockAction).toHaveBeenCalledWith('1')
  })

  it('handles multiple actions per notification', () => {
    const mockPrimaryAction = jest.fn()
    const mockSecondaryAction = jest.fn()
    
    mockNotifications.push({
      id: '1',
      type: 'warning',
      title: 'Multiple Actions',
      message: 'Choose an action',
      actions: [
        {
          label: 'Primary',
          action: mockPrimaryAction,
          style: 'primary'
        },
        {
          label: 'Secondary',
          action: mockSecondaryAction,
          style: 'secondary'
        }
      ]
    })

    renderWithProvider(<NotificationSystem />)
    
    const primaryButton = screen.getByRole('button', { name: /primary/i })
    const secondaryButton = screen.getByRole('button', { name: /secondary/i })
    
    fireEvent.click(primaryButton)
    fireEvent.click(secondaryButton)
    
    expect(mockPrimaryAction).toHaveBeenCalledWith('1')
    expect(mockSecondaryAction).toHaveBeenCalledWith('1')
  })

  it('handles notifications with progress indication', () => {
    mockNotifications.push({
      id: '1',
      type: 'info',
      title: 'Progress Test',
      message: 'Upload in progress',
      progress: 65
    })

    renderWithProvider(<NotificationSystem />)
    
    expect(screen.getByText('Progress Test')).toBeInTheDocument()
    expect(screen.getByText('Upload in progress')).toBeInTheDocument()
    
    // Check that progress bar exists and has correct value
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toBeInTheDocument()
    expect(progressBar).toHaveAttribute('aria-valuenow', '65')
  })

  it('displays notification history when enabled', () => {
    renderWithProvider(<NotificationSystem showHistory={true} />)
    
    const historyButton = screen.getByRole('button', { name: /notification history/i })
    expect(historyButton).toBeInTheDocument()
    
    fireEvent.click(historyButton)
    
    // Should show history panel
    expect(screen.getByText('Notification History')).toBeInTheDocument()
  })

  it('clears all notifications when clear button is clicked', async () => {
    mockNotifications.push(
      { id: '1', type: 'info', title: 'Test 1', message: 'Message 1' },
      { id: '2', type: 'success', title: 'Test 2', message: 'Message 2' }
    )

    renderWithProvider(<NotificationSystem showHistory={true} />)
    
    const historyButton = screen.getByRole('button', { name: /notification history/i })
    fireEvent.click(historyButton)
    
    const clearButton = screen.getByRole('button', { name: /clear all/i })
    fireEvent.click(clearButton)
    
    await waitFor(() => {
      expect(mockClearNotifications).toHaveBeenCalled()
    })
  })

  it('positions notifications correctly', () => {
    mockNotifications.push({
      id: '1',
      type: 'info',
      title: 'Position Test',
      message: 'Check positioning'
    })

    renderWithProvider(<NotificationSystem position="top-right" />)
    
    const container = screen.getByTestId('notification-system')
    expect(container).toHaveClass('top-4', 'right-4')
  })

  it('supports different positioning options', () => {
    const positions = [
      { position: 'top-left', classes: ['top-4', 'left-4'] },
      { position: 'top-right', classes: ['top-4', 'right-4'] },
      { position: 'bottom-left', classes: ['bottom-4', 'left-4'] },
      { position: 'bottom-right', classes: ['bottom-4', 'right-4'] }
    ]

    positions.forEach(({ position, classes }) => {
      const { unmount } = renderWithProvider(<NotificationSystem position={position} />)
      
      const container = screen.getByTestId('notification-system')
      classes.forEach(className => {
        expect(container).toHaveClass(className)
      })
      
      unmount()
    })
  })

  it('limits maximum number of visible notifications', () => {
    // Add more notifications than the max limit
    for (let i = 1; i <= 8; i++) {
      mockNotifications.push({
        id: i.toString(),
        type: 'info',
        title: `Notification ${i}`,
        message: `Message ${i}`
      })
    }

    renderWithProvider(<NotificationSystem maxNotifications={5} />)
    
    // Should only show 5 notifications
    const notifications = screen.getAllByText(/Notification \d/)
    expect(notifications).toHaveLength(5)
    
    // Should show the most recent 5
    expect(screen.getByText('Notification 4')).toBeInTheDocument()
    expect(screen.getByText('Notification 5')).toBeInTheDocument()
    expect(screen.getByText('Notification 6')).toBeInTheDocument()
    expect(screen.getByText('Notification 7')).toBeInTheDocument()
    expect(screen.getByText('Notification 8')).toBeInTheDocument()
    expect(screen.queryByText('Notification 1')).not.toBeInTheDocument()
  })

  it('handles animation transitions properly', async () => {
    jest.useFakeTimers()
    
    mockNotifications.push({
      id: '1',
      type: 'success',
      title: 'Animation Test',
      message: 'Testing animations'
    })

    const { rerender } = renderWithProvider(<NotificationSystem />)
    
    // Initially should not be visible
    const notification = screen.getByText('Animation Test').closest('[data-testid^="notification-"]')
    expect(notification).toHaveClass('opacity-0')
    
    // After animation delay, should be visible
    act(() => {
      jest.advanceTimersByTime(100)
    })
    
    rerender(<QueryClientProvider client={queryClient}><NotificationSystem /></QueryClientProvider>)
    
    await waitFor(() => {
      expect(notification).toHaveClass('opacity-100')
    })
    
    jest.useRealTimers()
  })

  it('handles keyboard navigation for accessibility', () => {
    mockNotifications.push({
      id: '1',
      type: 'warning',
      title: 'Keyboard Test',
      message: 'Press Escape to dismiss',
      actions: [
        { label: 'Action', action: jest.fn(), style: 'primary' }
      ]
    })

    renderWithProvider(<NotificationSystem />)
    
    const actionButton = screen.getByRole('button', { name: /action/i })
    
    // Should be focusable
    actionButton.focus()
    expect(actionButton).toHaveFocus()
    
    // Should handle Enter key
    fireEvent.keyDown(actionButton, { key: 'Enter' })
    
    // Should handle Space key
    fireEvent.keyDown(actionButton, { key: ' ' })
  })
})