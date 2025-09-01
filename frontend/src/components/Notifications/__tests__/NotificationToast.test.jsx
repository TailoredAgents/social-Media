import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import NotificationToast from '../NotificationToast'

describe('NotificationToast', () => {
  const mockNotification = {
    id: 1,
    type: 'success',
    title: 'Success!',
    message: 'Operation completed successfully',
    duration: 3000,
    persistent: false
  }

  const mockOnDismiss = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders notification toast', () => {
    render(<NotificationToast notification={mockNotification} onDismiss={mockOnDismiss} />)
    
    expect(screen.getByText('Success!')).toBeInTheDocument()
    expect(screen.getByText('Operation completed successfully')).toBeInTheDocument()
  })

  it('renders success notification with correct icon', () => {
    render(<NotificationToast notification={mockNotification} onDismiss={mockOnDismiss} />)
    
    const successIcon = screen.getByRole('img', { hidden: true })
    expect(successIcon).toBeInTheDocument()
  })

  it('renders error notification', () => {
    const errorNotification = {
      ...mockNotification,
      type: 'error',
      title: 'Error!',
      message: 'Something went wrong'
    }
    
    render(<NotificationToast notification={errorNotification} onDismiss={mockOnDismiss} />)
    
    expect(screen.getByText('Error!')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders warning notification', () => {
    const warningNotification = {
      ...mockNotification,
      type: 'warning',
      title: 'Warning!',
      message: 'Please be careful'
    }
    
    render(<NotificationToast notification={warningNotification} onDismiss={mockOnDismiss} />)
    
    expect(screen.getByText('Warning!')).toBeInTheDocument()
    expect(screen.getByText('Please be careful')).toBeInTheDocument()
  })

  it('renders info notification', () => {
    const infoNotification = {
      ...mockNotification,
      type: 'info',
      title: 'Info',
      message: 'Here is some information'
    }
    
    render(<NotificationToast notification={infoNotification} onDismiss={mockOnDismiss} />)
    
    expect(screen.getByText('Info')).toBeInTheDocument()
    expect(screen.getByText('Here is some information')).toBeInTheDocument()
  })

  it('calls onDismiss when close button clicked', () => {
    render(<NotificationToast notification={mockNotification} onDismiss={mockOnDismiss} />)
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    expect(mockOnDismiss).toHaveBeenCalledWith(mockNotification.id)
  })

  it('auto-dismisses after duration', async () => {
    render(<NotificationToast notification={mockNotification} onDismiss={mockOnDismiss} />)
    
    // Fast-forward time
    jest.advanceTimersByTime(3000)
    
    await waitFor(() => {
      expect(mockOnDismiss).toHaveBeenCalledWith(mockNotification.id)
    })
  })

  it('does not auto-dismiss persistent notifications', () => {
    const persistentNotification = {
      ...mockNotification,
      persistent: true
    }
    
    render(<NotificationToast notification={persistentNotification} onDismiss={mockOnDismiss} />)
    
    jest.advanceTimersByTime(5000)
    
    expect(mockOnDismiss).not.toHaveBeenCalled()
  })

  it('does not auto-dismiss when no duration specified', () => {
    const noDurationNotification = {
      ...mockNotification,
      duration: undefined
    }
    
    render(<NotificationToast notification={noDurationNotification} onDismiss={mockOnDismiss} />)
    
    jest.advanceTimersByTime(5000)
    
    expect(mockOnDismiss).not.toHaveBeenCalled()
  })

  it('renders action button when provided', () => {
    const notificationWithAction = {
      ...mockNotification,
      action: {
        label: 'Undo',
        handler: jest.fn()
      }
    }
    
    render(<NotificationToast notification={notificationWithAction} onDismiss={mockOnDismiss} />)
    
    const actionButton = screen.getByText('Undo')
    expect(actionButton).toBeInTheDocument()
    
    fireEvent.click(actionButton)
    expect(notificationWithAction.action.handler).toHaveBeenCalled()
  })

  it('handles missing title gracefully', () => {
    const notificationWithoutTitle = {
      ...mockNotification,
      title: undefined
    }
    
    render(<NotificationToast notification={notificationWithoutTitle} onDismiss={mockOnDismiss} />)
    
    expect(screen.getByText('Operation completed successfully')).toBeInTheDocument()
  })

  it('handles missing message gracefully', () => {
    const notificationWithoutMessage = {
      ...mockNotification,
      message: undefined
    }
    
    render(<NotificationToast notification={notificationWithoutMessage} onDismiss={mockOnDismiss} />)
    
    expect(screen.getByText('Success!')).toBeInTheDocument()
  })

  it('cleans up timeout on unmount', () => {
    const { unmount } = render(<NotificationToast notification={mockNotification} onDismiss={mockOnDismiss} />)
    
    unmount()
    
    jest.advanceTimersByTime(3000)
    expect(mockOnDismiss).not.toHaveBeenCalled()
  })
})