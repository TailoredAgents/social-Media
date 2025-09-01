import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../AuthContext'

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: jest.fn()
}))

jest.mock('../../utils/logger.js', () => ({
  error: jest.fn()
}))

import { useAuth0 } from '@auth0/auth0-react'
import { error as logError } from '../../utils/logger.js'

// Test component to access auth context
const TestAuthComponent = () => {
  const auth = useAuth()
  return (
    <div>
      <div data-testid="loading">{auth.isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{auth.isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="access-token">{auth.accessToken || 'no-token'}</div>
      <div data-testid="user-email">{auth.userProfile?.email || 'no-email'}</div>
      <div data-testid="user-name">{auth.userProfile?.name || 'no-name'}</div>
      <button onClick={() => auth.login()}>Login</button>
      <button onClick={() => auth.logout()}>Logout</button>
      <button onClick={() => auth.refreshToken()}>Refresh</button>
    </div>
  )
}

describe('AuthContext Comprehensive Tests', () => {
  const mockUseAuth0 = useAuth0
  const mockLoginWithRedirect = jest.fn()
  const mockLogout = jest.fn()
  const mockGetAccessTokenSilently = jest.fn()
  const mockGetIdTokenClaims = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    process.env.VITE_AUTH0_AUDIENCE = 'test-audience'
    
    // Default Auth0 mock
    mockUseAuth0.mockReturnValue({
      user: {
        email: 'test@example.com',
        name: 'Test User',
        picture: 'https://example.com/avatar.jpg'
      },
      isAuthenticated: false,
      isLoading: false,
      loginWithRedirect: mockLoginWithRedirect,
      logout: mockLogout,
      getAccessTokenSilently: mockGetAccessTokenSilently,
      getIdTokenClaims: mockGetIdTokenClaims
    })
  })

  describe('Provider Setup and Context Access', () => {
    it('provides auth context to children', () => {
      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated')
    })

    it('throws error when useAuth is used outside provider', () => {
      // Suppress console.error for this test
      const originalError = console.error
      console.error = jest.fn()

      expect(() => {
        render(<TestAuthComponent />)
      }).toThrow('useAuth must be used within an AuthProvider')

      console.error = originalError
    })
  })

  describe('Authentication States', () => {
    it('shows loading state', () => {
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isLoading: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('loading')).toHaveTextContent('loading')
    })

    it('shows authenticated state', () => {
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')
    })

    it('shows unauthenticated state', () => {
      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated')
    })
  })

  describe('Token Management', () => {
    it('fetches access token when authenticated', async () => {
      mockGetAccessTokenSilently.mockResolvedValue('mock-access-token')
      mockGetIdTokenClaims.mockResolvedValue({
        sub: 'auth0|123456',
        aud: 'test-audience'
      })

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(mockGetAccessTokenSilently).toHaveBeenCalledWith({
          authorizationParams: {
            audience: 'test-audience',
            scope: 'openid profile email'
          }
        })
      })

      expect(screen.getByTestId('access-token')).toHaveTextContent('mock-access-token')
    })

    it('fetches user profile with claims', async () => {
      mockGetAccessTokenSilently.mockResolvedValue('token')
      mockGetIdTokenClaims.mockResolvedValue({
        sub: 'auth0|123456',
        email_verified: true
      })

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true,
        user: {
          email: 'user@example.com',
          name: 'John Doe'
        }
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('user@example.com')
        expect(screen.getByTestId('user-name')).toHaveTextContent('John Doe')
      })
    })

    it('handles token fetch errors gracefully', async () => {
      mockGetAccessTokenSilently.mockRejectedValue(new Error('Token fetch failed'))

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(logError).toHaveBeenCalledWith('Error getting access token:', expect.any(Error))
      })

      expect(screen.getByTestId('access-token')).toHaveTextContent('no-token')
    })

    it('refreshes token on demand', async () => {
      mockGetAccessTokenSilently
        .mockResolvedValueOnce('initial-token')
        .mockResolvedValueOnce('refreshed-token')

      mockGetIdTokenClaims.mockResolvedValue({ sub: 'auth0|123456' })

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      // Wait for initial token
      await waitFor(() => {
        expect(screen.getByTestId('access-token')).toHaveTextContent('initial-token')
      })

      // Trigger refresh
      await act(async () => {
        screen.getByText('Refresh').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('access-token')).toHaveTextContent('refreshed-token')
      })
    })
  })

  describe('Authentication Actions', () => {
    it('calls login when login action is triggered', () => {
      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      screen.getByText('Login').click()

      expect(mockLoginWithRedirect).toHaveBeenCalled()
    })

    it('calls logout when logout action is triggered', () => {
      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      screen.getByText('Logout').click()

      expect(mockLogout).toHaveBeenCalledWith({
        logoutParams: {
          returnTo: window.location.origin
        }
      })
    })

    it('provides login with custom options', () => {
      const TestCustomLogin = () => {
        const { login } = useAuth()
        return (
          <button onClick={() => login({ screen_hint: 'signup' })}>
            Custom Login
          </button>
        )
      }

      render(
        <AuthProvider>
          <TestCustomLogin />
        </AuthProvider>
      )

      screen.getByText('Custom Login').click()

      expect(mockLoginWithRedirect).toHaveBeenCalledWith({ screen_hint: 'signup' })
    })
  })

  describe('Authentication State Transitions', () => {
    it('handles transition from unauthenticated to authenticated', async () => {
      mockGetAccessTokenSilently.mockResolvedValue('new-token')
      mockGetIdTokenClaims.mockResolvedValue({ sub: 'auth0|123456' })

      // Start unauthenticated
      const { rerender } = render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated')

      // Change to authenticated
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true,
        user: { email: 'test@example.com', name: 'Test User' }
      })

      rerender(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')
        expect(screen.getByTestId('access-token')).toHaveTextContent('new-token')
      })
    })

    it('handles transition from authenticated to unauthenticated', () => {
      // Start authenticated
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      const { rerender } = render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated')

      // Change to unauthenticated
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: false,
        user: null
      })

      rerender(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated')
    })

    it('clears tokens when becoming unauthenticated', () => {
      // Start with tokens
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      const { rerender } = render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      // Change to unauthenticated
      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: false
      })

      rerender(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('access-token')).toHaveTextContent('no-token')
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-email')
    })
  })

  describe('Error Scenarios', () => {
    it('handles missing environment variables', async () => {
      delete process.env.VITE_AUTH0_AUDIENCE

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(mockGetAccessTokenSilently).toHaveBeenCalledWith({
          authorizationParams: {
            audience: undefined,
            scope: 'openid profile email'
          }
        })
      })
    })

    it('handles token claims fetch errors', async () => {
      mockGetAccessTokenSilently.mockResolvedValue('token')
      mockGetIdTokenClaims.mockRejectedValue(new Error('Claims fetch failed'))

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      render(
        <AuthProvider>
          <TestAuthComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(logError).toHaveBeenCalledWith('Error getting access token:', expect.any(Error))
      })
    })

    it('handles concurrent token refresh attempts', async () => {
      let resolveTokenFetch
      const tokenPromise = new Promise(resolve => {
        resolveTokenFetch = resolve
      })
      
      mockGetAccessTokenSilently.mockReturnValue(tokenPromise)
      mockGetIdTokenClaims.mockResolvedValue({ sub: 'auth0|123456' })

      mockUseAuth0.mockReturnValue({
        ...mockUseAuth0(),
        isAuthenticated: true
      })

      const TestConcurrentRefresh = () => {
        const { refreshToken } = useAuth()
        return (
          <div>
            <button onClick={() => refreshToken()}>Refresh 1</button>
            <button onClick={() => refreshToken()}>Refresh 2</button>
          </div>
        )
      }

      render(
        <AuthProvider>
          <TestConcurrentRefresh />
        </AuthProvider>
      )

      // Trigger concurrent refreshes
      screen.getByText('Refresh 1').click()
      screen.getByText('Refresh 2').click()

      // Resolve the promise
      resolveTokenFetch('concurrent-token')

      await waitFor(() => {
        // Should only call once despite multiple refresh attempts
        expect(mockGetAccessTokenSilently).toHaveBeenCalledTimes(2) // Initial + refresh
      })
    })
  })
})