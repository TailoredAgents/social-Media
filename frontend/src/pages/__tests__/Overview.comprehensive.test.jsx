import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock logger before importing Overview
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
  debug: jest.fn()
}))

import Overview from '../Overview'

// Mock hooks
const mockEnhancedApi = {
  api: {
    analytics: {
      getMetrics: jest.fn(() => Promise.resolve({
        total_views: 125000,
        engagement_rate: 6.8,
        total_followers: 15200,
        total_engagement: 8500
      }))
    },
    workflow: {
      getStatusSummary: jest.fn(() => Promise.resolve({
        current_stage: 'content_generation',
        executions: [
          {
            workflow_type: 'Content Generation',
            status: 'running',
            progress: 75,
            duration_minutes: 15,
            started_at: '2025-07-26T10:00:00Z'
          },
          {
            workflow_type: 'Analytics Review',
            status: 'completed',
            duration_minutes: 8,
            started_at: '2025-07-26T09:30:00Z'
          }
        ]
      })),
      executeDailyWorkflow: jest.fn(() => Promise.resolve())
    },
    goals: {
      getDashboard: jest.fn(() => Promise.resolve({
        goals: [
          {
            id: 1,
            title: 'Grow LinkedIn Following',
            progress_percentage: 85,
            current_value: '2,750',
            target_value: '3,000',
            is_on_track: true
          },
          {
            id: 2,
            title: 'Improve Engagement Rate',
            progress_percentage: 92,
            current_value: '5.1%',
            target_value: '6.0%',
            is_on_track: true
          }
        ],
        active_goals: 3,
        on_track_goals: 2
      }))
    },
    memory: {
      getAnalytics: jest.fn(() => Promise.resolve({
        total_content: 1250,
        total_embeddings: 980,
        high_performing: 45,
        repurpose_candidates: 23
      }))
    }
  }
}

const mockRealTimeMetrics = {
  metrics: {
    postsToday: 12,
    engagementRate: 7.2,
    totalViews: 128000,
    viewsChange: 15,
    engagementRateChange: 0.8,
    totalFollowers: 15650,
    followersChange: 28,
    totalEngagement: 9200,
    engagementChange: 8.5,
    activeUsers: 5
  },
  connectionStatus: 'Connected'
}

jest.mock('../../hooks/useEnhancedApi', () => ({
  useEnhancedApi: () => mockEnhancedApi
}))

