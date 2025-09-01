import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '../Layout'

// Mock the auth context
const mockAuthContext = {
  user: {
    name: 'Test User',
    email: 'test@example.com',
    picture: 'https://example.com/avatar.jpg'
  },
  logout: jest.fn(),
  isAuthenticated: true
}

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

// Mock the notification system
jest.mock('../Notifications/NotificationSystem', () => {
  return function MockNotificationSystem() {
    return <div data-testid="notification-system">Notifications</div>
  }
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    </BrowserRouter>
  )
}

describe('Layout Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the layout with branding', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    expect(screen.getAllByText('SocialAgent')).toHaveLength(2) // Desktop and mobile
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('displays all navigation items', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    const expectedNavItems = [
      'Overview', 'Calendar', 'Analytics', 'Performance', 
      'Content', 'Memory', 'Goals', 'Settings'
    ]
    
    expectedNavItems.forEach(item => {
      expect(screen.getAllByText(item)).toHaveLength(2) // Desktop and mobile
    })
  })

  it('shows user information in header', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByAltText('Test User')).toBeInTheDocument()
  })

  it('opens and closes mobile sidebar', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    // Find the mobile menu button
    const mobileMenuButton = screen.getByRole('button', { name: /bars3icon/i })
    
    // Initially, mobile sidebar should be hidden
    const mobileSidebar = document.querySelector('.relative.z-50.lg\\:hidden')
    expect(mobileSidebar).toHaveClass('hidden')
    
    // Click to open sidebar
    fireEvent.click(mobileMenuButton)
    expect(mobileSidebar).not.toHaveClass('hidden')
    
    // Click to close sidebar
    const closeButton = screen.getByRole('button', { name: /xmarkicon/i })
    fireEvent.click(closeButton)
    expect(mobileSidebar).toHaveClass('hidden')
  })

  it('toggles user menu', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    const userMenuButton = screen.getByRole('button', { name: /test user/i })
    
    // Initially, user menu should not be visible
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    expect(screen.queryByText('Sign out')).not.toBeInTheDocument()
    
    // Click to open user menu
    fireEvent.click(userMenuButton)
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Sign out')).toBeInTheDocument()
  })

  it('calls logout when sign out is clicked', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    const userMenuButton = screen.getByRole('button', { name: /test user/i })
    fireEvent.click(userMenuButton)
    
    const signOutButton = screen.getByText('Sign out')
    fireEvent.click(signOutButton)
    
    expect(mockAuthContext.logout).toHaveBeenCalledTimes(1)
  })

  it('displays connection status', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('renders notification system', () => {
    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    expect(screen.getByTestId('notification-system')).toBeInTheDocument()
  })

  it('displays fallback user initial when no picture', () => {
    const mockAuthWithoutPicture = {
      ...mockAuthContext,
      user: {
        name: 'Test User',
        email: 'test@example.com',
        picture: null
      }
    }

    jest.doMock('../../contexts/AuthContext', () => ({
      useAuth: () => mockAuthWithoutPicture
    }))

    renderWithProviders(<Layout><div>Test Content</div></Layout>)
    
    // Should show the first letter of the name
    expect(screen.getByText('T')).toBeInTheDocument()
  })
})