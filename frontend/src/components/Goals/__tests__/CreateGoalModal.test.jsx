import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CreateGoalModal from '../CreateGoalModal'

describe('CreateGoalModal', () => {
  const mockProps = {
    isOpen: true,
    onClose: jest.fn(),
    onSubmit: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders modal when open', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    expect(screen.getByText('Create New Goal')).toBeInTheDocument()
    expect(screen.getByLabelText('Goal Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<CreateGoalModal {...mockProps} isOpen={false} />)
    
    expect(screen.queryByText('Create New Goal')).not.toBeInTheDocument()
  })

  it('displays all goal types', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    expect(screen.getByText('Follower Growth')).toBeInTheDocument()
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument()
    expect(screen.getByText('Content Volume')).toBeInTheDocument()
    expect(screen.getByText('Reach Increase')).toBeInTheDocument()
  })

  it('displays platform options', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    expect(screen.getByLabelText('Platform')).toBeInTheDocument()
    
    // Check some platform options exist
    const platformSelect = screen.getByLabelText('Platform')
    expect(platformSelect).toBeInTheDocument()
  })

  it('calls onClose when close button clicked', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    expect(mockProps.onClose).toHaveBeenCalled()
  })

  it('creates goal with valid data', async () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Fill out form
    fireEvent.change(screen.getByLabelText('Goal Title'), {
      target: { value: 'Increase LinkedIn followers' }
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Grow LinkedIn presence by engaging more' }
    })
    fireEvent.change(screen.getByLabelText('Target Value'), {
      target: { value: '1000' }
    })
    fireEvent.change(screen.getByLabelText('Current Value'), {
      target: { value: '500' }
    })
    
    // Submit form
    const createButton = screen.getByRole('button', { name: /create goal/i })
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Increase LinkedIn followers',
          description: 'Grow LinkedIn presence by engaging more',
          target_value: '1000',
          current_value: '500'
        })
      )
    })
  })

  it('shows validation errors for empty required fields', async () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Try to submit empty form
    const createButton = screen.getByRole('button', { name: /create goal/i })
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument()
      expect(screen.getByText('Target value is required')).toBeInTheDocument()
    })
    
    expect(mockProps.onSubmit).not.toHaveBeenCalled()
  })

  it('validates target value is greater than current value', async () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Fill form with invalid values (target < current)
    fireEvent.change(screen.getByLabelText('Goal Title'), {
      target: { value: 'Test Goal' }
    })
    fireEvent.change(screen.getByLabelText('Target Value'), {
      target: { value: '100' }
    })
    fireEvent.change(screen.getByLabelText('Current Value'), {
      target: { value: '200' }
    })
    
    const createButton = screen.getByRole('button', { name: /create goal/i })
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(screen.getByText('Target value must be greater than current value')).toBeInTheDocument()
    })
    
    expect(mockProps.onSubmit).not.toHaveBeenCalled()
  })

  it('allows selecting different goal types', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Click on engagement rate goal type
    const engagementOption = screen.getByText('Engagement Rate')
    fireEvent.click(engagementOption)
    
    // The engagement rate option should be selected
    expect(engagementOption.closest('div')).toHaveClass('border-blue-500')
  })

  it('shows correct unit for selected goal type', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Default goal type is follower_growth with unit 'followers'
    expect(screen.getByText('followers')).toBeInTheDocument()
    
    // Select engagement rate goal type
    const engagementOption = screen.getByText('Engagement Rate')
    fireEvent.click(engagementOption)
    
    // Should show percentage unit
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('allows setting deadline date', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    const deadlineInput = screen.getByLabelText('Deadline')
    fireEvent.change(deadlineInput, { target: { value: '2024-12-31' } })
    
    expect(deadlineInput.value).toBe('2024-12-31')
  })

  it('allows selecting platform', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    const platformSelect = screen.getByLabelText('Platform')
    fireEvent.change(platformSelect, { target: { value: 'linkedin' } })
    
    expect(platformSelect.value).toBe('linkedin')
  })

  it('resets form after successful submission', async () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Fill and submit form
    const titleInput = screen.getByLabelText('Goal Title')
    fireEvent.change(titleInput, { target: { value: 'Test Goal' } })
    fireEvent.change(screen.getByLabelText('Target Value'), { target: { value: '1000' } })
    
    const createButton = screen.getByRole('button', { name: /create goal/i })
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalled()
      expect(mockProps.onClose).toHaveBeenCalled()
    })
  })

  it('handles cancellation', () => {
    render(<CreateGoalModal {...mockProps} />)
    
    // Fill form partially
    fireEvent.change(screen.getByLabelText('Goal Title'), {
      target: { value: 'Test Goal' }
    })
    
    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    fireEvent.click(cancelButton)
    
    expect(mockProps.onClose).toHaveBeenCalled()
    expect(mockProps.onSubmit).not.toHaveBeenCalled()
  })
})