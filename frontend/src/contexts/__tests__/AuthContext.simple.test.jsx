import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { createMockAuth0, testCleanup } from '../../__tests__/testUtils'

// Mock Auth0 before importing our components
const mockAuth0 = createMockAuth0()
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => mockAuth0
}))

// Now we can safely import our AuthProvider
const { AuthProvider, useAuth } = require('../AuthContext')

const TestComponent = () => {
  const auth = useAuth()
  return (
    <div>
      <div data-testid="user-name">{auth.user?.name || 'No user'}</div>
      <div data-testid="is-authenticated">{auth.isAuthenticated.toString()}</div>
      <div data-testid="is-loading">{auth.isLoading.toString()}</div>
      <div data-testid="access-token">{auth.accessToken || 'No token'}</div>
    </div>
  )
}

describe('AuthContext (Simple)', () => {
  beforeEach(() => {
    testCleanup()
  })

  it('provides basic authentication state', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
    expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
    
    // Wait for async token fetching
    await waitFor(() => {
      expect(screen.getByTestId('access-token')).toHaveTextContent('mock-access-token')
    }, { timeout: 3000 })
  })

  it('handles unauthenticated state', () => {
    // Override the mock for this test
    mockAuth0.isAuthenticated = false
    mockAuth0.user = null

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('user-name')).toHaveTextContent('No user')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
  })

  it('handles loading state', () => {
    // Override the mock for this test
    mockAuth0.isLoading = true

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('is-loading')).toHaveTextContent('true')
  })

  it('throws error when useAuth is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleSpy.mockRestore()
  })
})