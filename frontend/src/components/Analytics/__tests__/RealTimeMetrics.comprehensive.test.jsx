import { render, screen, waitFor } from '@testing-library/react'

// Mock logger first
jest.mock('../../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
}))

// Mock Auth context
jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    accessToken: 'test-token',
    refreshToken: jest.fn(),
    isAuthenticated: true
  })
}))

// Mock real-time data hooks
const mockAnalyticsData = {
  data: {
    totalViews: 150000,
    totalEngagement: 9200,
    totalFollowers: 16500,
    engagementRate: 7.2,
    viewsChange: 15.3,
    engagementChange: 5.1,
    followersChange: 12.8,
    engagementRateChange: 2.1
  },
  isLoading: false,
  error: null,
  lastUpdated: new Date('2025-07-26T10:30:00Z')
}

const mockPerformanceData = {
  data: {
    avgResponseTime: 0.8,
    uptime: 99.9,
    activeUsers: 158,
    requestsPerSecond: 45
  },
  isLoading: false,
  error: null,
  lastUpdated: new Date('2025-07-26T10:29:00Z')
}

jest.mock('../../../hooks/useRealTimeData', () => ({
  useRealTimeAnalytics: jest.fn(() => mockAnalyticsData),
  useRealTimePerformance: jest.fn(() => mockPerformanceData)
}))

import RealTimeMetrics from '../RealTimeMetrics'

