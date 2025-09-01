import { render, screen } from '@testing-library/react'
import RecentActivity from '../RecentActivity'

describe('RecentActivity Component', () => {
  it('renders the component title', () => {
    render(<RecentActivity />)
    
    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('renders all activity items', () => {
    render(<RecentActivity />)
    
    // Check that all predefined activities are rendered
    expect(screen.getByText(/AI generated 3 new posts about industry trends/)).toBeInTheDocument()
    expect(screen.getByText(/LinkedIn post published: "The Future of AI in Marketing"/)).toBeInTheDocument()
    expect(screen.getByText(/Research agent analyzed 50\+ trending topics/)).toBeInTheDocument()
    expect(screen.getByText(/Performance optimization recommendations generated/)).toBeInTheDocument()
    expect(screen.getByText(/Twitter thread scheduled for 3:00 PM/)).toBeInTheDocument()
  })

  it('displays correct timestamps', () => {
    render(<RecentActivity />)
    
    expect(screen.getByText('2 minutes ago')).toBeInTheDocument()
    expect(screen.getByText('15 minutes ago')).toBeInTheDocument()
    expect(screen.getByText('1 hour ago')).toBeInTheDocument()
    expect(screen.getByText('2 hours ago')).toBeInTheDocument()
    expect(screen.getByText('3 hours ago')).toBeInTheDocument()
  })

  it('displays correct status badges', () => {
    render(<RecentActivity />)
    
    // Check for status badges (should appear multiple times)
    const successBadges = screen.getAllByText('success')
    const infoBadges = screen.getAllByText('info')
    const pendingBadges = screen.getAllByText('pending')
    
    expect(successBadges).toHaveLength(2) // Two success activities
    expect(infoBadges).toHaveLength(2) // Two info activities
    expect(pendingBadges).toHaveLength(1) // One pending activity
  })

  it('applies correct status colors for badges', () => {
    render(<RecentActivity />)
    
    const successBadge = screen.getAllByText('success')[0]
    const infoBadge = screen.getAllByText('info')[0]
    const pendingBadge = screen.getByText('pending')
    
    expect(successBadge).toHaveClass('bg-green-100', 'text-green-800')
    expect(infoBadge).toHaveClass('bg-blue-100', 'text-blue-800')
    expect(pendingBadge).toHaveClass('bg-yellow-100', 'text-yellow-800')
  })

  it('applies correct status colors for dots', () => {
    render(<RecentActivity />)
    
    // Check that status dots have correct colors
    const statusDots = document.querySelectorAll('.h-3.w-3.rounded-full')
    
    // First two activities are success (green)
    expect(statusDots[0]).toHaveClass('bg-green-400')
    expect(statusDots[1]).toHaveClass('bg-green-400')
    
    // Next two are info (blue)
    expect(statusDots[2]).toHaveClass('bg-blue-400')
    expect(statusDots[3]).toHaveClass('bg-blue-400')
    
    // Last one is pending (yellow)
    expect(statusDots[4]).toHaveClass('bg-yellow-400')
  })

  it('renders clock icons for timestamps', () => {
    render(<RecentActivity />)
    
    // Should have 5 clock icons (one for each activity)
    const clockIcons = document.querySelectorAll('.h-4.w-4.text-gray-400')
    expect(clockIcons).toHaveLength(5)
  })

  it('shows connecting lines between activities', () => {
    render(<RecentActivity />)
    
    // Should have 4 connecting lines (between 5 activities)
    const connectingLines = document.querySelectorAll('.absolute.top-5.left-5.-ml-px.h-full.w-0\\.5.bg-gray-200')
    expect(connectingLines).toHaveLength(4)
  })

  it('applies correct styling structure', () => {
    const { container } = render(<RecentActivity />)
    
    // Check main container styling
    const mainContainer = container.querySelector('.bg-white.shadow.rounded-lg')
    expect(mainContainer).toBeInTheDocument()
    
    // Check inner padding structure
    const innerContainer = container.querySelector('.px-4.py-5.sm\\:p-6')
    expect(innerContainer).toBeInTheDocument()
    
    // Check flow layout
    const flowContainer = container.querySelector('.flow-root')
    expect(flowContainer).toBeInTheDocument()
  })

  it('handles different activity types', () => {
    render(<RecentActivity />)
    
    // Each activity should be in a list item
    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(5)
    
    // Each activity should have proper relative positioning
    listItems.forEach(item => {
      const activityContent = item.querySelector('.relative.pb-8')
      expect(activityContent).toBeInTheDocument()
    })
  })

  it('maintains proper accessibility structure', () => {
    render(<RecentActivity />)
    
    // Check that the list is properly structured
    const activityList = screen.getByRole('list')
    expect(activityList).toBeInTheDocument()
    
    // Check that decorative elements are properly hidden from screen readers
    const hiddenElements = document.querySelectorAll('[aria-hidden="true"]')
    expect(hiddenElements.length).toBeGreaterThan(0)
  })
})