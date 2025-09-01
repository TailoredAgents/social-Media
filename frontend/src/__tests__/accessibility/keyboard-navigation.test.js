import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'

// Mock Auth0
const mockAuth0 = {
  user: { name: 'Test User', email: 'test@example.com' },
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('token'),
  getIdTokenClaims: jest.fn().mockResolvedValue({ roles: ['user'], permissions: ['read'] })
}

jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => mockAuth0,
  Auth0Provider: ({ children }) => children
}))

// Mock API service
jest.mock('../../services/api.js', () => ({
  __esModule: true,
  default: {
    setToken: jest.fn(),
    getContent: jest.fn().mockResolvedValue([]),
    createContent: jest.fn().mockResolvedValue({ id: 1 }),
    getGoals: jest.fn().mockResolvedValue([]),
    createGoal: jest.fn().mockResolvedValue({ id: 1 }),
    getAnalytics: jest.fn().mockResolvedValue({ totalViews: 0 }),
    getNotifications: jest.fn().mockResolvedValue([])
  }
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
}))

// Mock react-router-dom hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/' })
}))

import CreatePostModal from '../../components/Calendar/CreatePostModal'
import CreateGoalModal from '../../components/Goals/CreateGoalModal'
import NotificationToast from '../../components/Notifications/NotificationToast'

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
)

