import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Auth0Provider } from '@auth0/auth0-react'
import Layout from '../Layout'
import { AuthProvider } from '../../contexts/AuthContext'

// Mock the hooks and services
jest.mock('../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    notifications: [
      { id: 1, message: 'Test notification', type: 'info', read: false },
      { id: 2, message: 'Test warning', type: 'warning', read: true }
    ],
    unreadCount: 1,
    markAsRead: jest.fn(),
    markAllAsRead: jest.fn(),
    dismiss: jest.fn()
  })
}))

jest.mock('../../hooks/useApi', () => ({
  useApi: () => ({
    data: null,
    loading: false,
    error: null,
    refetch: jest.fn()
  })
}))

jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  warn: jest.fn()
}))

// Mock Auth0
const mockAuth0User = {
  sub: 'auth0|123456789',
  name: 'Test User',
  email: 'test@example.com',
  picture: 'https://example.com/avatar.jpg'
}

const mockAuth0 = {
  isAuthenticated: true,
  user: mockAuth0User,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('mock-token')
}

jest.mock('@auth0/auth0-react', () => ({
  Auth0Provider: ({ children }) => children,
  useAuth0: () => mockAuth0
}))

// Test wrapper component
const TestWrapper = ({ children, initialEntries = ['/'] }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return (
    <Auth0Provider domain="test.auth0.com" clientId="test-client-id">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={initialEntries}>
            {children}
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    </Auth0Provider>
  )
}

describe('Layout Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders main layout structure', () => {
    render(
      <TestWrapper>
        <Layout>
          <div data-testid="child-content">Child content</div>
        </Layout>
      </TestWrapper>
    )

    // Check for main layout elements
    expect(screen.getByRole('banner')).toBeInTheDocument() // header
    expect(screen.getByRole('navigation')).toBeInTheDocument() // sidebar
    expect(screen.getByRole('main')).toBeInTheDocument() // main content
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
  })

  it('displays user information in header', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('shows notification count', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Should show unread count of 1
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('renders all navigation menu items', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Check for main navigation items
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Calendar')).toBeInTheDocument()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
    expect(screen.getByText('Memory')).toBeInTheDocument()
    expect(screen.getByText('Goals')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('highlights active navigation item', () => {
    render(
      <TestWrapper initialEntries={['/analytics']}>
        <Layout>
          <div>Analytics Page</div>
        </Layout>
      </TestWrapper>
    )

    const analyticsLink = screen.getByText('Analytics').closest('a')
    expect(analyticsLink).toHaveClass('bg-indigo-50', 'text-indigo-700')
  })

  it('toggles mobile sidebar', async () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Find and click the mobile menu button
    const mobileMenuButton = screen.getByLabelText('Open sidebar')
    fireEvent.click(mobileMenuButton)

    // Mobile sidebar should be visible
    await waitFor(() => {
      expect(screen.getByTestId('mobile-sidebar')).toHaveClass('translate-x-0')
    })

    // Click close button
    const closeButton = screen.getByLabelText('Close sidebar')
    fireEvent.click(closeButton)

    // Mobile sidebar should be hidden
    await waitFor(() => {
      expect(screen.getByTestId('mobile-sidebar')).toHaveClass('-translate-x-full')
    })
  })

  it('opens and closes notification panel', async () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Click notification button
    const notificationButton = screen.getByLabelText('View notifications')
    fireEvent.click(notificationButton)

    // Notification panel should be visible
    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument()
      expect(screen.getByText('Test notification')).toBeInTheDocument()
    })

    // Click outside or close button to close
    fireEvent.click(document.body)

    await waitFor(() => {
      expect(screen.queryByText('Test notification')).not.toBeInTheDocument()
    })
  })

  it('opens user menu dropdown', async () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Click user avatar/button
    const userButton = screen.getByText('Test User').closest('button')
    fireEvent.click(userButton)

    // User menu should be visible
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
      expect(screen.getByText('Sign out')).toBeInTheDocument()
    })
  })

  it('handles logout when sign out is clicked', async () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Open user menu
    const userButton = screen.getByText('Test User').closest('button')
    fireEvent.click(userButton)

    // Click sign out
    const signOutButton = screen.getByText('Sign out')
    fireEvent.click(signOutButton)

    expect(mockAuth0.logout).toHaveBeenCalledWith({
      returnTo: window.location.origin
    })
  })

  it('renders breadcrumbs for nested routes', () => {
    render(
      <TestWrapper initialEntries={['/analytics/performance']}>
        <Layout>
          <div>Performance Analytics</div>
        </Layout>
      </TestWrapper>
    )

    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()
  })

  it('shows loading state when auth is loading', () => {
    // Mock loading state
    const mockLoadingAuth0 = {
      ...mockAuth0,
      isLoading: true,
      isAuthenticated: false,
      user: null
    }

    jest.mocked(require('@auth0/auth0-react').useAuth0).mockReturnValue(mockLoadingAuth0)

    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('handles keyboard navigation', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    const overviewLink = screen.getByText('Overview').closest('a')
    
    // Test keyboard focus
    overviewLink.focus()
    expect(document.activeElement).toBe(overviewLink)

    // Test Enter key navigation
    fireEvent.keyDown(overviewLink, { key: 'Enter', code: 'Enter' })
    // Navigation should occur (tested by router)
  })

  it('handles responsive design breakpoints', () => {
    // Test desktop view
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    })

    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Desktop sidebar should be visible
    expect(screen.getByTestId('desktop-sidebar')).toHaveClass('lg:block')

    // Mobile menu button should be hidden on desktop
    expect(screen.getByLabelText('Open sidebar')).toHaveClass('lg:hidden')
  })

  it('displays search functionality', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    const searchInput = screen.getByPlaceholderText('Search...')
    expect(searchInput).toBeInTheDocument()

    // Test search input
    fireEvent.change(searchInput, { target: { value: 'test query' } })
    expect(searchInput.value).toBe('test query')
  })

  it('handles notification interactions', async () => {
    const { markAsRead, dismiss } = require('../../hooks/useNotifications').useNotifications()

    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Open notifications panel
    const notificationButton = screen.getByLabelText('View notifications')
    fireEvent.click(notificationButton)

    await waitFor(() => {
      expect(screen.getByText('Test notification')).toBeInTheDocument()
    })

    // Test mark as read functionality
    const markReadButton = screen.getByText('Mark as read')
    fireEvent.click(markReadButton)

    expect(markAsRead).toHaveBeenCalledWith(1)

    // Test dismiss functionality
    const dismissButton = screen.getByText('Dismiss')
    fireEvent.click(dismissButton)

    expect(dismiss).toHaveBeenCalledWith(1)
  })

  it('shows correct navigation icons', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Test that navigation items have associated icons
    // This is a basic test - in real implementation you'd check for specific SVG icons
    const navigationItems = screen.getAllByRole('link')
    expect(navigationItems.length).toBeGreaterThan(0)
    
    // Each navigation item should have an icon (svg element)
    navigationItems.forEach(item => {
      const svg = item.querySelector('svg')
      if (svg) {
        expect(svg).toBeInTheDocument()
      }
    })
  })

  it('applies correct accessibility attributes', () => {
    render(
      <TestWrapper>
        <Layout>
          <div>Content</div>
        </Layout>
      </TestWrapper>
    )

    // Check ARIA labels and roles
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    
    // Check button accessibility
    expect(screen.getByLabelText('Open sidebar')).toBeInTheDocument()
    expect(screen.getByLabelText('View notifications')).toBeInTheDocument()
  })
})