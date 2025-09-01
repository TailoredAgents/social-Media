import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    user: { name: 'Test User', email: 'test@example.com' },
    isAuthenticated: true,
    isLoading: false,
    loginWithRedirect: jest.fn(),
    logout: jest.fn(),
    getAccessTokenSilently: jest.fn().mockResolvedValue('token'),
    getIdTokenClaims: jest.fn().mockResolvedValue({ roles: ['user'], permissions: ['read'] })
  })
}))

// Mock API service
jest.mock('../../services/api.js', () => ({
  __esModule: true,
  default: {
    setToken: jest.fn(),
    createContent: jest.fn().mockResolvedValue({ id: 1 }),
    createGoal: jest.fn().mockResolvedValue({ id: 1 })
  }
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  error: jest.fn()
}))

// Mock react-router-dom hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/' })
}))

import CreatePostModal from '../../components/Calendar/CreatePostModal'
import CreateGoalModal from '../../components/Goals/CreateGoalModal'

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
)

describe('Basic Keyboard Navigation Tests', () => {
  let user

  beforeEach(() => {
    user = userEvent.setup()
    jest.clearAllMocks()
  })

  describe('CreatePostModal Keyboard Navigation', () => {
    it('should allow tab navigation through form fields', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      // Test that form fields are focusable
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)

      await user.click(titleInput)
      expect(titleInput).toHaveFocus()

      await user.tab()
      expect(contentInput).toHaveFocus()
    })

    it('should handle keyboard input in form fields', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)

      await user.type(titleInput, 'Test Title')
      expect(titleInput.value).toBe('Test Title')

      await user.type(contentInput, 'Test Content')
      expect(contentInput.value).toBe('Test Content')
    })

    it('should close modal with Escape key', async () => {
      const mockOnClose = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      // Focus on modal and press Escape
      const titleInput = screen.getByLabelText(/title/i)
      await user.click(titleInput)
      
      await user.keyboard('{Escape}')
      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should submit form with complete data', async () => {
      const mockOnCreatePost = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={mockOnCreatePost}
          />
        </TestWrapper>
      )

      // Fill required fields
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)

      await user.type(titleInput, 'Test Title')
      await user.type(contentInput, 'Test Content')

      // Submit form using button click
      const submitButton = screen.getByRole('button', { name: /create post/i })
      await user.click(submitButton)

      expect(mockOnCreatePost).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Title',
          content: 'Test Content'
        })
      )
    })
  })

  describe('CreateGoalModal Keyboard Navigation', () => {
    it('should handle radio button keyboard navigation', async () => {
      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      // Test radio button navigation
      const radioButtons = screen.getAllByRole('radio')
      expect(radioButtons.length).toBeGreaterThan(0)

      // First radio should be selected by default
      expect(radioButtons[0]).toBeChecked()

      // Focus on radio group
      await user.click(radioButtons[1])
      expect(radioButtons[1]).toBeChecked()
      expect(radioButtons[1]).toHaveFocus()
    })

    it('should handle form field input', async () => {
      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const titleInput = screen.getByLabelText(/title/i)
      const descriptionInput = screen.getByLabelText(/description/i)

      await user.type(titleInput, 'Test Goal')
      expect(titleInput.value).toBe('Test Goal')

      await user.type(descriptionInput, 'Test Description')
      expect(descriptionInput.value).toBe('Test Description')
    })

    it('should handle select dropdown navigation', async () => {
      render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const platformSelect = screen.getByLabelText(/platform/i)
      
      // Test that select is focusable and can be changed
      await user.selectOptions(platformSelect, 'twitter')
      expect(platformSelect.value).toBe('twitter')
    })

    it('should handle date input', async () => {
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
      
      // Test date input
      await user.type(dateInput, '2024-12-31')
      expect(dateInput.value).toBe('2024-12-31')
    })
  })

  describe('Focus Management', () => {
    it('should maintain focus within modal', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      // Focus should stay within modal bounds
      const titleInput = screen.getByLabelText(/title/i)
      await user.click(titleInput)
      expect(titleInput).toHaveFocus()

      // Tabbing should move to next element within modal
      await user.tab()
      const focusedElement = document.activeElement
      expect(focusedElement).toBeInTheDocument()
      expect(focusedElement.tagName).toMatch(/INPUT|TEXTAREA|SELECT|BUTTON/)
    })

    it('should show focus indicators', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      const titleInput = screen.getByLabelText(/title/i)
      
      // Tab to element (keyboard navigation)
      await user.tab()
      if (document.activeElement === titleInput) {
        expect(titleInput).toHaveFocus()
        // Check that focus styles are applied
        expect(titleInput.className).toContain('focus:ring')
      }
    })
  })

  describe('Error Handling with Keyboard', () => {
    it('should handle form validation errors accessibly', async () => {
      const mockOnCreatePost = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={mockOnCreatePost}
          />
        </TestWrapper>
      )

      // Try to submit empty form
      const submitButton = screen.getByRole('button', { name: /create post/i })
      await user.click(submitButton)

      // Should show validation errors
      const titleError = screen.getByText(/title is required/i)
      const contentError = screen.getByText(/content is required/i)
      
      expect(titleError).toBeInTheDocument()
      expect(contentError).toBeInTheDocument()

      // Form should not have been submitted
      expect(mockOnCreatePost).not.toHaveBeenCalled()
    })

    it('should allow fixing validation errors with keyboard', async () => {
      const mockOnCreatePost = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={mockOnCreatePost}
          />
        </TestWrapper>
      )

      // Submit empty form to trigger validation
      const submitButton = screen.getByRole('button', { name: /create post/i })
      await user.click(submitButton)

      // Fix errors using keyboard
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)

      await user.type(titleInput, 'Fixed Title')
      await user.type(contentInput, 'Fixed Content')

      // Submit again
      await user.click(submitButton)

      expect(mockOnCreatePost).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Fixed Title',
          content: 'Fixed Content'
        })
      )
    })
  })

  describe('Keyboard Shortcuts', () => {
    it('should handle common keyboard shortcuts', async () => {
      const mockOnClose = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      // Test Escape key to close
      await user.keyboard('{Escape}')
      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should not interfere with text input shortcuts', async () => {
      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onCreatePost={jest.fn()}
          />
        </TestWrapper>
      )

      const contentInput = screen.getByLabelText(/content/i)
      await user.click(contentInput)

      // Test that Ctrl+A selects all text
      await user.type(contentInput, 'Some test content')
      await user.keyboard('{Control>}a{/Control}')
      await user.type(contentInput, 'Replaced')
      
      expect(contentInput.value).toBe('Replaced')
    })
  })
})