describe('RealTimeMetrics Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders real-time metrics container', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Real-Time Analytics')).toBeInTheDocument()
      expect(screen.getByText('Live data updates every 30 seconds')).toBeInTheDocument()
    })

    it('accepts timeframe prop and passes it to hooks', () => {
      const { useRealTimeAnalytics } = require('../../../hooks/useRealTimeData')
      
      render(<RealTimeMetrics timeframe="30d" />)
      
      expect(useRealTimeAnalytics).toHaveBeenCalledWith('30d')
    })

    it('defaults to 7d timeframe when no prop provided', () => {
      const { useRealTimeAnalytics } = require('../../../hooks/useRealTimeData')
      
      render(<RealTimeMetrics />)
      
      expect(useRealTimeAnalytics).toHaveBeenCalledWith('7d')
    })
  })

  describe('Connection Status', () => {
    it('shows connected status when data is fresh', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Connected')).toBeInTheDocument()
      expect(screen.getByTestId('connection-status')).toHaveClass('text-green-600')
    })

    it('shows disconnected status when data is stale', () => {
      const staleDate = new Date()
      staleDate.setMinutes(staleDate.getMinutes() - 10) // 10 minutes ago
      
      mockAnalyticsData.lastUpdated = staleDate
      mockPerformanceData.lastUpdated = staleDate
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
      expect(screen.getByTestId('connection-status')).toHaveClass('text-red-600')
    })

    it('shows connecting status when loading', () => {
      mockAnalyticsData.isLoading = true
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Connecting')).toBeInTheDocument()
      expect(screen.getByTestId('connection-status')).toHaveClass('text-yellow-600')
    })
  })

  describe('Metric Cards Display', () => {
    it('displays total views metric with change indicator', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Total Views')).toBeInTheDocument()
      expect(screen.getByText('150,000')).toBeInTheDocument()
      expect(screen.getByText('+15.3%')).toBeInTheDocument()
    })

    it('displays engagement metric with change indicator', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Total Engagement')).toBeInTheDocument()
      expect(screen.getByText('9,200')).toBeInTheDocument()
      expect(screen.getByText('+5.1%')).toBeInTheDocument()
    })

    it('displays followers metric with change indicator', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Total Followers')).toBeInTheDocument()
      expect(screen.getByText('16,500')).toBeInTheDocument()
      expect(screen.getByText('+12.8%')).toBeInTheDocument()
    })

    it('displays engagement rate metric with change indicator', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Engagement Rate')).toBeInTheDocument()
      expect(screen.getByText('7.2%')).toBeInTheDocument()
      expect(screen.getByText('+2.1%')).toBeInTheDocument()
    })

    it('shows negative changes with red color and down arrow', () => {
      mockAnalyticsData.data.engagementChange = -3.2
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('-3.2%')).toBeInTheDocument()
      // Check for red color class
      const changeElement = screen.getByText('-3.2%').closest('.text-red-600')
      expect(changeElement).toBeInTheDocument()
    })

    it('shows positive changes with green color and up arrow', () => {
      render(<RealTimeMetrics />)
      
      const positiveChange = screen.getByText('+15.3%')
      expect(positiveChange).toBeInTheDocument()
      // Check for green color class
      const changeElement = positiveChange.closest('.text-green-600')
      expect(changeElement).toBeInTheDocument()
    })
  })

  describe('Performance Metrics', () => {
    it('displays active users count', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Active Users')).toBeInTheDocument()
      expect(screen.getByText('158')).toBeInTheDocument()
    })

    it('displays average response time', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Avg Response Time')).toBeInTheDocument()
      expect(screen.getByText('0.8s')).toBeInTheDocument()
    })

    it('displays posts today count', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Posts Today')).toBeInTheDocument()
      expect(screen.getByText('8')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error message when analytics data fails to load', () => {
      mockAnalyticsData.error = new Error('Analytics API failed')
      mockAnalyticsData.data = null
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Unable to load analytics data')).toBeInTheDocument()
      expect(screen.getByText('Analytics API failed')).toBeInTheDocument()
    })

    it('displays error message when performance data fails to load', () => {
      mockPerformanceData.error = new Error('Performance API failed')
      mockPerformanceData.data = null
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Unable to load performance data')).toBeInTheDocument()
      expect(screen.getByText('Performance API failed')).toBeInTheDocument()
    })

    it('shows retry button when data loading fails', () => {
      mockAnalyticsData.error = new Error('Failed to load')
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('shows loading skeleton when analytics is loading', () => {
      mockAnalyticsData.isLoading = true
      mockAnalyticsData.data = null
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByTestId('metrics-loading')).toBeInTheDocument()
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })

    it('shows loading skeleton when performance is loading', () => {
      mockPerformanceData.isLoading = true
      mockPerformanceData.data = null
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByTestId('performance-loading')).toBeInTheDocument()
    })
  })

  describe('Last Updated Display', () => {
    it('shows last updated timestamp', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText(/Last updated/)).toBeInTheDocument()
      expect(screen.getByText(/10:30/)).toBeInTheDocument() // Time from mock data
    })

    it('formats timestamp correctly', () => {
      render(<RealTimeMetrics />)
      
      // Should show time in HH:MM format
      expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument()
    })

    it('shows "Never" when no last updated time available', () => {
      mockAnalyticsData.lastUpdated = null
      mockPerformanceData.lastUpdated = null
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Never')).toBeInTheDocument()
    })
  })

  describe('Data Formatting', () => {
    it('formats large numbers with commas', () => {
      mockAnalyticsData.data.totalViews = 1234567
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('1,234,567')).toBeInTheDocument()
    })

    it('formats large numbers to K notation', () => {
      mockAnalyticsData.data.totalViews = 12500
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('12.5K')).toBeInTheDocument()
    })

    it('formats percentage values correctly', () => {
      mockAnalyticsData.data.engagementRate = 7.234
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('7.2%')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels for metrics', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByLabelText('Total Views: 150,000')).toBeInTheDocument()
      expect(screen.getByLabelText('Total Engagement: 9,200')).toBeInTheDocument()
      expect(screen.getByLabelText('Total Followers: 16,500')).toBeInTheDocument()
      expect(screen.getByLabelText('Engagement Rate: 7.2%')).toBeInTheDocument()
    })

    it('has proper heading structure', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByRole('heading', { level: 2, name: 'Real-Time Analytics' })).toBeInTheDocument()
      expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(2) // Metrics and Performance sections
    })

    it('uses semantic HTML structure', () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByRole('main')).toBeInTheDocument()
      expect(screen.getAllByRole('region')).toHaveLength(2) // Analytics and Performance regions
    })
  })

  describe('Real-time Updates', () => {
    it('automatically updates metrics based on hook data', async () => {
      const { rerender } = render(<RealTimeMetrics />)
      
      expect(screen.getByText('150,000')).toBeInTheDocument()
      
      // Simulate data update
      mockAnalyticsData.data.totalViews = 151000
      mockAnalyticsData.lastUpdated = new Date()
      
      rerender(<RealTimeMetrics />)
      
      expect(screen.getByText('151,000')).toBeInTheDocument()
    })

    it('updates connection status when data freshness changes', async () => {
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('Connected')).toBeInTheDocument()
      
      // Simulate stale data
      const staleDate = new Date()
      staleDate.setMinutes(staleDate.getMinutes() - 10)
      mockAnalyticsData.lastUpdated = staleDate
      
      await waitFor(() => {
        expect(screen.queryByText('Connected')).not.toBeInTheDocument()
      })
    })
  })

  describe('Fallback Data', () => {
    it('shows fallback metrics when no data available', () => {
      mockAnalyticsData.data = null
      mockPerformanceData.data = null
      
      render(<RealTimeMetrics />)
      
      // Should show default/fallback values
      expect(screen.getByText('125,000')).toBeInTheDocument() // Default total views
      expect(screen.getByText('6.8%')).toBeInTheDocument() // Default engagement rate
    })

    it('gracefully handles partial data', () => {
      mockAnalyticsData.data = {
        totalViews: 150000,
        // Missing other fields
      }
      
      render(<RealTimeMetrics />)
      
      expect(screen.getByText('150,000')).toBeInTheDocument()
      // Should show defaults for missing fields
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })
})