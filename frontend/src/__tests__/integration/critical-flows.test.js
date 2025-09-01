import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { AuthProvider } from '../../contexts/AuthContext'
import Content from '../../pages/Content'
import CreatePostModal from '../../components/Calendar/CreatePostModal'
import NotificationContainer from '../../components/Notifications/NotificationContainer'

// Mock Auth0
jest.mock('@auth0/auth0-react')

// Mock API service
jest.mock('../../services/api.js', () => ({
  __esModule: true,
  default: {
    setToken: jest.fn(),
    getContent: jest.fn(),
    createContent: jest.fn(),
    getGoals: jest.fn(),
    createGoal: jest.fn(),
    getAnalytics: jest.fn(),
    getNotifications: jest.fn(),
    markNotificationRead: jest.fn(),
    searchMemory: jest.fn(),
    storeMemory: jest.fn(),
    getAllMemory: jest.fn(),
    getMemoryAnalytics: jest.fn(),
    updateContent: jest.fn(),
    deleteContent: jest.fn(),
  }
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
}))

// Mock Chart.js to avoid canvas issues
jest.mock('react-chartjs-2', () => ({
  Bar: ({ data }) => <div data-testid="bar-chart">{JSON.stringify(data)}</div>,
  Line: ({ data }) => <div data-testid="line-chart">{JSON.stringify(data)}</div>,
  Doughnut: ({ data }) => <div data-testid="doughnut-chart">{JSON.stringify(data)}</div>
}))

// Mock react-router-dom hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/' })
}))

import apiService from '../../services/api.js'

const mockAuthenticatedUser = {
  user: {
    name: 'Test User',
    email: 'test@example.com',
    picture: 'https://example.com/avatar.jpg'
  },
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('mock-token'),
  getIdTokenClaims: jest.fn().mockResolvedValue({
    roles: ['user'],
    permissions: ['read', 'write']
  })
}

