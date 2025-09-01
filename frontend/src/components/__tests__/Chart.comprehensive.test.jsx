import { render, screen } from '@testing-library/react'
import Chart from '../Chart'

// Mock react-chartjs-2 components
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options, ...props }) => (
    <div data-testid="line-chart" data-options={JSON.stringify(options)} {...props}>
      Line Chart: {data.datasets[0]?.label || 'No label'}
    </div>
  ),
  Bar: ({ data, options, ...props }) => (
    <div data-testid="bar-chart" data-options={JSON.stringify(options)} {...props}>
      Bar Chart: {data.datasets[0]?.label || 'No label'}
    </div>
  ),
  Doughnut: ({ data, options, ...props }) => (
    <div data-testid="doughnut-chart" data-options={JSON.stringify(options)} {...props}>
      Doughnut Chart: {data.datasets[0]?.label || 'No label'}
    </div>
  )
}))

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: { register: jest.fn() },
  CategoryScale: {},
  LinearScale: {},
  PointElement: {},
  LineElement: {},
  BarElement: {},
  Title: {},
  Tooltip: {},
  Legend: {},
  ArcElement: {}
}))

describe('Chart Component', () => {
  const mockLineData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Followers',
        data: [100, 150, 200, 250, 300],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      }
    ]
  }

  const mockBarData = {
    labels: ['LinkedIn', 'Twitter', 'Instagram'],
    datasets: [
      {
        label: 'Engagement',
        data: [65, 59, 80],
        backgroundColor: ['#0077B5', '#1DA1F2', '#E4405F'],
      }
    ]
  }

  const mockDoughnutData = {
    labels: ['Direct', 'Social', 'Email', 'Other'],
    datasets: [
      {
        label: 'Traffic Sources',
        data: [300, 50, 100, 75],
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
      }
    ]
  }

  describe('Chart Types', () => {
    it('renders line chart by default', () => {
      render(<Chart data={mockLineData} />)
      
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByText('Line Chart: Followers')).toBeInTheDocument()
    })

    it('renders bar chart when type is specified', () => {
      render(<Chart data={mockBarData} type="bar" />)
      
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      expect(screen.getByText('Bar Chart: Engagement')).toBeInTheDocument()
    })

    it('renders doughnut chart when type is specified', () => {
      render(<Chart data={mockDoughnutData} type="doughnut" />)
      
      expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument()
      expect(screen.getByText('Doughnut Chart: Traffic Sources')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<Chart data={mockLineData} ariaLabel="Follower growth chart" />)
      
      const chartContainer = screen.getByRole('img')
      expect(chartContainer).toHaveAttribute('aria-label', 'Follower growth chart')
    })

    it('uses default ARIA label when none provided', () => {
      render(<Chart data={mockLineData} type="bar" />)
      
      const chartContainer = screen.getByRole('img')
      expect(chartContainer).toHaveAttribute('aria-label', 'bar chart')
    })

    it('renders accessible description when provided', () => {
      const description = 'This chart shows follower growth over the past 5 months'
      render(
        <Chart 
          data={mockLineData} 
          type="line"
          ariaDescription={description}
        />
      )
      
      expect(screen.getByText(description)).toBeInTheDocument()
      expect(screen.getByText(description)).toHaveClass('sr-only')
      
      const chartContainer = screen.getByRole('img')
      expect(chartContainer).toHaveAttribute('aria-describedby', 'chart-desc-line')
    })
  })

  describe('Styling and Layout', () => {
    it('applies default height class', () => {
      render(<Chart data={mockLineData} />)
      
      const chartContainer = screen.getByRole('img')
      expect(chartContainer).toHaveClass('relative', 'h-64')
    })

    it('applies custom className', () => {
      render(<Chart data={mockLineData} className="custom-chart-class" />)
      
      const chartContainer = screen.getByRole('img')
      expect(chartContainer).toHaveClass('custom-chart-class')
    })

    it('maintains relative positioning', () => {
      render(<Chart data={mockLineData} />)
      
      const chartContainer = screen.getByRole('img')
      expect(chartContainer).toHaveClass('relative')
    })
  })

  describe('Options Handling', () => {
    it('applies default options for line/bar charts', () => {
      render(<Chart data={mockLineData} type="line" />)
      
      const chart = screen.getByTestId('line-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.responsive).toBe(true)
      expect(options.maintainAspectRatio).toBe(false)
      expect(options.plugins.legend.position).toBe('top')
      expect(options.scales.y.beginAtZero).toBe(true)
    })

    it('applies doughnut-specific options', () => {
      render(<Chart data={mockDoughnutData} type="doughnut" />)
      
      const chart = screen.getByTestId('doughnut-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.responsive).toBe(true)
      expect(options.maintainAspectRatio).toBe(false)
      expect(options.plugins.legend.position).toBe('bottom')
    })

    it('merges custom options with defaults', () => {
      const customOptions = {
        plugins: {
          legend: {
            position: 'right'
          }
        }
      }
      
      render(<Chart data={mockLineData} options={customOptions} />)
      
      const chart = screen.getByTestId('line-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.plugins.legend.position).toBe('right')
      expect(options.responsive).toBe(true) // Default should still be there
    })

    it('enables tooltips by default', () => {
      render(<Chart data={mockLineData} />)
      
      const chart = screen.getByTestId('line-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.plugins.tooltip.enabled).toBe(true)
      expect(options.plugins.tooltip.intersect).toBe(false)
    })
  })

  describe('Data Handling', () => {
    it('passes data correctly to chart components', () => {
      render(<Chart data={mockLineData} />)
      
      expect(screen.getByText('Line Chart: Followers')).toBeInTheDocument()
    })

    it('handles datasets without labels', () => {
      const dataWithoutLabel = {
        labels: ['A', 'B', 'C'],
        datasets: [{ data: [1, 2, 3] }]
      }
      
      render(<Chart data={dataWithoutLabel} />)
      
      expect(screen.getByText('Line Chart: No label')).toBeInTheDocument()
    })
  })

  describe('Component Memoization', () => {
    it('component is memoized for performance', () => {
      // Check if component is wrapped with React.memo
      expect(Chart.$$typeof).toBeDefined()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty datasets gracefully', () => {
      const emptyData = {
        labels: [],
        datasets: []
      }
      
      expect(() => render(<Chart data={emptyData} />)).not.toThrow()
    })

    it('handles missing dataset properties', () => {
      const incompleteData = {
        labels: ['A', 'B'],
        datasets: [{}]
      }
      
      expect(() => render(<Chart data={incompleteData} />)).not.toThrow()
    })

    it('handles invalid chart type gracefully', () => {
      // Component should not render any chart for invalid types
      render(<Chart data={mockLineData} type="invalid" />)
      
      expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument()
      expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
      expect(screen.queryByTestId('doughnut-chart')).not.toBeInTheDocument()
    })
  })

  describe('Responsiveness', () => {
    it('sets responsive options correctly', () => {
      render(<Chart data={mockLineData} />)
      
      const chart = screen.getByTestId('line-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.responsive).toBe(true)
      expect(options.maintainAspectRatio).toBe(false)
    })
  })

  describe('Grid and Scale Configuration', () => {
    it('configures y-axis grid correctly', () => {
      render(<Chart data={mockLineData} />)
      
      const chart = screen.getByTestId('line-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.scales.y.grid.color).toBe('rgba(0, 0, 0, 0.05)')
      expect(options.scales.y.beginAtZero).toBe(true)
    })

    it('disables x-axis grid', () => {
      render(<Chart data={mockLineData} />)
      
      const chart = screen.getByTestId('line-chart')
      const options = JSON.parse(chart.getAttribute('data-options'))
      
      expect(options.scales.x.grid.display).toBe(false)
    })
  })
})