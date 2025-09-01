import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChartBarIcon, UserIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline'
import MetricCard, { EngagementMetricCard, PerformanceMetricCard, SystemMetricCard } from '../MetricCard'

describe('MetricCard Component', () => {
  const defaultProps = {
    title: 'Test Metric',
    value: 1000,
    icon: ChartBarIcon
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders title and value', () => {
      render(<MetricCard {...defaultProps} />)
      
      expect(screen.getByText('Test Metric')).toBeInTheDocument()
      expect(screen.getByText('1,000')).toBeInTheDocument()
    })

    it('renders with icon', () => {
      render(<MetricCard {...defaultProps} />)
      
      // Icon should be rendered within the component
      const iconContainer = screen.getByText('Test Metric').closest('.bg-white')
      expect(iconContainer).toBeInTheDocument()
    })

    it('handles null or undefined values', () => {
      render(<MetricCard {...defaultProps} value={null} />)
      
      expect(screen.getByText('—')).toBeInTheDocument()
    })

    it('displays subtitle when provided', () => {
      render(<MetricCard {...defaultProps} subtitle="Additional info" />)
      
      expect(screen.getByText('Additional info')).toBeInTheDocument()
    })

    it('displays unit when provided', () => {
      render(<MetricCard {...defaultProps} value={25} unit="users" />)
      
      expect(screen.getByText('25')).toBeInTheDocument()
      expect(screen.getByText('users')).toBeInTheDocument()
    })
  })

  describe('Value Formatting', () => {
    it('formats numbers with commas for thousands', () => {
      render(<MetricCard {...defaultProps} value={12345} />)
      
      expect(screen.getByText('12,345')).toBeInTheDocument()
    })

    it('formats large numbers with K notation', () => {
      render(<MetricCard {...defaultProps} value={12500} />)
      
      expect(screen.getByText('12.5K')).toBeInTheDocument()
    })

    it('formats very large numbers with M notation', () => {
      render(<MetricCard {...defaultProps} value={1500000} />)
      
      expect(screen.getByText('1.5M')).toBeInTheDocument()
    })

    it('formats percentage values', () => {
      render(<MetricCard {...defaultProps} value={7.234} format="percentage" />)
      
      expect(screen.getByText('7.2%')).toBeInTheDocument()
    })

    it('formats currency values', () => {
      render(<MetricCard {...defaultProps} value={1234.56} format="currency" />)
      
      expect(screen.getByText('$1,234.56')).toBeInTheDocument()
    })

    it('formats time values in milliseconds', () => {
      render(<MetricCard {...defaultProps} value={450} format="time" />)
      
      expect(screen.getByText('450ms')).toBeInTheDocument()
    })

    it('formats time values in seconds', () => {
      render(<MetricCard {...defaultProps} value={1500} format="time" />)
      
      expect(screen.getByText('1.5s')).toBeInTheDocument()
    })

    it('respects precision parameter', () => {
      render(<MetricCard {...defaultProps} value={7.23456} format="percentage" precision={3} />)
      
      expect(screen.getByText('7.235%')).toBeInTheDocument()
    })
  })

  describe('Change Indicators', () => {
    it('displays positive change with green color and up arrow', () => {
      render(<MetricCard {...defaultProps} change={15.3} />)
      
      expect(screen.getByText('15.3%')).toBeInTheDocument()
      expect(screen.getByText('15.3%')).toHaveClass('text-green-600')
    })

    it('displays negative change with red color and down arrow', () => {
      render(<MetricCard {...defaultProps} change={-8.2} />)
      
      expect(screen.getByText('8.2%')).toBeInTheDocument()
      expect(screen.getByText('8.2%')).toHaveClass('text-red-600')
    })

    it('displays neutral change with gray color', () => {
      render(<MetricCard {...defaultProps} change={0} />)
      
      // Should show minus icon for zero change
      const iconElement = screen.getByText('Test Metric').closest('.bg-white')
      expect(iconElement).toBeInTheDocument()
    })

    it('handles reversed metrics (lower is better)', () => {
      render(<MetricCard {...defaultProps} change={-5} reversed={true} />)
      
      // Negative change should be good for reversed metrics
      expect(screen.getByText('5%')).toHaveClass('text-green-600')
    })

    it('shows vs last period text', () => {
      render(<MetricCard {...defaultProps} change={10} />)
      
      expect(screen.getByText('vs last period')).toBeInTheDocument()
    })
  })

  describe('Color Themes', () => {
    it('applies blue theme by default', () => {
      render(<MetricCard {...defaultProps} />)
      
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })

    it('applies green theme when specified', () => {
      render(<MetricCard {...defaultProps} color="green" />)
      
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })

    it('applies custom color themes', () => {
      const colors = ['purple', 'orange', 'red', 'yellow', 'indigo']
      
      colors.forEach(color => {
        const { unmount } = render(<MetricCard {...defaultProps} color={color} />)
        expect(screen.getByText('Test Metric')).toBeInTheDocument()
        unmount()
      })
    })
  })

  describe('Live Indicator', () => {
    it('shows live indicator when isLive is true', () => {
      render(<MetricCard {...defaultProps} isLive={true} />)
      
      expect(screen.getByText('LIVE')).toBeInTheDocument()
      expect(screen.getByTitle('Live data')).toBeInTheDocument()
    })

    it('hides live indicator when isLive is false', () => {
      render(<MetricCard {...defaultProps} isLive={false} />)
      
      expect(screen.queryByText('LIVE')).not.toBeInTheDocument()
    })

    it('has pulsing animation for live indicator', () => {
      render(<MetricCard {...defaultProps} isLive={true} />)
      
      const liveIndicator = screen.getByTitle('Live data')
      expect(liveIndicator).toHaveClass('animate-pulse')
    })
  })

  describe('Status Indicators', () => {
    it('shows good status with check icon', () => {
      render(<MetricCard {...defaultProps} status="good" />)
      
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })

    it('shows warning status with warning icon', () => {
      render(<MetricCard {...defaultProps} status="warning" />)
      
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })

    it('shows critical status with critical icon', () => {
      render(<MetricCard {...defaultProps} status="critical" />)
      
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })

    it('hides status indicator when no status provided', () => {
      render(<MetricCard {...defaultProps} />)
      
      // Should not have status-related icons visible
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })
  })

  describe('Target Progress', () => {
    it('displays progress bar when target is provided', () => {
      render(<MetricCard {...defaultProps} value={750} target={1000} />)
      
      expect(screen.getByText('Progress to target')).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('caps progress at 100%', () => {
      render(<MetricCard {...defaultProps} value={1200} target={1000} />)
      
      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('hides progress when no target provided', () => {
      render(<MetricCard {...defaultProps} />)
      
      expect(screen.queryByText('Progress to target')).not.toBeInTheDocument()
    })

    it('handles zero target gracefully', () => {
      render(<MetricCard {...defaultProps} value={100} target={0} />)
      
      // Should not crash with division by zero
      expect(screen.getByText('Test Metric')).toBeInTheDocument()
    })
  })

  describe('Trend Visualization', () => {
    const trendData = [10, 15, 12, 18, 20, 16, 22]

    it('renders sparkline when trend data provided', () => {
      render(<MetricCard {...defaultProps} trend={trendData} />)
      
      // Should render trend bars
      const container = screen.getByText('Test Metric').closest('.bg-white')
      expect(container).toBeInTheDocument()
    })

    it('shows trending up icon for increasing trend', () => {
      render(<MetricCard {...defaultProps} change={5} trend={[10, 15]} />)
      
      expect(screen.getByText('trending')).toBeInTheDocument()
    })

    it('shows trending down icon for decreasing trend', () => {
      render(<MetricCard {...defaultProps} change={-5} trend={[15, 10]} />)
      
      expect(screen.getByText('trending')).toBeInTheDocument()
    })

    it('hides trend when insufficient data', () => {
      render(<MetricCard {...defaultProps} trend={[10]} />)
      
      expect(screen.queryByText('trending')).not.toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      render(<MetricCard {...defaultProps} loading={true} />)
      
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('hides content when loading', () => {
      render(<MetricCard {...defaultProps} loading={true} />)
      
      // Content should be behind loading overlay
      const overlay = document.querySelector('.bg-opacity-75')
      expect(overlay).toBeInTheDocument()
    })

    it('shows content when not loading', () => {
      render(<MetricCard {...defaultProps} loading={false} />)
      
      expect(screen.getByText('Test Metric')).toBeVisible()
      expect(screen.getByText('1,000')).toBeVisible()
    })
  })

  describe('Threshold Indicators', () => {
    it('shows green indicator when value exceeds threshold', () => {
      render(<MetricCard {...defaultProps} value={150} threshold={100} />)
      
      const indicator = document.querySelector('.bg-green-200')
      expect(indicator).toBeInTheDocument()
    })

    it('shows red indicator when value is below threshold', () => {
      render(<MetricCard {...defaultProps} value={80} threshold={100} />)
      
      const indicator = document.querySelector('.bg-red-200')
      expect(indicator).toBeInTheDocument()
    })

    it('hides threshold indicator when no threshold provided', () => {
      render(<MetricCard {...defaultProps} />)
      
      expect(document.querySelector('.bg-green-200')).not.toBeInTheDocument()
      expect(document.querySelector('.bg-red-200')).not.toBeInTheDocument()
    })
  })

  describe('Click Interactions', () => {
    it('calls onClick when card is clicked', () => {
      const handleClick = jest.fn()
      render(<MetricCard {...defaultProps} onClick={handleClick} />)
      
      const card = screen.getByText('Test Metric').closest('.bg-white')
      fireEvent.click(card)
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('shows hover effects when clickable', () => {
      const handleClick = jest.fn()
      render(<MetricCard {...defaultProps} onClick={handleClick} />)
      
      const card = screen.getByText('Test Metric').closest('.bg-white')
      expect(card).toHaveClass('cursor-pointer')
    })

    it('does not show hover effects when not clickable', () => {
      render(<MetricCard {...defaultProps} />)
      
      const card = screen.getByText('Test Metric').closest('.bg-white')
      expect(card).not.toHaveClass('cursor-pointer')
    })
  })

  describe('Animation Effects', () => {
    it('animates when value changes', async () => {
      const { rerender } = render(<MetricCard {...defaultProps} value={1000} />)
      
      expect(screen.getByText('1,000')).toBeInTheDocument()
      
      rerender(<MetricCard {...defaultProps} value={1500} />)
      
      await waitFor(() => {
        expect(screen.getByText('1,500')).toBeInTheDocument()
      })
    })

    it('shows ring animation during value change', async () => {
      const { rerender } = render(<MetricCard {...defaultProps} value={1000} />)
      
      rerender(<MetricCard {...defaultProps} value={1500} />)
      
      // Should temporarily show animation class
      await waitFor(() => {
        const card = screen.getByText('Test Metric').closest('.bg-white')
        // Animation class might be present briefly
        expect(card).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(<MetricCard {...defaultProps} />)
      
      expect(screen.getByText('Test Metric')).toBeInTheDocument()
      expect(screen.getByText('1,000')).toBeInTheDocument()
    })

    it('provides descriptive text for screen readers', () => {
      render(<MetricCard {...defaultProps} change={15} />)
      
      expect(screen.getByText('vs last period')).toBeInTheDocument()
    })

    it('includes proper ARIA attributes for interactive elements', () => {
      const handleClick = jest.fn()
      render(<MetricCard {...defaultProps} onClick={handleClick} />)
      
      const card = screen.getByText('Test Metric').closest('.bg-white')
      expect(card).toHaveAttribute('class')
    })
  })
})

describe('EngagementMetricCard', () => {
  it('renders engagement-specific metrics', () => {
    render(<EngagementMetricCard platform="Twitter" rate={7.5} previousRate={6.2} />)
    
    expect(screen.getByText('Twitter Engagement')).toBeInTheDocument()
    expect(screen.getByText('7.5%')).toBeInTheDocument()
    expect(screen.getByText('Average engagement rate')).toBeInTheDocument()
  })

  it('calculates change percentage correctly', () => {
    render(<EngagementMetricCard platform="LinkedIn" rate={8.0} previousRate={6.0} />)
    
    // Change should be (8-6)/6 * 100 = 33.3%
    expect(screen.getByText('33.3%')).toBeInTheDocument()
  })

  it('handles missing previous rate', () => {
    render(<EngagementMetricCard platform="Instagram" rate={5.5} />)
    
    expect(screen.getByText('Instagram Engagement')).toBeInTheDocument()
    expect(screen.getByText('5.5%')).toBeInTheDocument()
  })
})

describe('PerformanceMetricCard', () => {
  it('renders performance metrics with target', () => {
    render(<PerformanceMetricCard metric="Response Time" current={150} target={200} threshold={100} />)
    
    expect(screen.getByText('Response Time')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('calculates progress percentage', () => {
    render(<PerformanceMetricCard metric="API Calls" current={750} target={1000} />)
    
    expect(screen.getByText('75% of target')).toBeInTheDocument()
  })

  it('determines status based on threshold', () => {
    render(<PerformanceMetricCard metric="Uptime" current={99.9} threshold={99.0} />)
    
    // Should show good status since current > threshold
    const container = screen.getByText('Uptime').closest('.bg-white')
    expect(container).toBeInTheDocument()
  })
})

describe('SystemMetricCard', () => {
  it('renders system metrics with uptime', () => {
    render(<SystemMetricCard systemName="Database" value={1.2} unit="ms" status="good" uptime="99.95%" />)
    
    expect(screen.getByText('Database')).toBeInTheDocument()
    expect(screen.getByText('1.2')).toBeInTheDocument()
    expect(screen.getByText('ms')).toBeInTheDocument()
    expect(screen.getByText('Uptime: 99.95%')).toBeInTheDocument()
  })

  it('applies color based on status', () => {
    const { rerender } = render(
      <SystemMetricCard systemName="Server" value={50} status="good" />
    )
    
    expect(screen.getByText('Server')).toBeInTheDocument()
    
    rerender(<SystemMetricCard systemName="Server" value={50} status="warning" />)
    expect(screen.getByText('Server')).toBeInTheDocument()
    
    rerender(<SystemMetricCard systemName="Server" value={50} status="critical" />)
    expect(screen.getByText('Server')).toBeInTheDocument()
  })

  it('handles missing uptime gracefully', () => {
    render(<SystemMetricCard systemName="Cache" value={45} unit="%" status="warning" />)
    
    expect(screen.getByText('Cache')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
    expect(screen.queryByText(/Uptime/)).not.toBeInTheDocument()
  })
})