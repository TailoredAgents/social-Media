import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import MemoryExplorer from '../MemoryExplorer'

// Mock dependencies
jest.mock('../../hooks/useApi', () => ({
  useApi: jest.fn()
}))

jest.mock('../../hooks/useEnhancedApi', () => ({
  useEnhancedApi: jest.fn()
}))

jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn()
}))

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Scatter: ({ data }) => (
    <div data-testid="scatter-chart" data-chart-data={JSON.stringify(data)}>
      Scatter Chart
    </div>
  )
}))

jest.mock('chart.js', () => ({
  Chart: { register: jest.fn() },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  PointElement: jest.fn(),
  LineElement: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn()
}))

// Mock ContentDetailModal
jest.mock('../../components/Memory/ContentDetailModal', () => {
  return function MockContentDetailModal({ content, isOpen, onClose, onRepurpose, onEdit, onDelete }) {
    if (!isOpen || !content) return null
    return (
      <div data-testid="content-detail-modal">
        <div>Content: {content.title}</div>
        <button onClick={() => onRepurpose(content.id, 'twitter-thread')}>Repurpose</button>
        <button onClick={() => onEdit(content)}>Edit</button>
        <button onClick={() => onDelete(content.id)}>Delete</button>
        <button onClick={onClose}>Close</button>
      </div>
    )
  }
})

import { useApi } from '../../hooks/useApi'
import { useEnhancedApi } from '../../hooks/useEnhancedApi'