const TestWrapper = ({ children }) => {
  useAuth0.mockReturnValue(mockAuthenticatedUser)
  
  return (
    <BrowserRouter>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Critical User Flows Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    apiService.getContent.mockResolvedValue([
      { 
        id: 1, 
        title: 'Test Post 1', 
        content: 'Content 1', 
        platform: 'LinkedIn',
        status: 'draft',
        created_at: '2023-12-01T00:00:00Z'
      },
      { 
        id: 2, 
        title: 'Test Post 2', 
        content: 'Content 2', 
        platform: 'Twitter',
        status: 'published',
        created_at: '2023-12-02T00:00:00Z'
      }
    ])
    
    apiService.getAllMemory.mockResolvedValue([
      {
        id: 1,
        content: 'Stored memory content',
        metadata: { type: 'post', platform: 'LinkedIn' },
        created_at: '2023-12-01T00:00:00Z'
      }
    ])
    
    apiService.getMemoryAnalytics.mockResolvedValue({
      total_memories: 10,
      avg_similarity: 0.85,
      top_tags: ['linkedin', 'content', 'marketing']
    })
  })

  describe('Content Management Flow', () => {
    it('should load and display content list successfully', async () => {
      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Wait for content to load
      await waitFor(() => {
        expect(apiService.getContent).toHaveBeenCalled()
      })

      // Verify content is displayed
      await waitFor(() => {
        expect(screen.getByText('Test Post 1')).toBeInTheDocument()
        expect(screen.getByText('Test Post 2')).toBeInTheDocument()
      })

      // Verify platform badges are shown
      expect(screen.getByText('LinkedIn')).toBeInTheDocument()
      expect(screen.getByText('Twitter')).toBeInTheDocument()
    })

    it('should handle content search functionality', async () => {
      apiService.searchMemory.mockResolvedValue([
        { 
          id: 1, 
          content: 'Search result content',
          similarity: 0.95,
          metadata: { type: 'post' }
        }
      ])

      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Test Post 1')).toBeInTheDocument()
      })

      // Find and use search
      const searchInput = screen.getByPlaceholderText(/search/i)
      fireEvent.change(searchInput, { target: { value: 'test query' } })
      
      // Submit search
      const searchButton = screen.getByRole('button', { name: /search/i })
      fireEvent.click(searchButton)

      await waitFor(() => {
        expect(apiService.searchMemory).toHaveBeenCalledWith('test query', 10)
      })
    })

    it('should filter content by platform', async () => {
      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Test Post 1')).toBeInTheDocument()
      })

      // Find platform filter
      const platformFilter = screen.getByDisplayValue('all')
      fireEvent.change(platformFilter, { target: { value: 'LinkedIn' } })

      // Content should be filtered (this tests the UI filtering logic)
      await waitFor(() => {
        // LinkedIn post should still be visible
        expect(screen.getByText('Test Post 1')).toBeInTheDocument()
      })
    })

    it('should handle content creation workflow', async () => {
      apiService.createContent.mockResolvedValue({
        id: 3,
        title: 'New Test Post',
        content: 'New test content',
        platform: 'LinkedIn',
        status: 'draft'
      })

      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Test Post 1')).toBeInTheDocument()
      })

      // Open create modal
      const createButton = screen.getByRole('button', { name: /create new post/i })
      fireEvent.click(createButton)

      // Wait for modal to open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Fill form
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)
      const platformSelect = screen.getByLabelText(/platform/i)

      fireEvent.change(titleInput, { target: { value: 'New Test Post' } })
      fireEvent.change(contentInput, { target: { value: 'New test content' } })
      fireEvent.change(platformSelect, { target: { value: 'LinkedIn' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: /save|create/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(apiService.createContent).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'New Test Post',
            content: 'New test content',
            platform: 'LinkedIn'
          })
        )
      })
    })
  })

  describe('Content Post Modal Integration', () => {
    it('should validate form before submission', async () => {
      const mockOnSave = jest.fn()
      const mockOnClose = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onSave={mockOnSave}
          />
        </TestWrapper>
      )

      // Try to submit empty form
      const submitButton = screen.getByRole('button', { name: /save|create/i })
      fireEvent.click(submitButton)

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/title is required/i)).toBeInTheDocument()
        expect(screen.getByText(/content is required/i)).toBeInTheDocument()
      })

      // onSave should not be called with invalid data
      expect(mockOnSave).not.toHaveBeenCalled()
    })

    it('should submit valid form data', async () => {
      const mockOnSave = jest.fn()
      const mockOnClose = jest.fn()

      render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={mockOnClose}
            onSave={mockOnSave}
          />
        </TestWrapper>
      )

      // Fill valid form data
      const titleInput = screen.getByLabelText(/title/i)
      const contentInput = screen.getByLabelText(/content/i)
      const platformSelect = screen.getByLabelText(/platform/i)

      fireEvent.change(titleInput, { target: { value: 'Valid Title' } })
      fireEvent.change(contentInput, { target: { value: 'Valid content text' } })
      fireEvent.change(platformSelect, { target: { value: 'LinkedIn' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: /save|create/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Valid Title',
            content: 'Valid content text',
            platform: 'LinkedIn'
          })
        )
      })
    })
  })

  describe('Notification System Integration', () => {
    it('should display and manage notifications', async () => {
      const mockNotifications = [
        {
          id: 1,
          type: 'success',
          message: 'Content saved successfully',
          timestamp: Date.now()
        },
        {
          id: 2,
          type: 'info',
          message: 'New analytics available',
          timestamp: Date.now() - 5000
        }
      ]

      render(
        <TestWrapper>
          <NotificationContainer />
        </TestWrapper>
      )

      // Simulate notifications being added
      mockNotifications.forEach(notification => {
        window.dispatchEvent(new CustomEvent('notification', {
          detail: notification
        }))
      })

      await waitFor(() => {
        expect(screen.getByText('Content saved successfully')).toBeInTheDocument()
        expect(screen.getByText('New analytics available')).toBeInTheDocument()
      })

      // Test dismissing notification
      const dismissButtons = screen.getAllByRole('button', { name: /dismiss|close/i })
      fireEvent.click(dismissButtons[0])

      await waitFor(() => {
        expect(screen.queryByText('Content saved successfully')).not.toBeInTheDocument()
      })
    })

    it('should auto-dismiss notifications after timeout', async () => {
      jest.useFakeTimers()

      render(
        <TestWrapper>
          <NotificationContainer />
        </TestWrapper>
      )

      // Add a notification
      window.dispatchEvent(new CustomEvent('notification', {
        detail: {
          id: 1,
          type: 'info',
          message: 'Auto-dismiss test',
          timestamp: Date.now()
        }
      }))

      await waitFor(() => {
        expect(screen.getByText('Auto-dismiss test')).toBeInTheDocument()
      })

      // Fast-forward time
      jest.advanceTimersByTime(6000) // 6 seconds

      await waitFor(() => {
        expect(screen.queryByText('Auto-dismiss test')).not.toBeInTheDocument()
      })

      jest.useRealTimers()
    })
  })

  describe('Error Handling Integration', () => {
    it('should handle API errors gracefully', async () => {
      apiService.getContent.mockRejectedValue(new Error('API Error'))

      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText(/error loading content|failed to load|something went wrong/i)).toBeInTheDocument()
      })
    })

    it('should show loading states', async () => {
      // Make API call take longer
      apiService.getContent.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve([]), 1000))
      )

      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Should show loading indicator
      expect(screen.getByText(/loading|fetching/i)).toBeInTheDocument()
    })

    it('should handle network connectivity issues', async () => {
      apiService.getContent.mockRejectedValue(new Error('Network Error'))

      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/network error|connection failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Authentication Integration', () => {
    it('should set API token when authenticated', async () => {
      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(apiService.setToken).toHaveBeenCalledWith('mock-token')
      })
    })

    it('should handle authentication state changes', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Simulate user logout
      useAuth0.mockReturnValue({
        ...mockAuthenticatedUser,
        isAuthenticated: false,
        user: null
      })

      rerender(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Should handle unauthenticated state
      await waitFor(() => {
        expect(screen.getByText(/please log in|authentication required/i)).toBeInTheDocument()
      })
    })
  })

  describe('Performance Integration', () => {
    it('should handle large content lists efficiently', async () => {
      // Generate large content list
      const largeContentList = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        title: `Post ${i + 1}`,
        content: `Content for post ${i + 1}`,
        platform: i % 2 === 0 ? 'LinkedIn' : 'Twitter',
        status: 'published',
        created_at: `2023-12-${String(i % 30 + 1).padStart(2, '0')}T00:00:00Z`
      }))

      apiService.getContent.mockResolvedValue(largeContentList)

      const startTime = Date.now()
      
      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Post 1')).toBeInTheDocument()
      })

      const renderTime = Date.now() - startTime
      expect(renderTime).toBeLessThan(3000) // Should render within 3 seconds
    })

    it('should handle concurrent API calls', async () => {
      render(
        <TestWrapper>
          <Content />
        </TestWrapper>
      )

      // Multiple API calls should be made concurrently
      await waitFor(() => {
        expect(apiService.getContent).toHaveBeenCalled()
        expect(apiService.getAllMemory).toHaveBeenCalled()
        expect(apiService.getMemoryAnalytics).toHaveBeenCalled()
      })
    })
  })
})