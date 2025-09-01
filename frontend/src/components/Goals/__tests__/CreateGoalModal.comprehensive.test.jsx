import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CreateGoalModal from '../CreateGoalModal'

describe('CreateGoalModal Component', () => {
  const mockProps = {
    isOpen: true,
    onClose: jest.fn(),
    onSubmit: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Modal Visibility', () => {
    it('renders when isOpen is true', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      expect(screen.getByText('Create New Goal')).toBeInTheDocument()
      expect(screen.getByText('Set up a new goal to track your social media progress')).toBeInTheDocument()
    })

    it('does not render when isOpen is false', () => {
      render(<CreateGoalModal {...mockProps} isOpen={false} />)
      
      expect(screen.queryByText('Create New Goal')).not.toBeInTheDocument()
    })

    it('calls onClose when close button is clicked', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const closeButton = screen.getByRole('button', { name: /close/i })
      fireEvent.click(closeButton)
      
      expect(mockProps.onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when overlay is clicked', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const overlay = screen.getByTestId('modal-overlay')
      fireEvent.click(overlay)
      
      expect(mockProps.onClose).toHaveBeenCalledTimes(1)
    })

    it('does not close when modal content is clicked', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const modalContent = screen.getByRole('dialog')
      fireEvent.click(modalContent)
      
      expect(mockProps.onClose).not.toHaveBeenCalled()
    })
  })

  describe('Goal Type Selection', () => {
    it('displays all goal type options', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      expect(screen.getByText('Follower Growth')).toBeInTheDocument()
      expect(screen.getByText('Engagement Rate')).toBeInTheDocument()
      expect(screen.getByText('Content Volume')).toBeInTheDocument()
      expect(screen.getByText('Reach Increase')).toBeInTheDocument()
    })

    it('shows goal type descriptions', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      expect(screen.getByText('Increase your follower count on social platforms')).toBeInTheDocument()
      expect(screen.getByText('Improve interaction rates on your content')).toBeInTheDocument()
      expect(screen.getByText('Increase the number of posts published')).toBeInTheDocument()
      expect(screen.getByText('Expand your content reach and impressions')).toBeInTheDocument()
    })

    it('allows selecting a goal type', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const followerGrowthOption = screen.getByLabelText('Follower Growth')
      fireEvent.click(followerGrowthOption)
      
      expect(followerGrowthOption).toBeChecked()
    })

    it('updates form when goal type changes', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const engagementOption = screen.getByLabelText('Engagement Rate')
      fireEvent.click(engagementOption)
      
      // Should show percentage unit for engagement rate
      expect(screen.getByText('%')).toBeInTheDocument()
    })
  })

  describe('Form Fields', () => {
    it('renders all required form fields', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      expect(screen.getByLabelText('Goal Title')).toBeInTheDocument()
      expect(screen.getByLabelText('Description')).toBeInTheDocument()
      expect(screen.getByLabelText('Current Value')).toBeInTheDocument()
      expect(screen.getByLabelText('Target Value')).toBeInTheDocument()
      expect(screen.getByLabelText('Target Date')).toBeInTheDocument()
      expect(screen.getByLabelText('Platform')).toBeInTheDocument()
    })

    it('accepts text input for goal title', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const titleInput = screen.getByLabelText('Goal Title')
      fireEvent.change(titleInput, { target: { value: 'Grow Instagram Following' } })
      
      expect(titleInput.value).toBe('Grow Instagram Following')
    })

    it('accepts text input for description', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const descriptionInput = screen.getByLabelText('Description')
      fireEvent.change(descriptionInput, { target: { value: 'Increase Instagram followers by 1000' } })
      
      expect(descriptionInput.value).toBe('Increase Instagram followers by 1000')
    })

    it('accepts numeric input for current value', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const currentValueInput = screen.getByLabelText('Current Value')
      fireEvent.change(currentValueInput, { target: { value: '1500' } })
      
      expect(currentValueInput.value).toBe('1500')
    })

    it('accepts numeric input for target value', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const targetValueInput = screen.getByLabelText('Target Value')
      fireEvent.change(targetValueInput, { target: { value: '2500' } })
      
      expect(targetValueInput.value).toBe('2500')
    })

    it('accepts date input for target date', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const targetDateInput = screen.getByLabelText('Target Date')
      fireEvent.change(targetDateInput, { target: { value: '2025-12-31' } })
      
      expect(targetDateInput.value).toBe('2025-12-31')
    })

    it('provides platform selection options', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const platformSelect = screen.getByLabelText('Platform')
      
      expect(platformSelect).toBeInTheDocument()
      expect(screen.getByText('All Platforms')).toBeInTheDocument()
      expect(screen.getByText('Twitter')).toBeInTheDocument()
      expect(screen.getByText('LinkedIn')).toBeInTheDocument()
      expect(screen.getByText('Instagram')).toBeInTheDocument()
      expect(screen.getByText('Facebook')).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('shows validation errors for empty required fields', async () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Goal title is required')).toBeInTheDocument()
        expect(screen.getByText('Please select a goal type')).toBeInTheDocument()
      })
    })

    it('validates that target value is greater than current value', async () => {
      render(<CreateGoalModal {...mockProps} />)
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText('Goal Title'), { target: { value: 'Test Goal' } })
      fireEvent.click(screen.getByLabelText('Follower Growth'))
      fireEvent.change(screen.getByLabelText('Current Value'), { target: { value: '1000' } })
      fireEvent.change(screen.getByLabelText('Target Value'), { target: { value: '500' } })
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Target value must be greater than current value')).toBeInTheDocument()
      })
    })

    it('validates that target date is in the future', async () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      
      fireEvent.change(screen.getByLabelText('Goal Title'), { target: { value: 'Test Goal' } })
      fireEvent.click(screen.getByLabelText('Follower Growth'))
      fireEvent.change(screen.getByLabelText('Target Date'), { 
        target: { value: yesterday.toISOString().split('T')[0] } 
      })
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Target date must be in the future')).toBeInTheDocument()
      })
    })

    it('prevents submission when form is invalid', async () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      expect(mockProps.onSubmit).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    const fillValidForm = () => {
      fireEvent.change(screen.getByLabelText('Goal Title'), {
        target: { value: 'Grow Twitter Following' }
      })
      fireEvent.change(screen.getByLabelText('Description'), {
        target: { value: 'Increase Twitter followers from 1000 to 2000' }
      })
      fireEvent.click(screen.getByLabelText('Follower Growth'))
      fireEvent.change(screen.getByLabelText('Current Value'), {
        target: { value: '1000' }
      })
      fireEvent.change(screen.getByLabelText('Target Value'), {
        target: { value: '2000' }
      })
      fireEvent.change(screen.getByLabelText('Target Date'), {
        target: { value: '2025-12-31' }
      })
      fireEvent.change(screen.getByLabelText('Platform'), {
        target: { value: 'twitter' }
      })
    }

    it('submits valid form data', async () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fillValidForm()
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(mockProps.onSubmit).toHaveBeenCalledWith({
          title: 'Grow Twitter Following',
          description: 'Increase Twitter followers from 1000 to 2000',
          goal_type: 'follower_growth',
          current_value: 1000,
          target_value: 2000,
          target_date: '2025-12-31',
          platform: 'twitter'
        })
      })
    })

    it('closes modal after successful submission', async () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fillValidForm()
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(mockProps.onClose).toHaveBeenCalledTimes(1)
      })
    })

    it('shows loading state during submission', async () => {
      let resolveSubmit
      const delayedSubmit = new Promise(resolve => {
        resolveSubmit = resolve
      })
      
      const delayedOnSubmit = jest.fn(() => delayedSubmit)
      
      render(<CreateGoalModal {...mockProps} onSubmit={delayedOnSubmit} />)
      
      fillValidForm()
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      expect(screen.getByText('Creating...')).toBeInTheDocument()
      expect(submitButton).toBeDisabled()
      
      resolveSubmit()
      
      await waitFor(() => {
        expect(screen.queryByText('Creating...')).not.toBeInTheDocument()
      })
    })
  })

  describe('Cancel Functionality', () => {
    it('calls onClose when cancel button is clicked', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      fireEvent.click(cancelButton)
      
      expect(mockProps.onClose).toHaveBeenCalledTimes(1)
    })

    it('resets form when canceled', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      // Fill some fields
      fireEvent.change(screen.getByLabelText('Goal Title'), {
        target: { value: 'Test Goal' }
      })
      fireEvent.click(screen.getByLabelText('Follower Growth'))
      
      // Cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      fireEvent.click(cancelButton)
      
      // Reopen modal
      render(<CreateGoalModal {...mockProps} />)
      
      // Fields should be empty
      expect(screen.getByLabelText('Goal Title').value).toBe('')
    })
  })

  describe('Progress Calculation', () => {
    it('shows estimated progress when values are entered', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fireEvent.change(screen.getByLabelText('Current Value'), {
        target: { value: '1000' }
      })
      fireEvent.change(screen.getByLabelText('Target Value'), {
        target: { value: '2000' }
      })
      
      expect(screen.getByText('Current Progress: 50%')).toBeInTheDocument()
    })

    it('handles zero current value correctly', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fireEvent.change(screen.getByLabelText('Current Value'), {
        target: { value: '0' }
      })
      fireEvent.change(screen.getByLabelText('Target Value'), {
        target: { value: '1000' }
      })
      
      expect(screen.getByText('Current Progress: 0%')).toBeInTheDocument()
    })
  })

  describe('Goal Type Units', () => {
    it('displays correct unit for follower growth', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fireEvent.click(screen.getByLabelText('Follower Growth'))
      
      expect(screen.getByText('followers')).toBeInTheDocument()
    })

    it('displays correct unit for engagement rate', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fireEvent.click(screen.getByLabelText('Engagement Rate'))
      
      expect(screen.getByText('%')).toBeInTheDocument()
    })

    it('displays correct unit for content volume', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fireEvent.click(screen.getByLabelText('Content Volume'))
      
      expect(screen.getByText('posts')).toBeInTheDocument()
    })

    it('displays correct unit for reach increase', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      fireEvent.click(screen.getByLabelText('Reach Increase'))
      
      expect(screen.getByText('impressions')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByLabelText('Goal Title')).toBeInTheDocument()
      expect(screen.getByLabelText('Description')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create goal/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('supports keyboard navigation', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const titleInput = screen.getByLabelText('Goal Title')
      
      titleInput.focus()
      expect(document.activeElement).toBe(titleInput)
      
      // Tab to next field
      fireEvent.keyDown(titleInput, { key: 'Tab' })
      expect(document.activeElement).toBe(screen.getByLabelText('Description'))
    })

    it('handles Escape key to close modal', () => {
      render(<CreateGoalModal {...mockProps} />)
      
      const modal = screen.getByRole('dialog')
      fireEvent.keyDown(modal, { key: 'Escape' })
      
      expect(mockProps.onClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Error Handling', () => {
    it('handles submission errors gracefully', async () => {
      const errorOnSubmit = jest.fn(() => {
        throw new Error('Submission failed')
      })
      
      render(<CreateGoalModal {...mockProps} onSubmit={errorOnSubmit} />)
      
      // Fill valid form
      fireEvent.change(screen.getByLabelText('Goal Title'), {
        target: { value: 'Test Goal' }
      })
      fireEvent.click(screen.getByLabelText('Follower Growth'))
      fireEvent.change(screen.getByLabelText('Current Value'), {
        target: { value: '1000' }
      })
      fireEvent.change(screen.getByLabelText('Target Value'), {
        target: { value: '2000' }
      })
      
      const submitButton = screen.getByRole('button', { name: /create goal/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Failed to create goal. Please try again.')).toBeInTheDocument()
      })
    })
  })
})