describe('MemoryExplorer Page', () => {
  const mockUseApi = useApi
  const mockUseEnhancedApi = useEnhancedApi
  const mockMakeAuthenticatedRequest = jest.fn()
  const mockMakeEnhancedRequest = jest.fn()

  const mockContent = [
    {
      id: 1,
      title: 'AI and Future of Work',
      body: 'Artificial intelligence is transforming how we work...',
      platform: 'LinkedIn',
      engagement: 250,
      views: 1500,
      created_at: '2023-12-01T10:00:00Z',
      tags: ['AI', 'Technology', 'Future'],
      similarity_score: 0.95,
      coordinates: { x: 0.2, y: 0.8 }
    },
    {
      id: 2,
      title: 'Social Media Trends 2024',
      body: 'The landscape of social media is evolving rapidly...',
      platform: 'Twitter',
      engagement: 180,
      views: 950,
      created_at: '2023-11-15T14:30:00Z',
      tags: ['Social Media', 'Trends', 'Marketing'],
      similarity_score: 0.87,
      coordinates: { x: 0.6, y: 0.4 }
    },
    {
      id: 3,
      title: 'Content Creation Best Practices',
      body: 'Creating engaging content requires strategy...',
      platform: 'Instagram',
      engagement: 320,
      views: 2100,
      created_at: '2023-11-20T09:15:00Z',
      tags: ['Content', 'Best Practices', 'Strategy'],
      similarity_score: 0.72,
      coordinates: { x: 0.8, y: 0.6 }
    }
  ]

  const mockAnalytics = {
    total_content: 156,
    avg_engagement: 8.5,
    top_performing_tags: ['AI', 'Technology', 'Marketing'],
    content_distribution: {
      LinkedIn: 45,
      Twitter: 38,
      Instagram: 32,
      Facebook: 25
    }
  }

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  const TestWrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )

  beforeEach(() => {
    jest.clearAllMocks()
    
    mockUseApi.mockReturnValue({
      apiService: {
        getContentMemory: jest.fn(),
        searchContentMemory: jest.fn(),
        getMemoryAnalytics: jest.fn(),
        repurposeContent: jest.fn(),
        updateContent: jest.fn(),
        deleteContent: jest.fn()
      },
      makeAuthenticatedRequest: mockMakeAuthenticatedRequest
    })

    mockUseEnhancedApi.mockReturnValue({
      makeEnhancedRequest: mockMakeEnhancedRequest,
      connectionStatus: 'connected'
    })

    // Default API responses
    mockMakeAuthenticatedRequest
      .mockResolvedValueOnce(mockContent) // getContentMemory
      .mockResolvedValueOnce(mockAnalytics) // getMemoryAnalytics
  })

  describe('Basic Rendering', () => {
    it('renders memory explorer layout', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      expect(screen.getByText('Content Memory Explorer')).toBeInTheDocument()
      expect(screen.getByText('Discover insights and patterns in your content history')).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText('156 pieces of content')).toBeInTheDocument()
      })
    })

    it('displays loading state initially', () => {
      mockMakeAuthenticatedRequest.mockImplementation(() => new Promise(() => {}))

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      expect(screen.getByText('Loading content memory...')).toBeInTheDocument()
    })

    it('displays error state on API failure', async () => {
      mockMakeAuthenticatedRequest.mockRejectedValue(new Error('Failed to load content'))

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Error loading content memory')).toBeInTheDocument()
      })
    })
  })

  describe('Content Search and Filtering', () => {
    it('displays search functionality', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search content by keywords, tags, or content...')).toBeInTheDocument()
      })
    })

    it('performs search on input', async () => {
      mockMakeAuthenticatedRequest
        .mockResolvedValueOnce(mockContent) // Initial load
        .mockResolvedValueOnce(mockAnalytics) // Analytics
        .mockResolvedValueOnce([mockContent[0]]) // Search result

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search content by keywords, tags, or content...')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search content by keywords, tags, or content...')
      fireEvent.change(searchInput, { target: { value: 'AI technology' } })
      fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter' })

      await waitFor(() => {
        expect(mockMakeAuthenticatedRequest).toHaveBeenCalledWith(
          expect.any(Function),
          'AI technology'
        )
      })
    })

    it('filters by platform', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('All Platforms')).toBeInTheDocument()
      })

      const platformFilter = screen.getByDisplayValue('all')
      fireEvent.change(platformFilter, { target: { value: 'linkedin' } })

      expect(platformFilter.value).toBe('linkedin')
    })

    it('filters by date range', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('All Time')).toBeInTheDocument()
      })

      const dateFilter = screen.getByDisplayValue('all')
      fireEvent.change(dateFilter, { target: { value: '30d' } })

      expect(dateFilter.value).toBe('30d')
    })

    it('sorts content by different criteria', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent First')).toBeInTheDocument()
      })

      const sortSelect = screen.getByDisplayValue('recent')
      fireEvent.change(sortSelect, { target: { value: 'engagement' } })

      expect(sortSelect.value).toBe('engagement')
    })
  })

  describe('Content Visualization', () => {
    it('renders similarity scatter chart', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('scatter-chart')).toBeInTheDocument()
      })

      const chart = screen.getByTestId('scatter-chart')
      const chartData = JSON.parse(chart.getAttribute('data-chart-data'))
      expect(chartData.datasets[0].data).toHaveLength(3)
    })

    it('displays content grid', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI and Future of Work')).toBeInTheDocument()
        expect(screen.getByText('Social Media Trends 2024')).toBeInTheDocument()
        expect(screen.getByText('Content Creation Best Practices')).toBeInTheDocument()
      })
    })

    it('shows engagement metrics for each content item', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('250 engagements')).toBeInTheDocument()
        expect(screen.getByText('1,500 views')).toBeInTheDocument()
      })
    })

    it('displays tags for content items', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI')).toBeInTheDocument()
        expect(screen.getByText('Technology')).toBeInTheDocument()
        expect(screen.getByText('Future')).toBeInTheDocument()
      })
    })
  })

  describe('Content Detail Modal', () => {
    it('opens content detail modal when content item is clicked', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI and Future of Work')).toBeInTheDocument()
      })

      const contentItem = screen.getByText('AI and Future of Work')
      fireEvent.click(contentItem)

      expect(screen.getByTestId('content-detail-modal')).toBeInTheDocument()
      expect(screen.getByText('Content: AI and Future of Work')).toBeInTheDocument()
    })

    it('closes modal when close button is clicked', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI and Future of Work')).toBeInTheDocument()
      })

      // Open modal
      const contentItem = screen.getByText('AI and Future of Work')
      fireEvent.click(contentItem)

      expect(screen.getByTestId('content-detail-modal')).toBeInTheDocument()

      // Close modal
      const closeButton = screen.getByText('Close')
      fireEvent.click(closeButton)

      expect(screen.queryByTestId('content-detail-modal')).not.toBeInTheDocument()
    })

    it('handles content repurposing', async () => {
      mockMakeAuthenticatedRequest
        .mockResolvedValueOnce(mockContent) // Initial load
        .mockResolvedValueOnce(mockAnalytics) // Analytics
        .mockResolvedValueOnce({ id: 4, title: 'Repurposed Content' }) // Repurpose response

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI and Future of Work')).toBeInTheDocument()
      })

      // Open modal
      const contentItem = screen.getByText('AI and Future of Work')
      fireEvent.click(contentItem)

      // Click repurpose
      const repurposeButton = screen.getByText('Repurpose')
      fireEvent.click(repurposeButton)

      await waitFor(() => {
        expect(mockMakeAuthenticatedRequest).toHaveBeenCalledWith(
          expect.any(Function),
          1,
          'twitter-thread'
        )
      })
    })

    it('handles content editing', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI and Future of Work')).toBeInTheDocument()
      })

      // Open modal
      const contentItem = screen.getByText('AI and Future of Work')
      fireEvent.click(contentItem)

      // Click edit
      const editButton = screen.getByText('Edit')
      fireEvent.click(editButton)

      // Should trigger edit functionality
      expect(editButton).toBeInTheDocument()
    })

    it('handles content deletion', async () => {
      mockMakeAuthenticatedRequest
        .mockResolvedValueOnce(mockContent) // Initial load
        .mockResolvedValueOnce(mockAnalytics) // Analytics
        .mockResolvedValueOnce({}) // Delete response

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('AI and Future of Work')).toBeInTheDocument()
      })

      // Open modal
      const contentItem = screen.getByText('AI and Future of Work')
      fireEvent.click(contentItem)

      // Click delete
      const deleteButton = screen.getByText('Delete')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(mockMakeAuthenticatedRequest).toHaveBeenCalledWith(
          expect.any(Function),
          1
        )
      })
    })
  })

  describe('Analytics Display', () => {
    it('shows memory analytics', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('156 pieces of content')).toBeInTheDocument()
        expect(screen.getByText('8.5% avg engagement')).toBeInTheDocument()
      })
    })

    it('displays top performing tags', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Top Tags')).toBeInTheDocument()
        expect(screen.getByText('AI')).toBeInTheDocument()
        expect(screen.getByText('Technology')).toBeInTheDocument()
        expect(screen.getByText('Marketing')).toBeInTheDocument()
      })
    })

    it('shows content distribution by platform', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Platform Distribution')).toBeInTheDocument()
        expect(screen.getByText('LinkedIn: 45')).toBeInTheDocument()
        expect(screen.getByText('Twitter: 38')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('shows retry option on load error', async () => {
      mockMakeAuthenticatedRequest.mockRejectedValue(new Error('Network error'))

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Error loading content memory')).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /retry/i })
      expect(retryButton).toBeInTheDocument()
    })

    it('handles search errors gracefully', async () => {
      mockMakeAuthenticatedRequest
        .mockResolvedValueOnce(mockContent) // Initial load
        .mockResolvedValueOnce(mockAnalytics) // Analytics
        .mockRejectedValueOnce(new Error('Search failed')) // Search error

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search content by keywords, tags, or content...')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search content by keywords, tags, or content...')
      fireEvent.change(searchInput, { target: { value: 'test' } })
      fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter' })

      // Should handle error gracefully
      await waitFor(() => {
        expect(mockMakeAuthenticatedRequest).toHaveBeenCalledTimes(3)
      })
    })

    it('handles empty content state', async () => {
      mockMakeAuthenticatedRequest
        .mockResolvedValueOnce([]) // Empty content
        .mockResolvedValueOnce(mockAnalytics) // Analytics

      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('No content found')).toBeInTheDocument()
        expect(screen.getByText('Start creating content to build your content memory')).toBeInTheDocument()
      })
    })
  })

  describe('View Toggle', () => {
    it('toggles between chart and grid view', async () => {
      render(
        <TestWrapper>
          <MemoryExplorer />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('scatter-chart')).toBeInTheDocument()
      })

      const gridViewButton = screen.getByRole('button', { name: /grid view/i })
      fireEvent.click(gridViewButton)

      // Should switch to grid view
      expect(gridViewButton).toHaveClass('bg-blue-600')
    })
  })
})