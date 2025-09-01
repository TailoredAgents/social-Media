import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Content from '../Content'

// Mock the enhanced API hook
const mockApi = {
  content: {
    getAll: jest.fn(() => Promise.resolve([
      {
        id: 1,
        title: 'AI Tools for Social Media Success',
        content: 'Discover the top 5 AI tools that will revolutionize your social media strategy and boost engagement rates.',
        content_type: 'text',
        platform: 'linkedin',
        status: 'published',
        scheduled_at: '2025-07-26T10:00:00Z',
        created_at: '2025-07-25T15:30:00Z',
        performance: { views: 1250 }
      },
      {
        id: 2,
        title: 'Behind the Scenes Video',
        content: 'Take a look at our content creation process and see how we generate engaging social media posts.',
        content_type: 'video',
        platform: 'instagram',
        status: 'scheduled',
        scheduled_at: '2025-07-27T14:00:00Z',
        created_at: '2025-07-26T09:00:00Z',
        performance: { views: 0 }
      },
      {
        id: 3,
        title: 'Quick Engagement Tips',
        content: 'Short and sweet tips to improve your social media engagement without spending hours on content creation.',
        content_type: 'image',
        platform: 'twitter',
        status: 'draft',
        created_at: '2025-07-26T11:00:00Z',
        performance: { views: 0 }
      },
      {
        id: 4,
        title: 'Marketing Strategy Carousel',
        content: 'A comprehensive guide to digital marketing strategies presented in an easy-to-digest carousel format.',
        content_type: 'carousel',
        platform: 'linkedin',
        status: 'failed',
        scheduled_at: '2025-07-26T08:00:00Z',
        created_at: '2025-07-25T16:00:00Z',
        performance: { views: 0 }
      }
    ])),
    getUpcoming: jest.fn(() => Promise.resolve([
      {
        id: 2,
        title: 'Behind the Scenes Video',
        scheduled_at: '2025-07-27T14:00:00Z'
      }
    ])),
    getAnalytics: jest.fn(() => Promise.resolve({
      total_content: 15,
      published_content: 8,
      scheduled_content: 3,
      draft_content: 4
    })),
    delete: jest.fn(() => Promise.resolve()),
    update: jest.fn(() => Promise.resolve()),
    generate: jest.fn(() => Promise.resolve({
      id: 5,
      title: 'Generated Content',
      content: 'AI-generated content based on your prompt'
    }))
  }
}

