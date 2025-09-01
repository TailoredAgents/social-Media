import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import LiveChart, { LiveMetricsChart, LiveEngagementChart, LivePerformanceRadar } from '../LiveChart'

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Line Chart
    </div>
  ),
  Bar: ({ data }) => (
    <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)}>
      Bar Chart
    </div>
  ),
  Doughnut: ({ data }) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)}>
      Doughnut Chart
    </div>
  ),
  Radar: ({ data }) => (
    <div data-testid="radar-chart" data-chart-data={JSON.stringify(data)}>
      Radar Chart
    </div>
  )
}))

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn()
  },
  CategoryScale: {},
  LinearScale: {},
  PointElement: {},
  LineElement: {},
  BarElement: {},
  Title: {},
  Tooltip: {},
  Legend: {},
  ArcElement: {},
  RadialLinearScale: {},
  Filler: {}
}))

describe('LiveChart Component', () => {
  const mockData = {
    labels: ['10:00', '10:05', '10:10', '10:15'],
    datasets: [{
      label: 'Views',
      data: [100, 120, 110, 130],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)'
    }]
  }

  const defaultProps = {
    title: 'Test Chart',
    data: mockData,
    type: 'line'
  }

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Basic Rendering', () => {
    it('renders chart title', () => {
      render(<LiveChart {...defaultProps} />)
      
      expect(screen.getByText('Test Chart')).toBeInTheDocument()
    })

    it('renders line chart by default', () => {
      render(<LiveChart {...defaultProps} />)
      
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('renders different chart types', () => {
      const types = ['line', 'bar', 'doughnut', 'radar']
      
      types.forEach(type => {
        const { unmount } = render(<LiveChart {...defaultProps} type={type} />)
        expect(screen.getByTestId(`${type}-chart`)).toBeInTheDocument()
        unmount()
      })
    })

    it('displays live indicator when auto-updating', () => {
      render(<LiveChart {...defaultProps} autoUpdate={true} />)
      
      expect(screen.getByText('LIVE')).toBeInTheDocument()
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('Chart Controls', () => {
    it('shows play/pause button when controls enabled', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      expect(screen.getByTitle(/Pause updates|Resume updates/)).toBeInTheDocument()
    })

    it('toggles play/pause state', () => {
      render(<LiveChart {...defaultProps} showControls={true} autoUpdate={true} />)
      
      const playPauseButton = screen.getByTitle('Pause updates')
      fireEvent.click(playPauseButton)
      
      expect(screen.getByTitle('Resume updates')).toBeInTheDocument()
      expect(screen.queryByText('LIVE')).not.toBeInTheDocument()
    })

    it('shows fullscreen toggle button', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      expect(screen.getByTitle('Enter fullscreen')).toBeInTheDocument()
    })

    it('toggles fullscreen mode', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      const fullscreenButton = screen.getByTitle('Enter fullscreen')
      fireEvent.click(fullscreenButton)
      
      expect(screen.getByTitle('Exit fullscreen')).toBeInTheDocument()
    })

    it('shows settings button', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      expect(screen.getByTitle('Chart settings')).toBeInTheDocument()
    })

    it('toggles settings panel', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      const settingsButton = screen.getByTitle('Chart settings')
      fireEvent.click(settingsButton)
      
      expect(screen.getByText('Update Interval')).toBeInTheDocument()
      expect(screen.getByText('Max Data Points')).toBeInTheDocument()
    })
  })

  describe('Chart Type Selector', () => {
    it('shows type selector when enabled', () => {
      render(<LiveChart {...defaultProps} showControls={true} showTypeSelector={true} />)
      
      const selector = screen.getByDisplayValue('Line Chart')
      expect(selector).toBeInTheDocument()
    })

    it('changes chart type when selector is used', () => {
      render(<LiveChart {...defaultProps} showControls={true} showTypeSelector={true} />)
      
      const selector = screen.getByDisplayValue('Line Chart')
      fireEvent.change(selector, { target: { value: 'bar' } })
      
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('hides type selector by default', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      expect(screen.queryByDisplayValue('Line Chart')).not.toBeInTheDocument()
    })
  })

  describe('Settings Panel', () => {
    beforeEach(() => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      fireEvent.click(screen.getByTitle('Chart settings'))
    })

    it('shows update interval options', () => {
      expect(screen.getByText('1 second')).toBeInTheDocument()
      expect(screen.getByText('5 seconds')).toBeInTheDocument()
      expect(screen.getByText('10 seconds')).toBeInTheDocument()
      expect(screen.getByText('30 seconds')).toBeInTheDocument()
    })

    it('shows max data points options', () => {
      expect(screen.getByText('10 points')).toBeInTheDocument()
      expect(screen.getByText('20 points')).toBeInTheDocument()
      expect(screen.getByText('50 points')).toBeInTheDocument()
      expect(screen.getByText('100 points')).toBeInTheDocument()
    })

    it('shows reset data button', () => {
      expect(screen.getByText('Reset Data')).toBeInTheDocument()
    })

    it('shows export button', () => {
      expect(screen.getByText('Export PNG')).toBeInTheDocument()
    })
  })

  describe('Data Updates', () => {
    it('auto-updates data when playing', async () => {
      const onDataUpdate = jest.fn()
      render(
        <LiveChart 
          {...defaultProps} 
          autoUpdate={true} 
          updateInterval={1000}
          onDataUpdate={onDataUpdate}
        />
      )

      act(() => {
        jest.advanceTimersByTime(1000)
      })

      await waitFor(() => {
        expect(onDataUpdate).toHaveBeenCalled()
      })
    })

    it('stops updates when paused', async () => {
      const onDataUpdate = jest.fn()
      render(
        <LiveChart 
          {...defaultProps} 
          autoUpdate={false}
          updateInterval={1000}
          onDataUpdate={onDataUpdate}
        />
      )

      act(() => {
        jest.advanceTimersByTime(2000)
      })

      expect(onDataUpdate).not.toHaveBeenCalled()
    })

    it('maintains max data points limit', async () => {
      render(
        <LiveChart 
          {...defaultProps} 
          autoUpdate={true} 
          updateInterval={100}
          maxDataPoints={3}
        />
      )

      // Fast forward to generate several data points
      act(() => {
        jest.advanceTimersByTime(1000)
      })

      const chartElement = screen.getByTestId('line-chart')
      const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
      
      // Should not exceed maxDataPoints
      expect(chartData.datasets[0].data.length).toBeLessThanOrEqual(3)
    })

    it('updates labels with timestamps', async () => {
      render(
        <LiveChart 
          {...defaultProps} 
          autoUpdate={true} 
          updateInterval={100}
        />
      )

      act(() => {
        jest.advanceTimersByTime(200)
      })

      const chartElement = screen.getByTestId('line-chart')
      const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
      
      // Should have timestamp labels
      expect(chartData.labels.length).toBeGreaterThan(mockData.labels.length)
    })
  })

  describe('Chart Footer', () => {
    it('displays last updated time', () => {
      render(<LiveChart {...defaultProps} />)
      
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })

    it('displays data points count', () => {
      render(<LiveChart {...defaultProps} />)
      
      expect(screen.getByText('4 data points')).toBeInTheDocument()
    })

    it('displays auto-update status', () => {
      render(<LiveChart {...defaultProps} autoUpdate={true} />)
      
      expect(screen.getByText('Auto-update: ON')).toBeInTheDocument()
    })

    it('displays update interval', () => {
      render(<LiveChart {...defaultProps} updateInterval={10000} />)
      
      expect(screen.getByText('Interval: 10s')).toBeInTheDocument()
    })
  })

  describe('Chart Options', () => {
    it('applies custom height', () => {
      render(<LiveChart {...defaultProps} height={400} />)
      
      const container = document.querySelector('[style*="height: 400px"]')
      expect(container).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(<LiveChart {...defaultProps} className="custom-class" />)
      
      const container = document.querySelector('.custom-class')
      expect(container).toBeInTheDocument()
    })

    it('merges custom options with defaults', () => {
      const customOptions = {
        plugins: {
          legend: {
            display: false
          }
        }
      }
      
      render(<LiveChart {...defaultProps} options={customOptions} />)
      
      const chartElement = screen.getByTestId('line-chart')
      const chartOptions = JSON.parse(chartElement.getAttribute('data-chart-options'))
      
      expect(chartOptions.plugins.legend.display).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('handles missing data gracefully', () => {
      render(<LiveChart title="Test" data={null} />)
      
      expect(screen.getByText('Test')).toBeInTheDocument()
    })

    it('handles empty datasets', () => {
      const emptyData = { labels: [], datasets: [] }
      render(<LiveChart {...defaultProps} data={emptyData} />)
      
      expect(screen.getByText('0 data points')).toBeInTheDocument()
    })

    it('handles invalid chart type', () => {
      render(<LiveChart {...defaultProps} type="invalid" />)
      
      // Should fall back to line chart
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper button labels', () => {
      render(<LiveChart {...defaultProps} showControls={true} />)
      
      expect(screen.getByTitle('Chart settings')).toBeInTheDocument()
      expect(screen.getByTitle('Pause updates')).toBeInTheDocument()
      expect(screen.getByTitle('Enter fullscreen')).toBeInTheDocument()
    })

    it('provides semantic structure', () => {
      render(<LiveChart {...defaultProps} />)
      
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument()
    })
  })
})

