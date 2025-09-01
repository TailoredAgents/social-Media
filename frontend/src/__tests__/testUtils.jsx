import React from 'react'
import { render } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock environment variables for tests
export const mockEnvVars = {
  VITE_AUTH0_DOMAIN: 'test-domain.auth0.com',
  VITE_AUTH0_CLIENT_ID: 'test-client-id',
  VITE_AUTH0_AUDIENCE: 'test-audience'
}

// Create a fresh QueryClient for each test
export const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
    },
    mutations: {
      retry: false,
    },
  },
})

// Mock Auth0 Provider for tests
const MockAuth0Provider = ({ children }) => children

// Test wrapper with all providers
export const TestWrapper = ({ children, initialEntries = ['/'] }) => {
  const queryClient = createTestQueryClient()
  
  return (
    <MemoryRouter initialEntries={initialEntries}>
      <MockAuth0Provider>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </MockAuth0Provider>
    </MemoryRouter>
  )
}

// Helper function to render with all providers
export const renderWithProviders = (ui, options = {}) => {
  const { initialEntries, ...renderOptions } = options
  
  return render(
    <TestWrapper initialEntries={initialEntries}>
      {ui}
    </TestWrapper>,
    renderOptions
  )
}

// Mock Auth0 user for tests
export const mockAuth0User = {
  name: 'Test User',
  email: 'test@example.com',
  picture: 'https://example.com/avatar.jpg',
  sub: 'auth0|123456789'
}

// Mock Auth0 hook with common defaults
export const createMockAuth0 = (overrides = {}) => ({
  user: mockAuth0User,
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('mock-access-token'),
  getIdTokenClaims: jest.fn().mockResolvedValue({
    roles: ['user'],
    permissions: ['read']
  }),
  ...overrides
})

// Mock the Auth0 provider for tests
export const mockAuth0Provider = (mockImplementation) => {
  const mockAuth0Hook = mockImplementation || createMockAuth0()
  jest.mock('@auth0/auth0-react', () => ({
    Auth0Provider: ({ children }) => children,
    useAuth0: () => mockAuth0Hook
  }))
}

// Cleanup function for tests
export const testCleanup = () => {
  jest.clearAllMocks()
  // Clear any cached queries
  const queryClient = createTestQueryClient()
  queryClient.clear()
}

// Mock window methods commonly needed in tests  
export const mockWindowMethods = () => {
  const mockDispatchEvent = jest.fn()
  Object.defineProperty(window, 'dispatchEvent', {
    value: mockDispatchEvent,
    writable: true
  })
  
  return { mockDispatchEvent }
}

export default {
  TestWrapper,
  renderWithProviders,
  mockAuth0User,
  createMockAuth0,
  mockAuth0Provider,
  testCleanup,
  mockWindowMethods,
  mockEnvVars
}