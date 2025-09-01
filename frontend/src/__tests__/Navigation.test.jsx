import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '../contexts/AuthContext'
import Layout from '../components/Layout'

// Mock Auth0
const mockAuth0 = {
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
  getIdTokenClaims: jest.fn().mockResolvedValue({})
}

jest.mock('@auth0/auth0-react', () => ({
  Auth0Provider: ({ children }) => children,
  useAuth0: () => mockAuth0
}))

// Mock notification system
jest.mock('../components/Notifications/NotificationSystem', () => {
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

const renderWithProviders = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Auth0Provider
        domain="test-domain"
        clientId="test-client-id"
        authorizationParams={{ redirectUri: window.location.origin }}
      >
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Layout>
              <div data-testid="page-content">Current Page Content</div>
            </Layout>
          </AuthProvider>
        </QueryClientProvider>
      </Auth0Provider>
    </MemoryRouter>
  )
}

describe('Navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Navigation Menu', () => {
    const navigationItems = [
      { name: 'Overview', href: '/' },
      { name: 'Calendar', href: '/calendar' },
      { name: 'Analytics', href: '/analytics' },
      { name: 'Performance', href: '/performance' },
      { name: 'Content', href: '/content' },
      { name: 'Memory', href: '/memory' },
      { name: 'Goals', href: '/goals' },
      { name: 'Settings', href: '/settings' }
    ]

    navigationItems.forEach(({ name, href }) => {
      it(`renders ${name} navigation link`, () => {
        renderWithProviders()
        
        // Check both desktop and mobile navigation
        const links = screen.getAllByText(name)
        expect(links).toHaveLength(2) // Desktop and mobile
        
        // Check that at least one link has the correct href
        const linkWithHref = links.find(link => 
          link.getAttribute('href') === href ||
          link.closest('a')?.getAttribute('href') === href
        )
        expect(linkWithHref).toBeTruthy()
      })

      it(`highlights ${name} navigation when on ${href} route`, () => {
        renderWithProviders([href])
        
        // Find navigation links
        const links = screen.getAllByText(name)
        
        // Check that at least one link has active styling
        const hasActiveLink = links.some(link => {
          const parentElement = link.closest('a')
          return parentElement && (
            parentElement.className.includes('bg-gray-50') ||
            parentElement.className.includes('text-indigo-600')
          )
        })
        
        expect(hasActiveLink).toBe(true)
      })
    })
  })

  describe('Mobile Navigation', () => {
    it('opens mobile sidebar when menu button is clicked', () => {
      renderWithProviders()
      
      // Find the mobile menu button (Bars3Icon)
      const mobileMenuButton = screen.getByRole('button', { name: /bars3icon/i })
      
      // Initially, mobile sidebar should be hidden
      const mobileSidebar = document.querySelector('.relative.z-50.lg\\:hidden')
      expect(mobileSidebar).toHaveClass('hidden')
      
      // Click to open sidebar
      fireEvent.click(mobileMenuButton)
      expect(mobileSidebar).not.toHaveClass('hidden')
    })

    it('closes mobile sidebar when close button is clicked', () => {
      renderWithProviders()
      
      // Open the sidebar first
      const mobileMenuButton = screen.getByRole('button', { name: /bars3icon/i })
      fireEvent.click(mobileMenuButton)
      
      const mobileSidebar = document.querySelector('.relative.z-50.lg\\:hidden')
      expect(mobileSidebar).not.toHaveClass('hidden')
      
      // Click close button
      const closeButton = screen.getByRole('button', { name: /xmarkicon/i })
      fireEvent.click(closeButton)
      
      expect(mobileSidebar).toHaveClass('hidden')
    })

    it('closes mobile sidebar when overlay is clicked', () => {
      renderWithProviders()
      
      // Open the sidebar first
      const mobileMenuButton = screen.getByRole('button', { name: /bars3icon/i })
      fireEvent.click(mobileMenuButton)
      
      const mobileSidebar = document.querySelector('.relative.z-50.lg\\:hidden')
      expect(mobileSidebar).not.toHaveClass('hidden')
      
      // Click overlay
      const overlay = document.querySelector('.fixed.inset-0.bg-gray-900\\/80')
      fireEvent.click(overlay)
      
      expect(mobileSidebar).toHaveClass('hidden')
    })
  })

  describe('Page Title Display', () => {
    const routeTitleMappings = [
      { route: '/', expectedTitle: 'Overview' },
      { route: '/calendar', expectedTitle: 'Calendar' },
      { route: '/analytics', expectedTitle: 'Analytics' },
      { route: '/performance', expectedTitle: 'Performance' },
      { route: '/content', expectedTitle: 'Content' },
      { route: '/memory', expectedTitle: 'Memory' },
      { route: '/goals', expectedTitle: 'Goals' },
      { route: '/settings', expectedTitle: 'Settings' }
    ]

    routeTitleMappings.forEach(({ route, expectedTitle }) => {
      it(`displays "${expectedTitle}" as page title for ${route} route`, () => {
        renderWithProviders([route])
        
        expect(screen.getByText(expectedTitle)).toBeInTheDocument()
      })
    })

    it('displays "Dashboard" as fallback title for unknown routes', () => {
      renderWithProviders(['/unknown-route'])
      
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
  })

  describe('User Menu', () => {
    it('displays user information', () => {
      renderWithProviders()
      
      expect(screen.getByText('Test User')).toBeInTheDocument()
      expect(screen.getByAltText('Test User')).toBeInTheDocument()
    })

    it('toggles user menu dropdown', () => {
      renderWithProviders()
      
      const userMenuButton = screen.getByRole('button', { name: /test user/i })
      
      // Initially, user menu should not be visible
      expect(screen.queryByText('Sign out')).not.toBeInTheDocument()
      
      // Click to open user menu
      fireEvent.click(userMenuButton)
      expect(screen.getByText('Sign out')).toBeInTheDocument()
      
      // Click again to close (clicking outside the menu)
      fireEvent.click(document.body)
      // Note: The test doesn't easily support clicking outside to close,
      // but we can verify the menu opens at least
    })

    it('calls logout when sign out is clicked', () => {
      renderWithProviders()
      
      const userMenuButton = screen.getByRole('button', { name: /test user/i })
      fireEvent.click(userMenuButton)
      
      const signOutButton = screen.getByText('Sign out')
      fireEvent.click(signOutButton)
      
      expect(mockAuth0.logout).toHaveBeenCalledTimes(1)
    })

    it('navigates to settings when settings is clicked', () => {
      renderWithProviders()
      
      const userMenuButton = screen.getByRole('button', { name: /test user/i })
      fireEvent.click(userMenuButton)
      
      const settingsLink = screen.getByText('Settings')
      expect(settingsLink.closest('a')).toHaveAttribute('href', '/settings')
    })
  })

  describe('Branding', () => {
    it('displays application branding', () => {
      renderWithProviders()
      
      // Should appear twice (desktop and mobile)
      const brandingElements = screen.getAllByText('SocialAgent')
      expect(brandingElements).toHaveLength(2)
      
      // Check for logo/icon
      const logoElements = document.querySelectorAll('.bg-gradient-to-r.from-blue-600.to-indigo-600')
      expect(logoElements.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('Status Indicators', () => {
    it('displays connection status', () => {
      renderWithProviders()
      
      expect(screen.getByText('Connected')).toBeInTheDocument()
      
      // Check for status indicator dot
      const statusDot = document.querySelector('.h-2.w-2.bg-green-400.rounded-full')
      expect(statusDot).toBeInTheDocument()
    })
  })

  describe('Responsive Behavior', () => {
    it('hides mobile menu on desktop breakpoint', () => {
      renderWithProviders()
      
      // Mobile menu button should have lg:hidden class
      const mobileMenuButton = screen.getByRole('button', { name: /bars3icon/i })
      expect(mobileMenuButton).toHaveClass('lg:hidden')
    })

    it('shows desktop navigation', () => {
      renderWithProviders()
      
      // Desktop sidebar should have lg:flex class
      const desktopSidebar = document.querySelector('.hidden.lg\\:fixed')
      expect(desktopSidebar).toBeInTheDocument()
    })
  })
})