import React from 'react'
import { render, screen } from '@testing-library/react'
import { 
  TestWrapper, 
  renderWithProviders, 
  mockAuth0User, 
  createMockAuth0,
  testCleanup,
  mockWindowMethods,
  mockEnvVars 
} from './testUtils'

describe('Test Utils', () => {
  beforeEach(() => {
    testCleanup()
  })

  describe('TestWrapper', () => {
    it('renders children without error', () => {
      render(
        <TestWrapper>
          <div data-testid="test-content">Test Content</div>
        </TestWrapper>
      )
      
      expect(screen.getByTestId('test-content')).toBeInTheDocument()
    })

    it('provides routing context', () => {
      render(
        <TestWrapper initialEntries={['/test']}>
          <div data-testid="test-content">Test Content</div>
        </TestWrapper>
      )
      
      expect(screen.getByTestId('test-content')).toBeInTheDocument()
    })
  })

  describe('renderWithProviders', () => {
    it('renders component with all providers', () => {
      const TestComponent = () => <div data-testid="test-component">Hello Test</div>
      
      renderWithProviders(<TestComponent />)
      
      expect(screen.getByTestId('test-component')).toBeInTheDocument()
      expect(screen.getByText('Hello Test')).toBeInTheDocument()
    })
  })

  describe('mockAuth0User', () => {
    it('has required user properties', () => {
      expect(mockAuth0User).toHaveProperty('name')
      expect(mockAuth0User).toHaveProperty('email')
      expect(mockAuth0User).toHaveProperty('picture')
      expect(mockAuth0User).toHaveProperty('sub')
      
      expect(mockAuth0User.name).toBe('Test User')
      expect(mockAuth0User.email).toBe('test@example.com')
    })
  })

  describe('createMockAuth0', () => {
    it('creates mock with default values', () => {
      const mockAuth0 = createMockAuth0()
      
      expect(mockAuth0.user).toEqual(mockAuth0User)
      expect(mockAuth0.isAuthenticated).toBe(true)
      expect(mockAuth0.isLoading).toBe(false)
      expect(typeof mockAuth0.loginWithRedirect).toBe('function')
      expect(typeof mockAuth0.logout).toBe('function')
    })

    it('allows overriding default values', () => {
      const mockAuth0 = createMockAuth0({
        isAuthenticated: false,
        isLoading: true
      })
      
      expect(mockAuth0.isAuthenticated).toBe(false)
      expect(mockAuth0.isLoading).toBe(true)
      expect(mockAuth0.user).toEqual(mockAuth0User) // Should still have default user
    })
  })

  describe('mockWindowMethods', () => {
    it('creates mock dispatch event function', () => {
      const { mockDispatchEvent } = mockWindowMethods()
      
      expect(typeof mockDispatchEvent).toBe('function')
      expect(mockDispatchEvent).toHaveBeenCalledTimes(0)
    })
  })

  describe('mockEnvVars', () => {
    it('provides test environment variables', () => {
      expect(mockEnvVars).toHaveProperty('VITE_AUTH0_DOMAIN')
      expect(mockEnvVars).toHaveProperty('VITE_AUTH0_CLIENT_ID')
      expect(mockEnvVars).toHaveProperty('VITE_AUTH0_AUDIENCE')
      
      expect(mockEnvVars.VITE_AUTH0_DOMAIN).toBe('test-domain.auth0.com')
      expect(mockEnvVars.VITE_AUTH0_CLIENT_ID).toBe('test-client-id')
    })
  })
})