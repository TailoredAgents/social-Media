import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'

// Mock environment variables before importing App
Object.defineProperty(global, 'import', {
  value: {
    meta: {
      env: {
        VITE_AUTH0_DOMAIN: 'test-domain.auth0.com',
        VITE_AUTH0_CLIENT_ID: 'test-client-id',
        VITE_AUTH0_AUDIENCE: 'test-audience',
        VITE_API_BASE_URL: 'http://localhost:8000'
      }
    }
  }
})

import App from '../../App'
import { AuthProvider } from '../../contexts/AuthContext'

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
    getHealth: jest.fn(),
  }
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
}))

// Mock Chart.js to avoid canvas issues in tests
jest.mock('react-chartjs-2', () => ({
  Bar: ({ data }) => <div data-testid="bar-chart">{JSON.stringify(data)}</div>,
  Line: ({ data }) => <div data-testid="line-chart">{JSON.stringify(data)}</div>,
  Doughnut: ({ data }) => <div data-testid="doughnut-chart">{JSON.stringify(data)}</div>
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

const mockUnauthenticatedUser = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn(),
  getIdTokenClaims: jest.fn()
}

const TestWrapper = ({ children, authenticated = true }) => {
  useAuth0.mockReturnValue(authenticated ? mockAuthenticatedUser : mockUnauthenticatedUser)
  
  return (
    <BrowserRouter>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Critical User Journey Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    apiService.getHealth.mockResolvedValue({ status: 'healthy' })
    apiService.getContent.mockResolvedValue([
      { id: 1, title: 'Test Post 1', content: 'Content 1', platform: 'LinkedIn' },
      { id: 2, title: 'Test Post 2', content: 'Content 2', platform: 'Twitter' }
    ])
    apiService.getGoals.mockResolvedValue([
      { id: 1, title: 'Increase followers', target: 1000, current: 750 }
    ])
    apiService.getAnalytics.mockResolvedValue({
      totalViews: 1000,
      totalEngagement: 150,
      topPerformingPosts: []
    })
    apiService.getNotifications.mockResolvedValue([
      { id: 1, type: 'info', message: 'Welcome!', read: false }
    ])
  })

  describe('Authentication Journey', () => {
    it('should redirect unauthenticated users to login', async () => {
      render(
        <TestWrapper authenticated={false}>
          <App />
        </TestWrapper>
      )

      // Should show login prompt or redirect
      expect(mockUnauthenticatedUser.loginWithRedirect).toHaveBeenCalled()
    })

    it('should load dashboard for authenticated users', async () => {
      render(
        <TestWrapper authenticated={true}>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(apiService.setToken).toHaveBeenCalledWith('mock-token')
      })

      // Should show user name or dashboard elements
      await waitFor(() => {
        expect(screen.getByText(/Test User|Dashboard|Welcome/i)).toBeInTheDocument()
      })
    })

    it('should handle logout flow', async () => {
      render(
        <TestWrapper authenticated={true}>
          <App />
        </TestWrapper>
      )

      // Find and click logout button
      const logoutButton = await waitFor(() => 
        screen.getByRole('button', { name: /logout|sign out/i })
      )
      
      fireEvent.click(logoutButton)

      expect(mockAuthenticatedUser.logout).toHaveBeenCalledWith({
        logoutParams: {
          returnTo: window.location.origin
        }
      })
    })
  })

  describe('Content Management Journey', () => {
    it('should complete content creation workflow', async () => {
      apiService.createContent.mockResolvedValue({
        id: 3,
        title: 'New Post',
        content: 'New content',
        platform: 'LinkedIn'
      })

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Navigate to content creation
      const createButton = await waitFor(() => 
        screen.getByRole('button', { name: /create|new post|add content/i })
      )
      fireEvent.click(createButton)

      // Fill out content form
      const titleInput = await waitFor(() => 
        screen.getByLabelText(/title/i)
      )
      const contentInput = await waitFor(() => 
        screen.getByLabelText(/content|description/i)
      )

      fireEvent.change(titleInput, { target: { value: 'New Post' } })
      fireEvent.change(contentInput, { target: { value: 'New content' } })

      // Submit form
      const submitButton = screen.getByRole('button', { name: /save|create|submit/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(apiService.createContent).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'New Post',
            content: 'New content'
          })
        )
      })
    })

    it('should display and interact with content list', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Wait for content to load
      await waitFor(() => {
        expect(apiService.getContent).toHaveBeenCalled()
      })

      // Should show content items
      await waitFor(() => {
        expect(screen.getByText('Test Post 1')).toBeInTheDocument()
        expect(screen.getByText('Test Post 2')).toBeInTheDocument()
      })
    })
  })

  describe('Goals Management Journey', () => {
    it('should create and track goals', async () => {
      apiService.createGoal.mockResolvedValue({
        id: 2,
        title: 'New Goal',
        target: 500,
        current: 0
      })

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Navigate to goals section
      const goalsLink = await waitFor(() => 
        screen.getByText(/goals/i)
      )
      fireEvent.click(goalsLink)

      // Create new goal
      const createGoalButton = await waitFor(() => 
        screen.getByRole('button', { name: /create goal|new goal|add goal/i })
      )
      fireEvent.click(createGoalButton)

      // Fill goal form
      const goalTitleInput = await waitFor(() => 
        screen.getByLabelText(/title|name/i)
      )
      const targetInput = await waitFor(() => 
        screen.getByLabelText(/target|goal/i)
      )

      fireEvent.change(goalTitleInput, { target: { value: 'New Goal' } })
      fireEvent.change(targetInput, { target: { value: '500' } })

      // Submit goal
      const submitGoalButton = screen.getByRole('button', { name: /save|create|submit/i })
      fireEvent.click(submitGoalButton)

      await waitFor(() => {
        expect(apiService.createGoal).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'New Goal',
            target: 500
          })
        )
      })
    })

    it('should display goals progress', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(apiService.getGoals).toHaveBeenCalled()
      })

      // Should show goal information
      await waitFor(() => {
        expect(screen.getByText('Increase followers')).toBeInTheDocument()
      })
    })
  })

  describe('Analytics Dashboard Journey', () => {
    it('should load and display analytics data', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Navigate to analytics
      const analyticsLink = await waitFor(() => 
        screen.getByText(/analytics|metrics|dashboard/i)
      )
      fireEvent.click(analyticsLink)

      await waitFor(() => {
        expect(apiService.getAnalytics).toHaveBeenCalled()
      })

      // Should show analytics metrics
      await waitFor(() => {
        expect(screen.getByText(/1000|150/)).toBeInTheDocument()
      })
    })

    it('should render charts and visualizations', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Wait for charts to render
      await waitFor(() => {
        const charts = screen.getAllByTestId(/chart/i)
        expect(charts.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Notifications Journey', () => {
    it('should display and manage notifications', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(apiService.getNotifications).toHaveBeenCalled()
      })

      // Should show notification
      await waitFor(() => {
        expect(screen.getByText('Welcome!')).toBeInTheDocument()
      })

      // Mark notification as read
      const notificationElement = screen.getByText('Welcome!')
      fireEvent.click(notificationElement)

      await waitFor(() => {
        expect(apiService.markNotificationRead).toHaveBeenCalledWith(1)
      })
    })
  })

  describe('Search and Memory Journey', () => {
    it('should perform content search', async () => {
      apiService.searchMemory.mockResolvedValue([
        { id: 1, title: 'Search Result 1', similarity: 0.9 }
      ])

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Find search input
      const searchInput = await waitFor(() => 
        screen.getByPlaceholderText(/search/i)
      )

      fireEvent.change(searchInput, { target: { value: 'test query' } })
      fireEvent.submit(searchInput.closest('form'))

      await waitFor(() => {
        expect(apiService.searchMemory).toHaveBeenCalledWith('test query')
      })
    })
  })

  describe('Error Handling Journey', () => {
    it('should handle API errors gracefully', async () => {
      apiService.getContent.mockRejectedValue(new Error('API Error'))

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Should show error message or fallback UI
      await waitFor(() => {
        expect(screen.getByText(/error|failed|try again/i)).toBeInTheDocument()
      })
    })

    it('should handle network connectivity issues', async () => {
      apiService.getHealth.mockRejectedValue(new Error('Network Error'))

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Should show connectivity warning
      await waitFor(() => {
        expect(screen.getByText(/offline|connection|network/i)).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Design Journey', () => {
    it('should adapt to mobile viewport', async () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 })
      Object.defineProperty(window, 'innerHeight', { writable: true, configurable: true, value: 667 })
      window.dispatchEvent(new Event('resize'))

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Should show mobile-friendly layout
      await waitFor(() => {
        const mobileElements = screen.getAllByTestId(/mobile|drawer|hamburger/i)
        expect(mobileElements.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Performance Journey', () => {
    it('should load initial content within reasonable time', async () => {
      const startTime = Date.now()

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/Dashboard|Welcome|Test User/i)).toBeInTheDocument()
      })

      const loadTime = Date.now() - startTime
      expect(loadTime).toBeLessThan(5000) // Should load within 5 seconds
    })

    it('should handle concurrent API calls', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      // Multiple API calls should execute in parallel
      await waitFor(() => {
        expect(apiService.getContent).toHaveBeenCalled()
        expect(apiService.getGoals).toHaveBeenCalled()
        expect(apiService.getNotifications).toHaveBeenCalled()
      })
    })
  })
})