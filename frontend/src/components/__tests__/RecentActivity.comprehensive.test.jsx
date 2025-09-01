import { render, screen } from '@testing-library/react'
import RecentActivity from '../RecentActivity'

describe('RecentActivity Component', () => {
  it('renders recent activity heading', () => {
    render(<RecentActivity />)
    
    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Recent Activity')
  })

  it('renders all activity items', () => {
    render(<RecentActivity />)
    
    const expectedActivities = [
      'AI generated 3 new posts about industry trends',
      'LinkedIn post published: "The Future of AI in Marketing"',
      'Research agent analyzed 50+ trending topics',
      'Performance optimization recommendations generated',
      'Twitter thread scheduled for 3:00 PM'
    ]
    
    expectedActivities.forEach(activity => {
      expect(screen.getByText(activity)).toBeInTheDocument()
    })
  })

  it('displays correct timestamps for activities', () => {
    render(<RecentActivity />)
    
    const expectedTimes = [
      '2 minutes ago',
      '15 minutes ago',
      '1 hour ago', 
      '2 hours ago',
      '3 hours ago'
    ]
    
    expectedTimes.forEach(time => {
      expect(screen.getByText(time)).toBeInTheDocument()
    })
  })

  it('applies correct status colors for different activity types', () => {
    render(<RecentActivity />)
    
    // Check for success status (green)
    const successBadges = document.querySelectorAll('.bg-green-100.text-green-800')
    expect(successBadges).toHaveLength(2) // AI generated and LinkedIn post
    
    // Check for info status (blue)
    const infoBadges = document.querySelectorAll('.bg-blue-100.text-blue-800')
    expect(infoBadges).toHaveLength(2) // Research and optimization
    
    // Check for pending status (yellow)
    const pendingBadges = document.querySelectorAll('.bg-yellow-100.text-yellow-800')
    expect(pendingBadges).toHaveLength(1) // Scheduled post
  })

  it('displays status dots with correct colors', () => {
    render(<RecentActivity />)
    
    // Check for green dots (success)
    const greenDots = document.querySelectorAll('.bg-green-400')
    expect(greenDots).toHaveLength(2)
    
    // Check for blue dots (info)
    const blueDots = document.querySelectorAll('.bg-blue-400')
    expect(blueDots).toHaveLength(2)
    
    // Check for yellow dots (pending)
    const yellowDots = document.querySelectorAll('.bg-yellow-400')
    expect(yellowDots).toHaveLength(1)
  })

  it('has proper accessibility attributes', () => {
    render(<RecentActivity />)
    
    expect(screen.getByRole('region')).toHaveAttribute('aria-labelledby', 'recent-activity-heading')
    expect(screen.getByRole('list')).toHaveAttribute('aria-label', 'Recent activity items')
    
    // Check that all items are list items
    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(5)
  })

  it('renders status indicators with accessibility labels', () => {
    render(<RecentActivity />)
    
    // Check that status dots have proper aria-labels (multiple success items)
    expect(screen.getAllByLabelText('Status: success')).toHaveLength(2)
    expect(screen.getAllByLabelText('Status: info')).toHaveLength(2)
    expect(screen.getByLabelText('Status: pending')).toBeInTheDocument()
  })

  it('displays connecting lines between activities except for the last one', () => {
    render(<RecentActivity />)
    
    // Should have 4 connecting lines (5 items - 1)
    const connectingLines = document.querySelectorAll('.bg-gray-200[aria-hidden="true"]')
    expect(connectingLines).toHaveLength(4)
  })

  it('renders status badges with correct text', () => {
    render(<RecentActivity />)
    
    expect(screen.getAllByText('success')).toHaveLength(2)
    expect(screen.getAllByText('info')).toHaveLength(2)
    expect(screen.getByText('pending')).toBeInTheDocument()
  })

  it('uses semantic HTML structure', () => {
    render(<RecentActivity />)
    
    expect(screen.getByRole('region')).toBeInTheDocument()
    expect(screen.getByRole('list')).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(5)
  })

  it('maintains proper visual hierarchy with headings', () => {
    render(<RecentActivity />)
    
    const heading = screen.getByRole('heading', { level: 3 })
    expect(heading).toHaveAttribute('id', 'recent-activity-heading')
    expect(heading).toHaveClass('text-lg', 'leading-6', 'font-medium', 'text-gray-900')
  })

  describe('Component Memoization', () => {
    it('component is memoized for performance', () => {
      // Check if component is wrapped with React.memo
      expect(RecentActivity.$$typeof).toBeDefined()
    })
  })

  describe('Status Color Functions', () => {
    it('handles all status types correctly', () => {
      render(<RecentActivity />)
      
      // Test that the component handles different status types
      // This is implicitly tested by checking for different colored elements
      const allStatusElements = document.querySelectorAll('[class*="bg-"][class*="text-"]')
      expect(allStatusElements.length).toBeGreaterThan(0)
    })
  })

  describe('Activity Types', () => {
    const activityTypes = [
      'content_generated',
      'post_published', 
      'research_completed',
      'optimization',
      'post_scheduled'
    ]

    it('displays different types of activities', () => {
      render(<RecentActivity />)
      
      // Each activity type should be represented in the messages
      expect(screen.getByText(/AI generated/)).toBeInTheDocument()
      expect(screen.getByText(/LinkedIn post published/)).toBeInTheDocument()
      expect(screen.getByText(/Research agent analyzed/)).toBeInTheDocument()
      expect(screen.getByText(/Performance optimization/)).toBeInTheDocument()
      expect(screen.getByText(/Twitter thread scheduled/)).toBeInTheDocument()
    })
  })

  describe('Time Display', () => {
    it('shows relative time format consistently', () => {
      render(<RecentActivity />)
      
      // All time displays should follow the "X time ago" format
      const timeElements = screen.getAllByText(/ago$/)
      expect(timeElements).toHaveLength(5)
    })
  })

  describe('Layout and Styling', () => {
    it('applies correct CSS classes for layout', () => {
      render(<RecentActivity />)
      
      const container = screen.getByRole('region')
      expect(container).toHaveClass('bg-white', 'shadow', 'rounded-lg')
    })

    it('uses proper spacing and flow classes', () => {
      render(<RecentActivity />)
      
      const flowContainer = document.querySelector('.flow-root')
      expect(flowContainer).toBeInTheDocument()
      
      const list = screen.getByRole('list')
      expect(list).toHaveClass('-mb-8')
    })
  })
})