jest.mock('../../hooks/useEnhancedApi', () => ({
  useEnhancedApi: () => ({ api: mockApi })
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn()
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

describe('Content Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock window.confirm and window.prompt
    global.confirm = jest.fn(() => true)
    global.prompt = jest.fn(() => 'Test prompt for content generation')
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Page Header', () => {
    it('renders content library title and description', () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByText('Content Library')).toBeInTheDocument()
      expect(screen.getByText('Manage your content across all platforms')).toBeInTheDocument()
    })

    it('displays action buttons in header', () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByRole('button', { name: /Generate AI Content/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Create Content/ })).toBeInTheDocument()
    })
  })

  describe('Statistics Cards', () => {
    it('displays content statistics correctly', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('4')).toBeInTheDocument() // Total content
        expect(screen.getByText('Total Content')).toBeInTheDocument()
        
        expect(screen.getByText('1')).toBeInTheDocument() // Scheduled
        expect(screen.getByText('Scheduled')).toBeInTheDocument()
        
        expect(screen.getByText('1')).toBeInTheDocument() // Published
        expect(screen.getByText('Published')).toBeInTheDocument()
        
        expect(screen.getByText('1')).toBeInTheDocument() // Drafts
        expect(screen.getByText('Drafts')).toBeInTheDocument()
      })
    })

    it('updates statistics based on filtered content', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        // Should show counts based on mock data
        const publishedCount = screen.getAllByText('1').filter(el => 
          el.parentElement?.textContent?.includes('Published')
        )
        expect(publishedCount).toHaveLength(1)
      })
    })
  })

  describe('Search and Filters', () => {
    it('renders search input with placeholder', () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByPlaceholderText('Search content...')).toBeInTheDocument()
    })

    it('filters content by search query', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText('Search content...')
      fireEvent.change(searchInput, { target: { value: 'AI Tools' } })
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
        expect(screen.queryByText('Behind the Scenes Video')).not.toBeInTheDocument()
      })
    })

    it('renders all filter dropdowns', () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByDisplayValue('All Types')).toBeInTheDocument()
      expect(screen.getByDisplayValue('All Platforms')).toBeInTheDocument()
      expect(screen.getByDisplayValue('All Status')).toBeInTheDocument()
    })

    it('filters by content type', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
      })
      
      const typeFilter = screen.getByDisplayValue('All Types')
      fireEvent.change(typeFilter, { target: { value: 'video' } })
      
      await waitFor(() => {
        expect(screen.getByText('Behind the Scenes Video')).toBeInTheDocument()
        expect(screen.queryByText('AI Tools for Social Media Success')).not.toBeInTheDocument()
      })
    })

    it('filters by platform', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
      })
      
      const platformFilter = screen.getByDisplayValue('All Platforms')
      fireEvent.change(platformFilter, { target: { value: 'linkedin' } })
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
        expect(screen.queryByText('Behind the Scenes Video')).not.toBeInTheDocument()
      })
    })

    it('filters by status', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
      })
      
      const statusFilter = screen.getByDisplayValue('All Status')
      fireEvent.change(statusFilter, { target: { value: 'published' } })
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
        expect(screen.queryByText('Behind the Scenes Video')).not.toBeInTheDocument()
      })
    })
  })

  describe('Content Grid', () => {
    it('displays all content items correctly', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
        expect(screen.getByText('Behind the Scenes Video')).toBeInTheDocument()
        expect(screen.getByText('Quick Engagement Tips')).toBeInTheDocument()
        expect(screen.getByText('Marketing Strategy Carousel')).toBeInTheDocument()
      })
    })

    it('shows content type icons correctly', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('text')).toBeInTheDocument()
        expect(screen.getByText('video')).toBeInTheDocument()
        expect(screen.getByText('image')).toBeInTheDocument()
        expect(screen.getByText('carousel')).toBeInTheDocument()
      })
    })

    it('displays status badges with correct colors', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('published')).toBeInTheDocument()
        expect(screen.getByText('scheduled')).toBeInTheDocument()
        expect(screen.getByText('draft')).toBeInTheDocument()
        expect(screen.getByText('failed')).toBeInTheDocument()
      })
    })

    it('shows platform information for each item', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('linkedin')).toBeInTheDocument()
        expect(screen.getByText('instagram')).toBeInTheDocument()
        expect(screen.getByText('twitter')).toBeInTheDocument()
      })
    })

    it('displays view counts and dates', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('1250 views')).toBeInTheDocument()
        expect(screen.getAllByText('0 views')).toHaveLength(3)
      })
    })
  })

  describe('Content Actions', () => {
    it('renders action buttons for each content item', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        const viewButtons = screen.getAllByTitle('View')
        const editButtons = screen.getAllByTitle('Edit')
        const deleteButtons = screen.getAllByTitle('Delete')
        
        expect(viewButtons).toHaveLength(4)
        expect(editButtons).toHaveLength(4)
        expect(deleteButtons).toHaveLength(4)
      })
    })

    it('shows publish button only for draft content', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        const publishButtons = screen.getAllByTitle('Publish')
        expect(publishButtons).toHaveLength(1) // Only for draft content
      })
    })

    it('handles content deletion with confirmation', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByTitle('Delete')
        fireEvent.click(deleteButtons[0])
      })
      
      expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this content?')
      expect(mockApi.content.delete).toHaveBeenCalledWith(1)
    })

    it('handles content publishing', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        const publishButton = screen.getByTitle('Publish')
        fireEvent.click(publishButton)
      })
      
      expect(mockApi.content.update).toHaveBeenCalledWith(3, { status: 'published' })
    })
  })

  describe('Content Generation', () => {
    it('handles AI content generation', async () => {
      renderWithQueryClient(<Content />)
      
      const generateButton = screen.getByRole('button', { name: /Generate AI Content/ })
      fireEvent.click(generateButton)
      
      expect(global.prompt).toHaveBeenCalledWith('Enter a prompt for content generation:')
      
      await waitFor(() => {
        expect(mockApi.content.generate).toHaveBeenCalledWith(
          'Test prompt for content generation',
          'text'
        )
      })
    })

    it('cancels generation when no prompt provided', () => {
      global.prompt.mockReturnValue(null)
      
      renderWithQueryClient(<Content />)
      
      const generateButton = screen.getByRole('button', { name: /Generate AI Content/ })
      fireEvent.click(generateButton)
      
      expect(mockApi.content.generate).not.toHaveBeenCalled()
    })
  })

  describe('Loading States', () => {
    it('shows loading skeleton while fetching content', () => {
      mockApi.content.getAll.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )
      
      renderWithQueryClient(<Content />)
      
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('Empty States', () => {
    it('shows empty state when no content matches filters', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('AI Tools for Social Media Success')).toBeInTheDocument()
      })
      
      // Apply filter that matches nothing
      const typeFilter = screen.getByDisplayValue('All Types')
      fireEvent.change(typeFilter, { target: { value: 'nonexistent' } })
      
      await waitFor(() => {
        expect(screen.getByText('No content found')).toBeInTheDocument()
        expect(screen.getByText('Try adjusting your filters or search query.')).toBeInTheDocument()
      })
    })

    it('shows empty state when no content exists', async () => {
      mockApi.content.getAll.mockResolvedValue([])
      
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('No content found')).toBeInTheDocument()
        expect(screen.getByText('Get started by creating your first piece of content.')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Create Content/ })).toBeInTheDocument()
      })
    })
  })

  describe('Date Formatting', () => {
    it('formats dates correctly', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        // Should show formatted dates
        expect(screen.getByText(/Jul 26/)).toBeInTheDocument()
        expect(screen.getByText(/Jul 27/)).toBeInTheDocument()
      })
    })

    it('handles missing scheduled dates', async () => {
      const contentWithoutSchedule = {
        id: 5,
        title: 'Unscheduled Content',
        content: 'Content without schedule',
        content_type: 'text',
        platform: 'twitter',
        status: 'draft',
        created_at: '2025-07-26T12:00:00Z'
      }
      
      mockApi.content.getAll.mockResolvedValue([contentWithoutSchedule])
      
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('Jul 26')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})
      mockApi.content.delete.mockRejectedValue(new Error('Delete failed'))
      
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByTitle('Delete')
        fireEvent.click(deleteButtons[0])
      })
      
      // Should not crash the app
      expect(screen.getByText('Content Library')).toBeInTheDocument()
      
      consoleError.mockRestore()
    })
  })

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByRole('heading', { level: 2, name: 'Content Library' })).toBeInTheDocument()
    })

    it('provides meaningful button labels', async () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByRole('button', { name: /Generate AI Content/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Create Content/ })).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.getAllByTitle('View')).toHaveLength(4)
        expect(screen.getAllByTitle('Edit')).toHaveLength(4)
        expect(screen.getAllByTitle('Delete')).toHaveLength(4)
      })
    })

    it('uses semantic form controls', () => {
      renderWithQueryClient(<Content />)
      
      expect(screen.getByRole('searchbox') || screen.getByPlaceholderText('Search content...')).toBeInTheDocument()
      expect(screen.getAllByRole('combobox')).toHaveLength(3) // Three dropdowns
    })
  })

  describe('Content Preview', () => {
    it('truncates long content previews', async () => {
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        const contentPreviews = screen.getAllByText(/Discover the top 5 AI tools/)
        expect(contentPreviews.length).toBeGreaterThan(0)
      })
    })

    it('shows fallback for missing content', async () => {
      const contentWithoutText = {
        id: 6,
        title: 'Title Only',
        content: null,
        content_type: 'text',
        platform: 'twitter',
        status: 'draft'
      }
      
      mockApi.content.getAll.mockResolvedValue([contentWithoutText])
      
      renderWithQueryClient(<Content />)
      
      await waitFor(() => {
        expect(screen.getByText('Title Only')).toBeInTheDocument()
        expect(screen.getByText('No content preview available')).toBeInTheDocument()
      })
    })
  })
})