import { render, screen } from '@testing-library/react'
import { ChartBarIcon } from '@heroicons/react/24/outline'
import MetricsCard from '../MetricsCard'

describe('MetricsCard Component', () => {
  const mockStatIncrease = {
    name: 'Total Posts',
    value: '142',
    change: '12%',
    changeType: 'increase',
    icon: ChartBarIcon
  }

  const mockStatDecrease = {
    name: 'Engagement Rate',
    value: '3.2%',
    change: '0.5%',
    changeType: 'decrease',
    icon: ChartBarIcon
  }

  it('renders stat data correctly', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    expect(screen.getByText('Total Posts')).toBeInTheDocument()
    expect(screen.getByText('142')).toBeInTheDocument()
    expect(screen.getByText('12%')).toBeInTheDocument()
  })

  it('shows increase arrow and green color for positive changes', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    // Find the container with the change styling
    const changeContainer = screen.getByText('12%').closest('.text-green-600')
    expect(changeContainer).toBeInTheDocument()
    
    // Check for screen reader text
    expect(screen.getByText('Increased by')).toBeInTheDocument()
  })

  it('shows decrease arrow and red color for negative changes', () => {
    render(<MetricsCard stat={mockStatDecrease} />)
    
    // Find the container with the change styling
    const changeContainer = screen.getByText('0.5%').closest('.text-red-600')
    expect(changeContainer).toBeInTheDocument()
    
    // Check for screen reader text
    expect(screen.getByText('Decreased by')).toBeInTheDocument()
  })

  it('renders the icon', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    // Check that the icon is rendered (it should have the correct CSS class)
    const iconElement = document.querySelector('.h-6.w-6.text-gray-400')
    expect(iconElement).toBeInTheDocument()
  })

  it('applies correct styling classes', () => {
    const { container } = render(<MetricsCard stat={mockStatIncrease} />)
    
    // Check main container styling
    const cardElement = container.querySelector('.bg-white.overflow-hidden.shadow.rounded-lg')
    expect(cardElement).toBeInTheDocument()
    
    // Check padding and layout classes
    const contentElement = container.querySelector('.p-5')
    expect(contentElement).toBeInTheDocument()
  })

  it('handles long stat names with truncation', () => {
    const longNameStat = {
      ...mockStatIncrease,
      name: 'This is a very long stat name that should be truncated'
    }
    
    render(<MetricsCard stat={longNameStat} />)
    
    const nameElement = screen.getByText(longNameStat.name)
    expect(nameElement).toHaveClass('truncate')
  })
})