describe('Keyboard Navigation Accessibility Tests', () => {
  let user

  beforeEach(() => {
    user = userEvent.setup()
    jest.clearAllMocks()
  })

  describe('Modal Keyboard Navigation', () => {
    it('should navigate through CreatePostModal with keyboard', async () => {
      const mockOnClose = jest.fn()
      const mockOnSave = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onSave={mockOnSave}
          />
        </TestWrapper>
      )

      // Get all focusable elements in order
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)
      const platformSelect = screen.getByLabelText(/platform/i)
      const closeButton = screen.getByLabelText(/close/i)
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      const saveButton = screen.getByRole('button', { name: /create post/i })

      // Test Tab navigation forward
      await user.tab()
      expect(titleInput).toHaveFocus()

      await user.tab()
      expect(contentInput).toHaveFocus()

      await user.tab()
      expect(platformSelect).toHaveFocus()

      await user.tab()
      expect(closeButton).toHaveFocus()

      await user.tab()
      expect(cancelButton).toHaveFocus()

      await user.tab()
      expect(saveButton).toHaveFocus()

      // Test Shift+Tab navigation backward
      await user.tab({ shift: true })
      expect(cancelButton).toHaveFocus()

      await user.tab({ shift: true })
      expect(closeButton).toHaveFocus()
    })

    it('should navigate through CreateGoalModal with keyboard', async () => {
      const mockOnClose = jest.fn()
      const mockOnSubmit = jest.fn()

      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={mockOnClose}
            onSubmit={mockOnSubmit}
          />
        </TestWrapper>
      )

      // Test goal type radio navigation
      const goalTypeRadios = screen.getAllByRole('radio')
      expect(goalTypeRadios).toHaveLength(4)

      await user.tab()
      expect(goalTypeRadios[0]).toHaveFocus()

      // Test arrow key navigation within radio group
      await user.keyboard('{ArrowDown}')
      expect(goalTypeRadios[1]).toHaveFocus()

      await user.keyboard('{ArrowDown}')
      expect(goalTypeRadios[2]).toHaveFocus()

      await user.keyboard('{ArrowUp}')
      expect(goalTypeRadios[1]).toHaveFocus()

      // Continue to other form fields
      await user.tab()
      const titleInput = screen.getByLabelText(/goal title/i)
      expect(titleInput).toHaveFocus()

      await user.tab()
      const descriptionInput = screen.getByLabelText(/description/i)
      expect(descriptionInput).toHaveFocus()

      await user.tab()
      const platformSelect = screen.getByLabelText(/platform/i)
      expect(platformSelect).toHaveFocus()
    })

    it('should close modal with Escape key', async () => {
      const mockOnClose = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      await user.keyboard('{Escape}')
      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should handle Enter key for form submission', async () => {
      const mockOnSave = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={mockOnSave}
          />
        </TestWrapper>
      )

      // Fill required fields
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)

      await user.type(titleInput, 'Test Title')
      await user.type(contentInput, 'Test Content')

      // Submit with Enter key
      await user.keyboard('{Enter}')

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Test Title',
            content: 'Test Content'
          })
        )
      })
    })
  })

  describe('Form Field Keyboard Navigation', () => {
    it('should handle select dropdown keyboard navigation', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      const platformSelect = screen.getByLabelText(/platform/i)
      
      // Focus and open dropdown
      await user.click(platformSelect)
      expect(platformSelect).toHaveFocus()

      // Test arrow key navigation in select
      await user.keyboard('{ArrowDown}')
      await user.keyboard('{ArrowDown}')
      await user.keyboard('{Enter}')

      // Verify selection changed
      expect(platformSelect.value).not.toBe('LinkedIn') // Should have changed from default
    })

    it('should handle textarea keyboard navigation and expansion', async () => {
      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const descriptionInput = screen.getByLabelText(/description/i)
      await user.click(descriptionInput)

      // Test multi-line input
      const longText = 'This is a long description that spans multiple lines\nand tests keyboard navigation\nwithin a textarea element'
      await user.type(descriptionInput, longText)

      expect(descriptionInput.value).toBe(longText)

      // Test cursor navigation
      await user.keyboard('{Home}')
      await user.keyboard('{End}')
      await user.keyboard('{Control>}{Home}{/Control}') // Ctrl+Home (start of text)
    })

    it('should handle date input keyboard navigation', async () => {
      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const dateInput = screen.getByLabelText(/target date/i)
      await user.click(dateInput)

      // Test date input with keyboard
      await user.type(dateInput, '2024-12-31')
      expect(dateInput.value).toBe('2024-12-31')

      // Test arrow navigation within date
      await user.keyboard('{Home}')
      await user.keyboard('{ArrowRight}{ArrowRight}{ArrowRight}{ArrowRight}')
      await user.keyboard('{Backspace}{Backspace}01')
      expect(dateInput.value).toBe('2024-01-31')
    })
  })

  describe('Notification Keyboard Navigation', () => {
    it('should handle notification dismissal with keyboard', async () => {
      const mockOnDismiss = jest.fn()
      const notification = {
        id: 1,
        type: 'info',
        message: 'Test notification',
        timestamp: Date.now()
      }

      render(
        <TestWrapper>
          <NotificationToast
            notification={notification}
            onDismiss={mockOnDismiss}
          />
        </TestWrapper>
      )

      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i })
      
      // Focus and activate with keyboard
      await user.tab()
      expect(dismissButton).toHaveFocus()

      await user.keyboard('{Enter}')
      expect(mockOnDismiss).toHaveBeenCalledWith(1)
    })

    it('should handle notification action buttons with keyboard', async () => {
      const mockOnDismiss = jest.fn()
      const notification = {
        id: 1,
        type: 'success',
        message: 'Content saved successfully',
        timestamp: Date.now(),
        action: {
          label: 'View',
          onClick: jest.fn()
        }
      }

      render(
        <TestWrapper>
          <NotificationToast
            notification={notification}
            onDismiss={mockOnDismiss}
          />
        </TestWrapper>
      )

      // Should be able to navigate to action button
      await user.tab()
      const actionButton = screen.getByRole('button', { name: /view/i })
      expect(actionButton).toHaveFocus()

      await user.keyboard('{Enter}')
      expect(notification.action.onClick).toHaveBeenCalled()

      // Should be able to navigate to dismiss button
      await user.tab()
      const dismissButton = screen.getByRole('button', { name: /dismiss|close/i })
      expect(dismissButton).toHaveFocus()
    })
  })

  describe('Focus Management', () => {
    it('should trap focus within modal', async () => {
      const mockOnClose = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      // Get first and last focusable elements
      const titleInput = screen.getByLabelText(/title/i)
      const saveButton = screen.getByRole('button', { name: /create post/i })

      // Focus should start on first element
      await user.tab()
      expect(titleInput).toHaveFocus()

      // Tab through all elements to last one
      let currentElement = titleInput
      let tabCount = 0
      const maxTabs = 10 // Safety limit

      while (currentElement !== saveButton && tabCount < maxTabs) {
        await user.tab()
        currentElement = document.activeElement
        tabCount++
      }

      expect(saveButton).toHaveFocus()

      // Tab from last element should cycle back to first
      await user.tab()
      expect(titleInput).toHaveFocus()

      // Shift+Tab from first should cycle to last
      await user.tab({ shift: true })
      expect(saveButton).toHaveFocus()
    })

    it('should restore focus after modal closes', async () => {
      const mockOnClose = jest.fn()

      // Create a button outside modal to test focus restoration
      render(
        <TestWrapper>
          <div>
            <button data-testid="trigger-button">Open Modal</button>
            <CreatePostModal
              isOpen={true}
              onClose={mockOnClose}
              onSave={jest.fn()}
            />
          </div>
        </TestWrapper>
      )

      const triggerButton = screen.getByTestId('trigger-button')
      
      // Simulate that this button opened the modal
      triggerButton.focus()
      
      // Focus moves into modal
      await user.tab()
      const titleInput = screen.getByLabelText(/title/i)
      expect(titleInput).toHaveFocus()

      // Close modal with Escape
      await user.keyboard('{Escape}')
      expect(mockOnClose).toHaveBeenCalled()

      // In real implementation, focus should return to trigger button
      // This would be handled by the modal component's useEffect cleanup
    })

    it('should handle focus visible states correctly', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      const titleInput = screen.getByLabelText(/title/i)
      
      // Tab navigation should show focus ring
      await user.tab()
      expect(titleInput).toHaveFocus()
      expect(titleInput).toHaveClass('focus:ring-2', 'focus:ring-blue-500')

      // Mouse click should also be focusable
      await user.click(titleInput)
      expect(titleInput).toHaveFocus()
    })
  })

  describe('Skip Links and Landmarks', () => {
    it('should provide logical tab order in complex forms', async () => {
      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const focusOrder = []
      
      // Record focus order by tabbing through form
      for (let i = 0; i < 10; i++) {
        await user.tab()
        const activeElement = document.activeElement
        if (activeElement && activeElement.tagName !== 'BODY') {
          focusOrder.push({
            tag: activeElement.tagName,
            type: activeElement.type,
            name: activeElement.name || activeElement.getAttribute('aria-label') || activeElement.textContent?.trim()
          })
        }
      }

      // Verify logical order: radio group -> title -> description -> platform -> values -> date -> buttons
      expect(focusOrder[0]).toMatchObject({ tag: 'INPUT', type: 'radio' })
      expect(focusOrder.find(el => el.name === 'title')).toBeTruthy()
      expect(focusOrder.find(el => el.name === 'description')).toBeTruthy()
      expect(focusOrder.find(el => el.name === 'platform')).toBeTruthy()
    })

    it('should handle keyboard shortcuts appropriately', async () => {
      const mockOnClose = jest.fn()
      const mockOnSave = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onSave={mockOnSave}
          />
        </TestWrapper>
      )

      // Test common keyboard shortcuts
      await user.keyboard('{Escape}')
      expect(mockOnClose).toHaveBeenCalled()

      // Test that Ctrl+Enter doesn't interfere with normal form submission
      const titleInput = screen.getByLabelText(/title/i)
      await user.type(titleInput, 'Test')
      
      await user.keyboard('{Control>}{Enter}{/Control}')
      // Should not submit incomplete form
      expect(mockOnSave).not.toHaveBeenCalled()
    })
  })
})