import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '../Layout'

// Mock navigation hooks
const mockLocation = { pathname: '/' }
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => mockLocation
}))

// Mock auth context
const mockAuthContext = {
  isAuthenticated: true,
  user: {
    name: 'Test User',
    email: 'test@example.com',
    picture: 'https://example.com/avatar.jpg'
  },
  logout: jest.fn()
}

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

// Mock NotificationSystem component
jest.mock('../Notifications/NotificationSystem', () => {
  return function MockNotificationSystem() {
    return <div data-testid="notification-system">Notifications</div>
  }
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
})

const renderWithProviders = (component) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Layout Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLocation.pathname = '/'
  })

  it('renders main layout structure', () => {
    renderWithProviders(
      <Layout>
        <div>Main Content</div>
      </Layout>
    )
    
    expect(screen.getByText('AI')).toBeInTheDocument()
    expect(screen.getByText('SocialAgent')).toBeInTheDocument()
    expect(screen.getByText('Main Content')).toBeInTheDocument()
    expect(screen.getByTestId('notification-system')).toBeInTheDocument()
  })

  it('renders all navigation items', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    const expectedNavItems = [
      'Overview', 'Calendar', 'Analytics', 'Performance', 
      'Content', 'Memory', 'Goals', 'Settings'
    ]
    
    expectedNavItems.forEach(item => {
      expect(screen.getAllByText(item)).toHaveLength(2) // Desktop and mobile
    })
  })

  it('highlights active navigation item', () => {
    mockLocation.pathname = '/calendar'
    
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    const calendarLinks = screen.getAllByRole('link', { name: /calendar/i })
    calendarLinks.forEach(link => {
      expect(link).toHaveAttribute('aria-current', 'page')
    })
  })

  it('opens mobile sidebar when menu button is clicked', async () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    const menuButton = screen.getByRole('button', { name: /open main menu/i })
    fireEvent.click(menuButton)
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /close navigation menu/i })).toBeInTheDocument()
    })
  })

  it('closes mobile sidebar when close button is clicked', async () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    // Open sidebar first
    const menuButton = screen.getByRole('button', { name: /open main menu/i })
    fireEvent.click(menuButton)
    
    await waitFor(() => {
      const closeButton = screen.getByRole('button', { name: /close navigation menu/i })
      fireEvent.click(closeButton)
    })
    
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /close navigation menu/i })).not.toBeInTheDocument()
    })
  })

  it('closes mobile sidebar when backdrop is clicked', async () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    // Open sidebar first
    const menuButton = screen.getByRole('button', { name: /open main menu/i })
    fireEvent.click(menuButton)
    
    await waitFor(() => {
      const backdrop = document.querySelector('.bg-gray-900\\/80')
      fireEvent.click(backdrop)
    })
    
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /close navigation menu/i })).not.toBeInTheDocument()
    })
  })

  it('displays user information in header', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByAltText('User avatar')).toHaveAttribute('src', 'https://example.com/avatar.jpg')
  })

  it('opens user menu when user avatar is clicked', async () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    fireEvent.click(userButton)
    
    await waitFor(() => {
      expect(screen.getByText('Your Profile')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
      expect(screen.getByText('Sign out')).toBeInTheDocument()
    })
  })

  it('calls logout when sign out is clicked', async () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    fireEvent.click(userButton)
    
    await waitFor(() => {
      const signOutButton = screen.getByText('Sign out')
      fireEvent.click(signOutButton)
    })
    
    expect(mockAuthContext.logout).toHaveBeenCalled()
  })

  it('applies correct accessibility attributes', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('handles keyboard navigation for user menu', async () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    userButton.focus()
    fireEvent.keyDown(userButton, { key: 'Enter' })
    
    await waitFor(() => {
      expect(screen.getByText('Your Profile')).toBeInTheDocument()
    })
  })

  it('renders children in main content area', () => {
    const testContent = <div data-testid="test-content">Test Children</div>
    
    renderWithProviders(
      <Layout>
        {testContent}
      </Layout>
    )
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument()
    expect(screen.getByRole('main')).toContainElement(screen.getByTestId('test-content'))
  })

  it('handles unauthenticated state gracefully', () => {
    mockAuthContext.isAuthenticated = false
    mockAuthContext.user = null
    
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )
    
    // Should still render layout structure
    expect(screen.getByText('AI')).toBeInTheDocument()
    expect(screen.getByText('SocialAgent')).toBeInTheDocument()
  })

  describe('Responsive Design', () => {
    it('shows mobile menu button on small screens', () => {
      renderWithProviders(
        <Layout>
          <div>Content</div>
        </Layout>
      )
      
      const mobileMenuButton = screen.getByRole('button', { name: /open main menu/i })
      expect(mobileMenuButton).toBeInTheDocument()
      expect(mobileMenuButton).toHaveClass('lg:hidden')
    })

    it('hides mobile sidebar by default', () => {
      renderWithProviders(
        <Layout>
          <div>Content</div>
        </Layout>
      )
      
      const mobileSidebar = document.querySelector('.lg\\:hidden')
      expect(mobileSidebar).toHaveClass('hidden')
    })
  })

  describe('Navigation Links', () => {
    const navigationItems = [
      { name: 'Overview', path: '/' },
      { name: 'Calendar', path: '/calendar' },
      { name: 'Analytics', path: '/analytics' },
      { name: 'Performance', path: '/performance' },
      { name: 'Content', path: '/content' },
      { name: 'Memory', path: '/memory' },
      { name: 'Goals', path: '/goals' },
      { name: 'Settings', path: '/settings' }
    ]

    navigationItems.forEach(({ name, path }) => {
      it(`renders ${name} navigation link with correct href`, () => {
        renderWithProviders(
          <Layout>
            <div>Content</div>
          </Layout>
        )
        
        const links = screen.getAllByRole('link', { name: new RegExp(name, 'i') })
        links.forEach(link => {
          expect(link).toHaveAttribute('href', path)
        })
      })
    })
  })
})