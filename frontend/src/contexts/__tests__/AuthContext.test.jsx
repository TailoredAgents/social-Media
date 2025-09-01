import React from 'react'
import { render, screen, act, waitFor } from '@testing-library/react'
import { useAuth0 } from '@auth0/auth0-react'
import { AuthProvider, useAuth } from '../AuthContext'

// Mock Auth0
jest.mock('@auth0/auth0-react')

const mockUseAuth0 = {
  user: {
    name: 'Test User',
    email: 'test@example.com',
    picture: 'https://example.com/avatar.jpg'
  },
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn(),
  getIdTokenClaims: jest.fn()
}

const TestComponent = () => {
  const auth = useAuth()
  return (
    <div>
      <div data-testid="user-name">{auth.user?.name || 'No user'}</div>
      <div data-testid="is-authenticated">{auth.isAuthenticated.toString()}</div>
      <div data-testid="is-loading">{auth.isLoading.toString()}</div>
      <div data-testid="access-token">{auth.accessToken || 'No token'}</div>
      <button onClick={auth.login}>Login</button>
      <button onClick={auth.logout}>Logout</button>
      <div data-testid="has-admin-role">{auth.hasRole('admin').toString()}</div>
      <div data-testid="has-write-permission">{auth.hasPermission('write').toString()}</div>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    useAuth0.mockReturnValue(mockUseAuth0)
  })

  it('provides authentication state to children', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('user-name')).toHaveTextContent('Test User')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
    expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
  })

  it('handles unauthenticated state', () => {
    useAuth0.mockReturnValue({
      ...mockUseAuth0,
      user: null,
      isAuthenticated: false
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('user-name')).toHaveTextContent('No user')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
  })

  it('handles loading state', () => {
    useAuth0.mockReturnValue({
      ...mockUseAuth0,
      isLoading: true
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('is-loading')).toHaveTextContent('true')
  })

  it('gets access token when authenticated', async () => {
    const mockToken = 'mock-access-token'
    mockUseAuth0.getAccessTokenSilently.mockResolvedValue(mockToken)
    mockUseAuth0.getIdTokenClaims.mockResolvedValue({
      roles: ['user'],
      permissions: ['read']
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('access-token')).toHaveTextContent(mockToken)
    })

    expect(mockUseAuth0.getAccessTokenSilently).toHaveBeenCalledWith({
      authorizationParams: {
        audience: undefined, // VITE_AUTH0_AUDIENCE env var
        scope: 'openid profile email'
      }
    })
  })

  it('handles token error gracefully', async () => {
    mockUseAuth0.getAccessTokenSilently.mockRejectedValue(new Error('Token error'))
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error getting access token:', expect.any(Error))
    })

    consoleSpy.mockRestore()
  })

  it('calls loginWithRedirect with correct parameters', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    const loginButton = screen.getByText('Login')
    loginButton.click()

    expect(mockUseAuth0.loginWithRedirect).toHaveBeenCalledWith({
      authorizationParams: {
        audience: undefined, // VITE_AUTH0_AUDIENCE env var
        scope: 'openid profile email'
      }
    })
  })

  it('calls logout with correct parameters', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    const logoutButton = screen.getByText('Logout')
    logoutButton.click()

    expect(mockUseAuth0.logout).toHaveBeenCalledWith({
      logoutParams: {
        returnTo: window.location.origin
      }
    })
  })

  it('refreshes token successfully', async () => {
    const mockNewToken = 'new-access-token'
    mockUseAuth0.getAccessTokenSilently.mockResolvedValue(mockNewToken)

    const TestRefreshComponent = () => {
      const auth = useAuth()
      const [refreshedToken, setRefreshedToken] = React.useState('')

      const handleRefresh = async () => {
        try {
          const token = await auth.refreshToken()
          setRefreshedToken(token)
        } catch (error) {
          setRefreshedToken('Error')
        }
      }

      return (
        <div>
          <button onClick={handleRefresh}>Refresh Token</button>
          <div data-testid="refreshed-token">{refreshedToken}</div>
        </div>
      )
    }

    render(
      <AuthProvider>
        <TestRefreshComponent />
      </AuthProvider>
    )

    const refreshButton = screen.getByText('Refresh Token')
    
    await act(async () => {
      refreshButton.click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('refreshed-token')).toHaveTextContent(mockNewToken)
    })

    expect(mockUseAuth0.getAccessTokenSilently).toHaveBeenCalledWith({
      authorizationParams: {
        audience: undefined,
        scope: 'openid profile email'
      },
      cacheMode: 'off'
    })
  })

  it('handles refresh token error', async () => {
    mockUseAuth0.getAccessTokenSilently.mockRejectedValue(new Error('Refresh error'))
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    const TestRefreshComponent = () => {
      const auth = useAuth()
      const [error, setError] = React.useState('')

      const handleRefresh = async () => {
        try {
          await auth.refreshToken()
        } catch (error) {
          setError('Error occurred')
        }
      }

      return (
        <div>
          <button onClick={handleRefresh}>Refresh Token</button>
          <div data-testid="refresh-error">{error}</div>
        </div>
      )
    }

    render(
      <AuthProvider>
        <TestRefreshComponent />
      </AuthProvider>
    )

    const refreshButton = screen.getByText('Refresh Token')
    
    await act(async () => {
      refreshButton.click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('refresh-error')).toHaveTextContent('Error occurred')
    })

    expect(consoleSpy).toHaveBeenCalledWith('Error refreshing token:', expect.any(Error))
    consoleSpy.mockRestore()
  })

  it('checks user roles correctly', async () => {
    mockUseAuth0.getAccessTokenSilently.mockResolvedValue('token')
    mockUseAuth0.getIdTokenClaims.mockResolvedValue({
      roles: ['admin', 'user'],
      permissions: ['read', 'write']
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('has-admin-role')).toHaveTextContent('true')
    })
  })

  it('checks user permissions correctly', async () => {
    mockUseAuth0.getAccessTokenSilently.mockResolvedValue('token')
    mockUseAuth0.getIdTokenClaims.mockResolvedValue({
      roles: ['user'],
      permissions: ['read', 'write']
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('has-write-permission')).toHaveTextContent('true')
    })
  })

  it('returns false for missing roles and permissions', async () => {
    mockUseAuth0.getAccessTokenSilently.mockResolvedValue('token')
    mockUseAuth0.getIdTokenClaims.mockResolvedValue({
      roles: ['user'],
      permissions: ['read']
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('has-admin-role')).toHaveTextContent('false')
    })
  })

  it('throws error when useAuth is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleSpy.mockRestore()
  })
})