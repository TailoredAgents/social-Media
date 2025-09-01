import { renderHook, act, waitFor } from '@testing-library/react'
import { Auth0Provider } from '@auth0/auth0-react'
import { AuthProvider, useAuth } from '../AuthContext'

// Mock Auth0
const mockAuth0 = {
  user: {
    sub: 'auth0|123456789',
    name: 'Test User',
    email: 'test@example.com',
    picture: 'https://example.com/avatar.jpg'
  },
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('mock-access-token'),
  getIdTokenClaims: jest.fn().mockResolvedValue({
    iss: 'https://test.auth0.com/',
    sub: 'auth0|123456789',
    aud: 'test-audience',
    roles: ['user'],
    permissions: ['read:profile']
  })
}

jest.mock('@auth0/auth0-react', () => ({
  ...jest.requireActual('@auth0/auth0-react'),
  useAuth0: () => mockAuth0,
  Auth0Provider: ({ children }) => children
}))

// Mock environment variables
const originalEnv = process.env
beforeAll(() => {
  process.env = {
    ...originalEnv,
    VITE_AUTH0_AUDIENCE: 'test-audience'
  }
})

afterAll(() => {
  process.env = originalEnv
})

const wrapper = ({ children }) => (
  <Auth0Provider
    domain="test-domain.auth0.com"
    clientId="test-client-id"
    authorizationParams={{
      redirectUri: window.location.origin,
      audience: 'test-audience'
    }}
  >
    <AuthProvider>
      {children}
    </AuthProvider>
  </Auth0Provider>
)

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('provides authentication state when authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.accessToken).toBe('mock-access-token')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.userProfile).toEqual({
      ...mockAuth0.user,
      claims: {
        iss: 'https://test.auth0.com/',
        sub: 'auth0|123456789',
        aud: 'test-audience',
        roles: ['user'],
        permissions: ['read:profile']
      }
    })
  })

  it('handles unauthenticated state', async () => {
    jest.mocked(require('@auth0/auth0-react').useAuth0).mockReturnValue({
      ...mockAuth0,
      user: null,
      isAuthenticated: false,
      getAccessTokenSilently: jest.fn().mockRejectedValue(new Error('Not authenticated'))
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.accessToken).toBe(null)
    expect(result.current.userProfile).toBe(null)
  })

  it('handles loading state', () => {
    jest.mocked(require('@auth0/auth0-react').useAuth0).mockReturnValue({
      ...mockAuth0,
      isLoading: true
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.isLoading).toBe(true)
  })

  it('refreshes token successfully', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    let refreshedToken
    await act(async () => {
      refreshedToken = await result.current.refreshToken()
    })

    expect(mockAuth0.getAccessTokenSilently).toHaveBeenCalledWith({
      authorizationParams: {
        audience: 'test-audience',
        scope: 'openid profile email'
      }
    })
    expect(refreshedToken).toBe('mock-access-token')
  })

  it('handles token refresh failure', async () => {
    const refreshError = new Error('Token refresh failed')
    mockAuth0.getAccessTokenSilently.mockRejectedValueOnce(refreshError)

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      try {
        await result.current.refreshToken()
      } catch (error) {
        expect(error).toBe(refreshError)
      }
    })
  })

  it('handles getAccessTokenSilently failure during initialization', async () => {
    mockAuth0.getAccessTokenSilently.mockRejectedValueOnce(new Error('Token error'))

    const { result } = renderHook(() => useAuth(), { wrapper })

    // Should handle the error gracefully without crashing
    await waitFor(() => {
      expect(result.current.accessToken).toBe(null)
    })
  })

  it('handles getIdTokenClaims failure during initialization', async () => {
    mockAuth0.getIdTokenClaims.mockRejectedValueOnce(new Error('Claims error'))

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.accessToken).toBe('mock-access-token')
      expect(result.current.userProfile.claims).toBeUndefined()
    })
  })

  it('exposes Auth0 methods correctly', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.loginWithRedirect).toBe(mockAuth0.loginWithRedirect)
    expect(result.current.logout).toBe(mockAuth0.logout)
    expect(result.current.user).toBe(mockAuth0.user)
  })

  it('throws error when used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleSpy.mockRestore()
  })

  it('updates access token when Auth0 state changes', async () => {
    let mockAuth0State = {
      ...mockAuth0,
      getAccessTokenSilently: jest.fn().mockResolvedValue('initial-token')
    }

    jest.mocked(require('@auth0/auth0-react').useAuth0).mockReturnValue(mockAuth0State)

    const { result, rerender } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.accessToken).toBe('initial-token')
    })

    // Simulate Auth0 state change
    mockAuth0State = {
      ...mockAuth0State,
      getAccessTokenSilently: jest.fn().mockResolvedValue('updated-token')
    }

    jest.mocked(require('@auth0/auth0-react').useAuth0).mockReturnValue(mockAuth0State)

    rerender()

    await waitFor(() => {
      expect(result.current.accessToken).toBe('updated-token')
    })
  })

  it('maintains user profile structure correctly', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.userProfile).toBeDefined()
    })

    const profile = result.current.userProfile
    expect(profile.sub).toBe('auth0|123456789')
    expect(profile.name).toBe('Test User')
    expect(profile.email).toBe('test@example.com')
    expect(profile.picture).toBe('https://example.com/avatar.jpg')
    expect(profile.claims.roles).toEqual(['user'])
    expect(profile.claims.permissions).toEqual(['read:profile'])
  })
})