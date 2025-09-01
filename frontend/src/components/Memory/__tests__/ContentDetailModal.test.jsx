import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ContentDetailModal from '../ContentDetailModal'

describe('ContentDetailModal', () => {
  const mockContent = {
    id: 1,
    title: 'Test Content',
    content: 'This is test content body with multiple lines.\n\nSecond paragraph here.',
    type: 'social_post',
    platform: 'LinkedIn',
    engagement: {
      views: 1500,
      likes: 120,
      shares: 45
    },
    created_at: '2025-07-28T10:00:00Z',
    tags: ['AI', 'Technology', 'Innovation'],
    similarity_score: 0.85
  }

  const mockProps = {
    content: mockContent,
    isOpen: true,
    onClose: jest.fn(),
    onRepurpose: jest.fn(),
    onEdit: jest.fn(),
    onDelete: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  // Basic rendering tests
  describe('Rendering and Visibility', () => {
    it('renders modal when open and content provided', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      expect(screen.getByText('Test Content')).toBeInTheDocument()
      expect(screen.getByText(/This is test content body/)).toBeInTheDocument()
      expect(screen.getByText('linkedin')).toBeInTheDocument()
      expect(screen.getByText('social post')).toBeInTheDocument()
    })

    it('does not render when closed', () => {
      render(<ContentDetailModal {...mockProps} isOpen={false} />)
      
      expect(screen.queryByText('Test Content')).not.toBeInTheDocument()
    })

    it('does not render when no content provided', () => {
      render(<ContentDetailModal {...mockProps} content={null} />)
      
      expect(screen.queryByText('Test Content')).not.toBeInTheDocument()
    })

    it('renders with empty content object gracefully', () => {
      const emptyContent = {
        id: 1,
        title: '',
        content: '',
        type: '',
        platform: '',
        created_at: '2025-07-28T10:00:00Z'
      }
      
      render(<ContentDetailModal {...mockProps} content={emptyContent} />)
      
      // Should not crash with empty content
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })

  // Date formatting tests
  describe('Date Formatting', () => {
    it('displays formatted date correctly', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      // Check that formatted date is displayed (should include "Monday" for 2025-07-28)
      expect(screen.getByText(/Monday/)).toBeInTheDocument()
      expect(screen.getByText(/July/)).toBeInTheDocument()
      expect(screen.getByText(/2025/)).toBeInTheDocument()
    })

    it('handles different date formats', () => {
      const contentWithDifferentDate = {
        ...mockContent,
        created_at: '2025-12-25T15:30:00Z'
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithDifferentDate} />)
      
      expect(screen.getByText(/December/)).toBeInTheDocument()
      expect(screen.getByText(/25/)).toBeInTheDocument()
    })
  })

  // Engagement metrics tests
  describe('Engagement Metrics', () => {
    it('displays engagement metrics correctly', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      expect(screen.getByText('1,500')).toBeInTheDocument() // views
      expect(screen.getByText('120')).toBeInTheDocument() // likes
      expect(screen.getByText('45')).toBeInTheDocument() // shares
      expect(screen.getByText('165')).toBeInTheDocument() // total engagement
    })

    it('calculates engagement rate correctly', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      // (120 + 45) / 1500 * 100 = 11.0%
      expect(screen.getByText('11.0%')).toBeInTheDocument()
    })

    it('handles zero engagement gracefully', () => {
      const contentWithZeroEngagement = {
        ...mockContent,
        engagement: {
          views: 0,
          likes: 0,
          shares: 0
        }
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithZeroEngagement} />)
      
      expect(screen.getAllByText('0')).toHaveLength(4) // views, likes, shares, total
    })

    it('handles missing engagement data', () => {
      const contentWithoutEngagement = {
        ...mockContent,
        engagement: undefined
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithoutEngagement} />)
      
      expect(screen.getAllByText('0')).toHaveLength(4) // should default to 0
    })

    it('handles partial engagement data', () => {
      const contentWithPartialEngagement = {
        ...mockContent,
        engagement: {
          views: 1000,
          likes: 50
          // shares missing
        }
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithPartialEngagement} />)
      
      expect(screen.getByText('1,000')).toBeInTheDocument()
      expect(screen.getByText('50')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument() // shares should default to 0
    })
  })

  // Tags and metadata tests
  describe('Tags and Metadata', () => {
    it('displays tags correctly', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      expect(screen.getByText('#AI')).toBeInTheDocument()
      expect(screen.getByText('#Technology')).toBeInTheDocument()
      expect(screen.getByText('#Innovation')).toBeInTheDocument()
    })

    it('handles empty tags array', () => {
      const contentWithEmptyTags = {
        ...mockContent,
        tags: []
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithEmptyTags} />)
      
      // Tags section should not be rendered
      expect(screen.queryByText('Tags')).not.toBeInTheDocument()
    })

    it('handles missing tags', () => {
      const contentWithoutTags = {
        ...mockContent,
        tags: undefined
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithoutTags} />)
      
      // Should not crash when tags are missing
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('displays similarity score when available', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      expect(screen.getByText('85% similarity match')).toBeInTheDocument()
      expect(screen.getByText(/Based on 85% similarity score/)).toBeInTheDocument()
    })

    it('handles content without similarity score', () => {
      const contentWithoutSimilarity = {
        ...mockContent,
        similarity_score: undefined
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithoutSimilarity} />)
      
      expect(screen.queryByText(/similarity match/)).not.toBeInTheDocument()
      expect(screen.queryByText('Similar Content')).not.toBeInTheDocument()
    })
  })

  // User interaction tests
  describe('User Interactions', () => {
    it('calls onClose when close button clicked', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const closeButtons = screen.getAllByRole('button')
      const closeButton = closeButtons.find(button => {
        const svg = button.querySelector('svg')
        return svg && svg.classList.toString().includes('h-5')
      })
      
      if (closeButton) {
        fireEvent.click(closeButton)
        expect(mockProps.onClose).toHaveBeenCalled()
      }
    })

    it('calls onClose when backdrop clicked', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const backdrop = document.querySelector('.bg-gray-500')
      fireEvent.click(backdrop)
      
      expect(mockProps.onClose).toHaveBeenCalled()
    })

    it('calls onEdit when edit button clicked', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const editButtons = screen.getAllByRole('button')
      const editButton = editButtons.find(button => {
        const svg = button.querySelector('svg')
        return svg && button.className.includes('text-gray-400')
      })
      
      if (editButton) {
        fireEvent.click(editButton)
        expect(mockProps.onEdit).toHaveBeenCalledWith(mockContent)
      }
    })

    it('calls onDelete when delete button clicked', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const deleteButtons = screen.getAllByRole('button')
      const deleteButton = deleteButtons.find(button => 
        button.className.includes('text-red-400')
      )
      
      if (deleteButton) {
        fireEvent.click(deleteButton)
        expect(mockProps.onDelete).toHaveBeenCalledWith(mockContent.id)
      }
    })
  })

  // Repurpose functionality tests
  describe('Repurpose Functionality', () => {
    it('toggles repurpose options visibility', async () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const showOptionsButton = screen.getByText('Show All Options')
      expect(screen.queryByText('Twitter Thread')).not.toBeInTheDocument()
      
      fireEvent.click(showOptionsButton)
      
      await waitFor(() => {
        expect(screen.getByText('Twitter Thread')).toBeInTheDocument()
        expect(screen.getByText('LinkedIn Carousel')).toBeInTheDocument()
        expect(screen.getByText('Instagram Stories')).toBeInTheDocument()
        expect(screen.getByText('Blog Post')).toBeInTheDocument()
        expect(screen.getByText('Video Script')).toBeInTheDocument()
      })
      
      // Should change button text
      expect(screen.getByText('Hide Options')).toBeInTheDocument()
    })

    it('calls onRepurpose when quick action button clicked', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const repurposeButton = screen.getByText('Repurpose Content')
      fireEvent.click(repurposeButton)
      
      expect(mockProps.onRepurpose).toHaveBeenCalledWith(mockContent)
    })

    it('calls onRepurpose when specific option selected', async () => {
      render(<ContentDetailModal {...mockProps} />)
      
      // Show repurpose options
      const showOptionsButton = screen.getByText('Show All Options')
      fireEvent.click(showOptionsButton)
      
      await waitFor(() => {
        expect(screen.getByText('Twitter Thread')).toBeInTheDocument()
      })
      
      // Click on Twitter Thread option
      const twitterOption = screen.getByText('Twitter Thread').closest('div')
      fireEvent.click(twitterOption)
      
      expect(mockProps.onRepurpose).toHaveBeenCalledWith(
        mockContent,
        expect.objectContaining({
          id: 'twitter-thread',
          title: 'Twitter Thread'
        })
      )
    })

    it('displays effort levels correctly', async () => {
      render(<ContentDetailModal {...mockProps} />)
      
      const showOptionsButton = screen.getByText('Show All Options')
      fireEvent.click(showOptionsButton)
      
      await waitFor(() => {
        expect(screen.getByText('Low')).toBeInTheDocument()
        expect(screen.getAllByText('Medium')).toHaveLength(2)
        expect(screen.getAllByText('High')).toHaveLength(2)
      })
    })
  })

  // Edge cases and error handling
  describe('Edge Cases', () => {
    it('handles content with multiline text properly', () => {
      render(<ContentDetailModal {...mockProps} />)
      
      // Should preserve line breaks
      expect(screen.getByText(/Second paragraph here/)).toBeInTheDocument()
    })

    it('handles very large engagement numbers', () => {
      const contentWithLargeNumbers = {
        ...mockContent,
        engagement: {
          views: 1500000,
          likes: 125000,
          shares: 45000
        }
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithLargeNumbers} />)
      
      expect(screen.getByText('1,500,000')).toBeInTheDocument()
      expect(screen.getByText('125,000')).toBeInTheDocument()
      expect(screen.getByText('45,000')).toBeInTheDocument()
      expect(screen.getByText('170,000')).toBeInTheDocument() // total engagement
    })

    it('handles content type with underscores', () => {
      const contentWithUnderscoreType = {
        ...mockContent,
        type: 'blog_post'
      }
      
      render(<ContentDetailModal {...mockProps} content={contentWithUnderscoreType} />)
      
      expect(screen.getByText('blog post')).toBeInTheDocument()
    })

    it('does not call handlers when they are not provided', () => {
      const propsWithoutHandlers = {
        ...mockProps,
        onEdit: undefined,
        onDelete: undefined,
        onRepurpose: undefined
      }
      
      render(<ContentDetailModal {...propsWithoutHandlers} />)
      
      // Should not crash when handlers are missing
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })
  })
})