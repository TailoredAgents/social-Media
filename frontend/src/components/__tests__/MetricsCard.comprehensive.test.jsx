import { render, screen } from '@testing-library/react'
import MetricsCard from '../MetricsCard'
import { UserIcon, HeartIcon } from '@heroicons/react/24/outline'

describe('MetricsCard Component', () => {
  const mockStatIncrease = {
    name: 'Total Followers',
    value: '12,345',
    change: '+12%',
    changeType: 'increase',
    icon: UserIcon
  }

  const mockStatDecrease = {
    name: 'Engagement Rate',
    value: '4.2%',
    change: '-2.1%',
    changeType: 'decrease',
    icon: HeartIcon
  }

  it('renders metric card with increase trend', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    expect(screen.getByText('Total Followers')).toBeInTheDocument()
    expect(screen.getByText('12,345')).toBeInTheDocument()
    expect(screen.getByText('+12%')).toBeInTheDocument()
    expect(screen.getByText('Increased by')).toBeInTheDocument()
  })

  it('renders metric card with decrease trend', () => {
    render(<MetricsCard stat={mockStatDecrease} />)
    
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument()
    expect(screen.getByText('4.2%')).toBeInTheDocument()
    expect(screen.getByText('-2.1%')).toBeInTheDocument()
    expect(screen.getByText('Decreased by')).toBeInTheDocument()
  })

  it('applies correct styling for increase trend', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    const changeElement = screen.getByText('+12%').parentElement
    expect(changeElement).toHaveClass('text-green-600')
    
    // Check for up arrow by looking for the specific class
    const arrowElement = document.querySelector('.text-green-500')
    expect(arrowElement).toBeInTheDocument()
  })

  it('applies correct styling for decrease trend', () => {
    render(<MetricsCard stat={mockStatDecrease} />)
    
    const changeElement = screen.getByText('-2.1%').parentElement
    expect(changeElement).toHaveClass('text-red-600')
    
    // Check for down arrow by looking for the specific class
    const arrowElement = document.querySelector('.text-red-500')
    expect(arrowElement).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    expect(screen.getByRole('article')).toHaveAttribute('aria-label', 'Total Followers metric')
    expect(screen.getByLabelText(/change: increased by \+12%/i)).toBeInTheDocument()
  })

  it('uses semantic HTML structure', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    expect(screen.getByRole('term')).toBeInTheDocument() // dt element
    expect(screen.getByRole('definition')).toBeInTheDocument() // dd element
  })

  it('renders icon when provided', () => {
    render(<MetricsCard stat={mockStatIncrease} />)
    
    // Icon should be rendered and have aria-hidden
    const iconContainer = document.querySelector('[aria-hidden="true"]')
    expect(iconContainer).toBeInTheDocument()
  })

  it('handles long metric names with truncation', () => {
    const longNameStat = {
      ...mockStatIncrease,
      name: 'This is a very long metric name that should be truncated'
    }
    
    render(<MetricsCard stat={longNameStat} />)
    
    const nameElement = screen.getByText(longNameStat.name)
    expect(nameElement).toHaveClass('truncate')
  })

  it('renders without icon gracefully', () => {
    const statWithoutIcon = {
      name: 'Test Metric',
      value: '100',
      change: '+5%',
      changeType: 'increase',
      icon: () => null // Provide a mock icon function
    }
    
    render(<MetricsCard stat={statWithoutIcon} />)
    expect(screen.getByText('Test Metric')).toBeInTheDocument()
  })

  it('handles zero or empty values', () => {
    const zeroStat = {
      name: 'Zero Metric',
      value: '0',
      change: '0%',
      changeType: 'increase',
      icon: UserIcon
    }
    
    render(<MetricsCard stat={zeroStat} />)
    
    expect(screen.getByText('Zero Metric')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('maintains component structure across different data', () => {
    const customStat = {
      name: 'Custom Metric',
      value: '999.99K',
      change: '+15.3%',
      changeType: 'increase',
      icon: HeartIcon
    }
    
    render(<MetricsCard stat={customStat} />)
    
    // Should maintain all expected elements
    expect(screen.getByRole('article')).toBeInTheDocument()
    expect(screen.getByRole('term')).toBeInTheDocument()
    expect(screen.getByRole('definition')).toBeInTheDocument()
    expect(screen.getByText('Custom Metric')).toBeInTheDocument()
    expect(screen.getByText('999.99K')).toBeInTheDocument()
    expect(screen.getByText('+15.3%')).toBeInTheDocument()
  })

  describe('Component Memoization', () => {
    it('component is memoized for performance', () => {
      // Check if component is wrapped with React.memo
      expect(MetricsCard.$$typeof).toBeDefined()
    })
  })

  describe('Edge Cases', () => {
    it('handles missing change type gracefully', () => {
      const statWithoutChangeType = {
        name: 'Test Metric',
        value: '100',
        change: '+5%',
        icon: UserIcon
      }
      
      expect(() => render(<MetricsCard stat={statWithoutChangeType} />)).not.toThrow()
    })

    it('handles special characters in values', () => {
      const specialCharStat = {
        name: 'Special Metric',
        value: '$1,234.56',
        change: '±2.5%',
        changeType: 'increase',
        icon: UserIcon
      }
      
      render(<MetricsCard stat={specialCharStat} />)
      
      expect(screen.getByText('$1,234.56')).toBeInTheDocument()
      expect(screen.getByText('±2.5%')).toBeInTheDocument()
    })
  })
})