describe('LiveMetricsChart', () => {
  const mockMetrics = {
    labels: ['12:00', '12:30', '13:00'],
    datasets: [{
      label: 'Page Views',
      data: [1000, 1200, 1100]
    }]
  }

  it('renders with metrics data', () => {
    render(<LiveMetricsChart metrics={mockMetrics} />)
    
    expect(screen.getByText('Live Metrics')).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  it('handles missing metrics data', () => {
    render(<LiveMetricsChart />)
    
    expect(screen.getByText('Live Metrics')).toBeInTheDocument()
  })
})

describe('LiveEngagementChart', () => {
  const mockPlatforms = [
    { name: 'Twitter', engagement: 7.5, color: '#1DA1F2' },
    { name: 'LinkedIn', engagement: 5.2, color: '#0077B5' }
  ]

  it('renders engagement data as bar chart', () => {
    render(<LiveEngagementChart platforms={mockPlatforms} />)
    
    expect(screen.getByText('Live Platform Engagement')).toBeInTheDocument()
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('handles missing platform data', () => {
    render(<LiveEngagementChart />)
    
    expect(screen.getByText('Live Platform Engagement')).toBeInTheDocument()
  })
})

describe('LivePerformanceRadar', () => {
  const mockPerformanceData = [8, 6, 7, 9, 5]

  it('renders performance data as radar chart', () => {
    render(<LivePerformanceRadar performanceData={mockPerformanceData} />)
    
    expect(screen.getByText('Performance Radar')).toBeInTheDocument()
    expect(screen.getByTestId('radar-chart')).toBeInTheDocument()
  })

  it('handles missing performance data', () => {
    render(<LivePerformanceRadar />)
    
    expect(screen.getByText('Performance Radar')).toBeInTheDocument()
  })

  it('uses default performance values when none provided', () => {
    render(<LivePerformanceRadar />)
    
    const chartElement = screen.getByTestId('radar-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    expect(chartData.datasets[0].data).toEqual([0, 0, 0, 0, 0])
  })
})