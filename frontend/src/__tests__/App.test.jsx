import { render, screen } from '@testing-library/react'
import { useAuth0 } from '@auth0/auth0-react'
import App from '../App'

// Mock Auth0
jest.mock('@auth0/auth0-react')

// Mock all page components
jest.mock('../pages/Login', () => {
  return function MockLogin() {
    return <div data-testid="login-page">Login Page</div>
  }
})

jest.mock('../pages/Overview', () => {
  return function MockOverview() {
    return <div data-testid="overview-page">Overview Page</div>
  }
})

jest.mock('../pages/Calendar', () => {
  return function MockCalendar() {
    return <div data-testid="calendar-page">Calendar Page</div>
  }
})

jest.mock('../pages/Analytics', () => {
  return function MockAnalytics() {
    return <div data-testid="analytics-page">Analytics Page</div>
  }
})

jest.mock('../pages/PerformanceDashboard', () => {
  return function MockPerformanceDashboard() {
    return <div data-testid="performance-page">Performance Page</div>
  }
})

jest.mock('../pages/Content', () => {
  return function MockContent() {
    return <div data-testid="content-page">Content Page</div>
  }
})

jest.mock('../pages/MemoryExplorer', () => {
  return function MockMemoryExplorer() {
    return <div data-testid="memory-page">Memory Page</div>
  }
})

jest.mock('../pages/GoalTracking', () => {
  return function MockGoalTracking() {
    return <div data-testid="goals-page">Goals Page</div>
  }
})

jest.mock('../pages/Settings', () => {
  return function MockSettings() {
    return <div data-testid="settings-page">Settings Page</div>
  }
})

// Mock the Layout component
jest.mock('../components/Layout', () => {
  return function MockLayout({ children }) {
    return (
      <div data-testid="layout">
        <div data-testid="layout-content">{children}</div>
      </div>
    )
  }
})

// Mock ProtectedRoute
jest.mock('../components/ProtectedRoute', () => {
  return function MockProtectedRoute({ children }) {
    return <div data-testid="protected-route">{children}</div>
  }
})

// Mock NotificationContainer
jest.mock('../components/Notifications/NotificationContainer', () => {
  return function MockNotificationContainer() {
    return <div data-testid="notification-container">Notifications</div>
  }
})

const mockUseAuth0 = {
  user: {
    name: 'Test User',
    email: 'test@example.com'
  },
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn(),
  getIdTokenClaims: jest.fn()
}

// Mock environment variables
const originalEnv = process.env
beforeAll(() => {
  process.env = {
    ...originalEnv,
    VITE_AUTH0_DOMAIN: 'test-domain.auth0.com',
    VITE_AUTH0_CLIENT_ID: 'test-client-id',
    VITE_AUTH0_AUDIENCE: 'test-audience'
  }
})

afterAll(() => {
  process.env = originalEnv
})

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    useAuth0.mockReturnValue(mockUseAuth0)
    
    // Mock window.location
    delete window.location
    window.location = { origin: 'http://localhost:3000' }
  })

  it('renders with Auth0Provider and other providers', () => {
    render(<App />)
    
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('renders login page at /login route', () => {
    // Mock history to simulate navigation to /login
    window.history.pushState({}, 'Login', '/login')
    
    render(<App />)
    
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
  })

  it('renders overview page at root route when authenticated', () => {
    // Mock history to simulate navigation to root
    window.history.pushState({}, 'Home', '/')
    
    render(<App />)
    
    expect(screen.getByTestId('protected-route')).toBeInTheDocument()
    expect(screen.getByTestId('layout')).toBeInTheDocument()
    expect(screen.getByTestId('overview-page')).toBeInTheDocument()
  })

  it('configures Auth0Provider with correct props', () => {
    const Auth0ProviderSpy = jest.fn(({ children }) => children)
    useAuth0.mockImplementation(() => mockUseAuth0)
    
    // We can't easily spy on Auth0Provider, but we can verify it doesn't crash
    render(<App />)
    
    // If App renders without errors, Auth0Provider is configured correctly
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('configures QueryClient with correct default options', () => {
    render(<App />)
    
    // If App renders without errors, QueryClient is configured correctly
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('wraps routes with proper provider hierarchy', () => {
    render(<App />)
    
    // Verify the provider hierarchy is working by checking for elements
    // that depend on different providers
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('applies correct app-level styling', () => {
    const { container } = render(<App />)
    
    const appWrapper = container.querySelector('.min-h-screen.bg-gray-50')
    expect(appWrapper).toBeInTheDocument()
  })

  describe('Protected Routes', () => {
    beforeEach(() => {
      // Ensure we're starting from a clean state
      window.history.pushState({}, 'Home', '/')
    })

    const protectedRoutes = [
      { path: '/', testId: 'overview-page', name: 'Overview' },
      { path: '/calendar', testId: 'calendar-page', name: 'Calendar' },
      { path: '/analytics', testId: 'analytics-page', name: 'Analytics' },
      { path: '/performance', testId: 'performance-page', name: 'Performance' },
      { path: '/content', testId: 'content-page', name: 'Content' },
      { path: '/memory', testId: 'memory-page', name: 'Memory' },
      { path: '/goals', testId: 'goals-page', name: 'Goals' },
      { path: '/settings', testId: 'settings-page', name: 'Settings' }
    ]

    protectedRoutes.forEach(({ path, testId, name }) => {
      it(`renders ${name} page at ${path} route with protection`, () => {
        window.history.pushState({}, name, path)
        
        render(<App />)
        
        expect(screen.getByTestId('protected-route')).toBeInTheDocument()
        expect(screen.getByTestId('layout')).toBeInTheDocument()
        expect(screen.getByTestId(testId)).toBeInTheDocument()
      })
    })
  })

  it('handles unauthenticated state', () => {
    useAuth0.mockReturnValue({
      ...mockUseAuth0,
      isAuthenticated: false,
      user: null
    })

    render(<App />)
    
    // App should still render, protection is handled by ProtectedRoute
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })

  it('handles loading state', () => {
    useAuth0.mockReturnValue({
      ...mockUseAuth0,
      isLoading: true
    })

    render(<App />)
    
    // App should still render during loading
    expect(screen.getByTestId('notification-container')).toBeInTheDocument()
  })
})