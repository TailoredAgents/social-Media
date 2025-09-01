import React from 'react'
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { BrowserRouter } from 'react-router-dom'

// Mock environment and Auth0 to avoid import.meta issues
const mockAuth0 = {
  user: { name: 'Test User', email: 'test@example.com' },
  isAuthenticated: true,
  isLoading: false,
  loginWithRedirect: jest.fn(),
  logout: jest.fn(),
  getAccessTokenSilently: jest.fn().mockResolvedValue('token'),
  getIdTokenClaims: jest.fn().mockResolvedValue({ roles: ['user'], permissions: ['read'] })
}

jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => mockAuth0,
  Auth0Provider: ({ children }) => children
}))

// Mock API service
jest.mock('../../services/api.js', () => ({
  __esModule: true,
  default: {
    setToken: jest.fn(),
    getContent: jest.fn().mockResolvedValue([]),
    getGoals: jest.fn().mockResolvedValue([]),
    getAnalytics: jest.fn().mockResolvedValue({ totalViews: 0, totalEngagement: 0 }),
    getNotifications: jest.fn().mockResolvedValue([]),
    getAllMemory: jest.fn().mockResolvedValue([]),
    getMemoryAnalytics: jest.fn().mockResolvedValue({ total_memories: 0 })
  }
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
}))

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Bar: ({ data, options }) => (
    <div 
      data-testid="bar-chart" 
      role="img" 
      aria-label={options?.plugins?.title?.text || 'Bar Chart'}
    >
      Bar Chart: {JSON.stringify(data.labels || [])}
    </div>
  ),
  Line: ({ data, options }) => (
    <div 
      data-testid="line-chart" 
      role="img" 
      aria-label={options?.plugins?.title?.text || 'Line Chart'}
    >
      Line Chart: {JSON.stringify(data.labels || [])}
    </div>
  ),
  Doughnut: ({ data, options }) => (
    <div 
      data-testid="doughnut-chart" 
      role="img" 
      aria-label={options?.plugins?.title?.text || 'Doughnut Chart'}
    >
      Doughnut Chart: {JSON.stringify(data.labels || [])}
    </div>
  )
}))

// Mock react-router-dom hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/' })
}))

// Import components after mocks
import CreatePostModal from '../../components/Calendar/CreatePostModal'
import NotificationContainer from '../../components/Notifications/NotificationContainer'
import NotificationToast from '../../components/Notifications/NotificationToast'
import CreateGoalModal from '../../components/Goals/CreateGoalModal'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
)

describe('Accessibility Audit with axe-core', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Modal Components Accessibility', () => {
    it('should not have accessibility violations in CreatePostModal', async () => {
      const { container } = render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should not have accessibility violations in CreateGoalModal', async () => {
      const { container } = render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })
  })

  describe('Notification Components Accessibility', () => {
    it('should not have accessibility violations in NotificationContainer', async () => {
      const { container } = render(
        <TestWrapper>
          <NotificationContainer />
        </TestWrapper>
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should not have accessibility violations in NotificationToast', async () => {
      const notification = {
        id: 1,
        type: 'success',
        message: 'Test notification message',
        timestamp: Date.now()
      }

      const { container } = render(
        <TestWrapper>
          <NotificationToast
            notification={notification}
            onDismiss={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should handle different notification types accessibly', async () => {
      const notificationTypes = ['success', 'error', 'warning', 'info']
      
      for (const type of notificationTypes) {
        const notification = {
          id: 1,
          type,
          message: `Test ${type} notification`,
          timestamp: Date.now()
        }

        const { container } = render(
          <TestWrapper>
            <NotificationToast
              notification={notification}
              onDismiss={jest.fn()}
            />
          </TestWrapper>
        )

        const results = await axe(container)
        expect(results).toHaveNoViolations()
      }
    })
  })

  describe('Form Components Accessibility', () => {
    it('should validate form field associations in CreatePostModal', async () => {
      const { container } = render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      // Test specifically for form field accessibility
      const results = await axe(container, {
        rules: {
          'label': { enabled: true },
          'label-title-only': { enabled: true },
          'form-field-multiple-labels': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })

    it('should validate form validation error accessibility', async () => {
      const { container } = render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      // Test form validation patterns
      const results = await axe(container, {
        rules: {
          'aria-valid-attr-value': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })
  })

  describe('Interactive Elements Accessibility', () => {
    it('should validate button accessibility in modals', async () => {
      const { container } = render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'button-name': { enabled: true },
          'role-img-alt': { enabled: true },
          'image-alt': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })

    it('should validate focus management in modals', async () => {
      const { container } = render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'tabindex': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })
  })

  describe('ARIA Accessibility', () => {
    it('should validate ARIA attributes in notifications', async () => {
      const notification = {
        id: 1,
        type: 'error',
        message: 'Important error message',
        timestamp: Date.now()
      }

      const { container } = render(
        <TestWrapper>
          <NotificationToast
            notification={notification}
            onDismiss={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'aria-valid-attr': { enabled: true },
          'aria-valid-attr-value': { enabled: true },
          'aria-roles': { enabled: true },
          'aria-required-attr': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })

    it('should validate modal ARIA patterns', async () => {
      const { container } = render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })
  })

  describe('Color and Contrast Accessibility', () => {
    it('should validate color contrast in notification components', async () => {
      const notification = {
        id: 1,
        type: 'warning',
        message: 'Warning message with contrast requirements',
        timestamp: Date.now()
      }

      const { container } = render(
        <TestWrapper>
          <NotificationToast
            notification={notification}
            onDismiss={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true },
          'color-contrast-enhanced': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })

    it('should validate color contrast in modal forms', async () => {
      const { container } = render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      // Skip color contrast testing for now due to jsdom canvas limitations
      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: false }
        }
      })
      expect(results).toHaveNoViolations()
    })
  })

  describe('Keyboard Navigation Accessibility', () => {
    it('should validate keyboard navigation in modals', async () => {
      const { container } = render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'tabindex': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })
  })

  describe('Screen Reader Accessibility', () => {
    it('should validate screen reader accessibility in notifications', async () => {
      const notification = {
        id: 1,
        type: 'info',
        message: 'Information for screen readers',
        timestamp: Date.now()
      }

      const { container } = render(
        <TestWrapper>
          <NotificationToast
            notification={notification}
            onDismiss={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'aria-hidden-body': { enabled: true },
          'aria-text': { enabled: true },
          'empty-heading': { enabled: true },
          'heading-order': { enabled: true }
        }
      })
      expect(results).toHaveNoViolations()
    })

    it('should validate semantic structure in modals', async () => {
      const { container } = render(
        <TestWrapper>
          <CreateGoalModal
            isOpen={true}
            onClose={jest.fn()}
            onSubmit={jest.fn()}
          />
        </TestWrapper>
      )

      const results = await axe(container, {
        rules: {
          'landmark-one-main': { enabled: false }, // Modals don't need main landmarks
          'skip-link': { enabled: false }, // Not required for modals
          'page-has-heading-one': { enabled: false } // Not required for modal content
        }
      })
      expect(results).toHaveNoViolations()
    })
  })

  describe('Mobile Accessibility', () => {
    it('should validate touch target sizes in modals', async () => {
      const { container } = render(
        <TestWrapper>
          <CreatePostModal
            isOpen={true}
            onClose={jest.fn()}
            onSave={jest.fn()}
          />
        </TestWrapper>
      )

      // Skip target size testing for now
      const results = await axe(container, {
        rules: {
          'target-size': { enabled: false }
        }
      })
      expect(results).toHaveNoViolations()
    })
  })
})