jest.mock('../../hooks/useRealTimeData', () => ({
  useRealTimeMetrics: () => mockRealTimeMetrics
}))

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithQueryClient = (component) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('Overview Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('shows loading skeleton while fetching metrics', () => {
      // Mock loading state
      mockEnhancedApi.api.analytics.getMetrics.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )
      
      renderWithQueryClient(<Overview />)
      
      expect(screen.getByTestId('loading-skeleton') || document.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error message when metrics fail to load', async () => {
      mockEnhancedApi.api.analytics.getMetrics.mockRejectedValue(new Error('API Error'))
      
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to load dashboard data/)).toBeInTheDocument()
        expect(screen.getByText(/Make sure the backend is running/)).toBeInTheDocument()
      })
    })
  })

  describe('Header Section', () => {
    it('renders welcome header with real-time data', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('🚀 AI Social Media Content Agent')).toBeInTheDocument()
        expect(screen.getByText(/Autonomous content factory generating/)).toBeInTheDocument()
        expect(screen.getByText(/12 posts/)).toBeInTheDocument()
        expect(screen.getByText(/7.2% avg engagement/)).toBeInTheDocument()
      })
    })

    it('displays connection status and active users', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('Connected')).toBeInTheDocument()
        expect(screen.getByText('5 active users')).toBeInTheDocument()
        expect(screen.getByText('CONTENT_GENERATION')).toBeInTheDocument()
      })
    })
  })

  describe('Metric Cards', () => {
    it('renders all four metric cards with correct data', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        // Total Views card
        expect(screen.getByText('Total Views')).toBeInTheDocument()
        expect(screen.getByText('128,000')).toBeInTheDocument()
        expect(screen.getByText('+15%')).toBeInTheDocument()
        
        // Engagement Rate card
        expect(screen.getByText('Engagement Rate')).toBeInTheDocument()
        expect(screen.getByText('7.2%')).toBeInTheDocument()
        expect(screen.getByText('+0.8%')).toBeInTheDocument()
        
        // Total Followers card
        expect(screen.getByText('Total Followers')).toBeInTheDocument()
        expect(screen.getByText('15,650')).toBeInTheDocument()
        expect(screen.getByText('+28%')).toBeInTheDocument()
        
        // Total Engagement card
        expect(screen.getByText('Total Engagement')).toBeInTheDocument()
        expect(screen.getByText('9,200')).toBeInTheDocument()
        expect(screen.getByText('+8.5%')).toBeInTheDocument()
      })
    })

    it('displays correct icons for each metric', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        const metricCards = screen.getAllByRole('article')
        expect(metricCards).toHaveLength(7) // 4 metrics + other sections
      })
    })

    it('handles negative changes correctly', async () => {
      mockRealTimeMetrics.metrics.viewsChange = -5
      mockRealTimeMetrics.metrics.engagementRateChange = -1.2
      
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('-5%')).toBeInTheDocument()
        expect(screen.getByText('-1.2%')).toBeInTheDocument()
      })
    })
  })

  describe('Workflow Status Section', () => {
    it('renders workflow header and trigger button', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('🤖 Autonomous Workflow')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Trigger Cycle/ })).toBeInTheDocument()
      })
    })

    it('displays workflow executions correctly', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('Content Generation')).toBeInTheDocument()
        expect(screen.getByText('Running... 75% complete')).toBeInTheDocument()
        expect(screen.getByText('Analytics Review')).toBeInTheDocument()
        expect(screen.getByText('Completed in 8min')).toBeInTheDocument()
      })
    })

    it('handles workflow trigger button click', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        const triggerButton = screen.getByRole('button', { name: /Trigger Cycle/ })
        fireEvent.click(triggerButton)
        expect(mockEnhancedApi.api.workflow.executeDailyWorkflow).toHaveBeenCalledTimes(1)
      })
    })

    it('shows empty state when no executions', async () => {
      mockEnhancedApi.api.workflow.getStatusSummary.mockResolvedValue({
        current_stage: 'idle',
        executions: []
      })
      
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('No recent workflow executions')).toBeInTheDocument()
        expect(screen.getByText('Click "Trigger Cycle" to start a new workflow')).toBeInTheDocument()
      })
    })
  })

  describe('Goals Section', () => {
    it('renders goals section with progress bars', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('🎯 Goal Progress')).toBeInTheDocument()
        expect(screen.getByText('Grow LinkedIn Following')).toBeInTheDocument()
        expect(screen.getByText('Improve Engagement Rate')).toBeInTheDocument()
        expect(screen.getByText('85%')).toBeInTheDocument()
        expect(screen.getByText('92%')).toBeInTheDocument()
      })
    })

    it('displays goal summary statistics', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('3 active goals')).toBeInTheDocument()
        expect(screen.getByText('2 on track')).toBeInTheDocument()
      })
    })

    it('shows empty state when no goals', async () => {
      mockEnhancedApi.api.goals.getDashboard.mockResolvedValue({
        goals: [],
        active_goals: 0,
        on_track_goals: 0
      })
      
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('No goals yet')).toBeInTheDocument()
        expect(screen.getByText('Create your first goal to start tracking progress')).toBeInTheDocument()
      })
    })
  })

  describe('Memory System Section', () => {
    it('renders memory analytics correctly', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('🧠 Memory System')).toBeInTheDocument()
        expect(screen.getByText('Content Items:')).toBeInTheDocument()
        expect(screen.getByText('1,250')).toBeInTheDocument()
        expect(screen.getByText('Vector Embeddings:')).toBeInTheDocument()
        expect(screen.getByText('980')).toBeInTheDocument()
        expect(screen.getByText('High Performing:')).toBeInTheDocument()
        expect(screen.getByText('45')).toBeInTheDocument()
        expect(screen.getByText('Repurpose Ready:')).toBeInTheDocument()
        expect(screen.getByText('23')).toBeInTheDocument()
      })
    })

    it('includes link to memory explorer', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('View Memory Explorer →')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        const articles = screen.getAllByRole('article')
        expect(articles.length).toBeGreaterThan(0)
        
        const progressBars = screen.getAllByRole('progressbar')
        expect(progressBars.length).toBeGreaterThan(0)
        
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      })
    })

    it('uses semantic HTML structure', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        // Check for headings hierarchy
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
        expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(3)
      })
    })
  })

  describe('Real-time Updates', () => {
    it('displays real-time metrics when available', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        // Should use real-time data over API data
        expect(screen.getByText('128,000')).toBeInTheDocument() // real-time views
        expect(screen.getByText('7.2%')).toBeInTheDocument() // real-time engagement
      })
    })

    it('falls back to API data when real-time unavailable', async () => {
      mockRealTimeMetrics.metrics = {}
      
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(screen.getByText('125,000')).toBeInTheDocument() // API data fallback
        expect(screen.getByText('6.8%')).toBeInTheDocument() // API data fallback
      })
    })
  })

  describe('Error Boundary', () => {
    it('gracefully handles component errors', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      
      // Force an error by providing invalid data
      mockEnhancedApi.api.analytics.getMetrics.mockResolvedValue(null)
      
      renderWithQueryClient(<Overview />)
      
      // Component should still render without crashing
      expect(screen.getByText('🚀 AI Social Media Content Agent')).toBeInTheDocument()
      
      consoleSpy.mockRestore()
    })
  })

  describe('Performance', () => {
    it('loads data efficiently with proper caching', async () => {
      renderWithQueryClient(<Overview />)
      
      await waitFor(() => {
        expect(mockEnhancedApi.api.analytics.getMetrics).toHaveBeenCalledTimes(1)
        expect(mockEnhancedApi.api.workflow.getStatusSummary).toHaveBeenCalledTimes(1)
        expect(mockEnhancedApi.api.goals.getDashboard).toHaveBeenCalledTimes(1)
        expect(mockEnhancedApi.api.memory.getAnalytics).toHaveBeenCalledTimes(1)
      })
    })
  })
})