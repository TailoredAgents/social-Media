import { render } from '@testing-library/react'
import Chart from '../Chart'

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Line Chart
    </div>
  ),
  Bar: ({ data, options }) => (
    <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Bar Chart
    </div>
  ),
  Doughnut: ({ data, options }) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Doughnut Chart
    </div>
  ),
}))

// Mock Chart.js registration
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn(),
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
}))

describe('Chart Component', () => {
  const mockData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Sales',
        data: [12, 19, 3, 5, 2],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
      },
    ],
  }

  it('renders line chart by default', () => {
    const { container } = render(<Chart data={mockData} />)
    
    const lineChart = container.querySelector('[data-testid="line-chart"]')
    expect(lineChart).toBeInTheDocument()
    expect(lineChart).toHaveTextContent('Line Chart')
  })

  it('renders bar chart when type is bar', () => {
    const { container } = render(<Chart data={mockData} type="bar" />)
    
    const barChart = container.querySelector('[data-testid="bar-chart"]')
    expect(barChart).toBeInTheDocument()
    expect(barChart).toHaveTextContent('Bar Chart')
  })

  it('renders doughnut chart when type is doughnut', () => {
    const { container } = render(<Chart data={mockData} type="doughnut" />)
    
    const doughnutChart = container.querySelector('[data-testid="doughnut-chart"]')
    expect(doughnutChart).toBeInTheDocument()
    expect(doughnutChart).toHaveTextContent('Doughnut Chart')
  })

  it('passes data to chart component', () => {
    const { container } = render(<Chart data={mockData} />)
    
    const lineChart = container.querySelector('[data-testid="line-chart"]')
    const chartData = JSON.parse(lineChart.getAttribute('data-chart-data'))
    
    expect(chartData).toEqual(mockData)
  })

  it('merges default options for line chart', () => {
    const { container } = render(<Chart data={mockData} />)
    
    const lineChart = container.querySelector('[data-testid="line-chart"]')
    const chartOptions = JSON.parse(lineChart.getAttribute('data-chart-options'))
    
    expect(chartOptions.responsive).toBe(true)
    expect(chartOptions.maintainAspectRatio).toBe(false)
    expect(chartOptions.plugins.legend.position).toBe('top')
    expect(chartOptions.scales.y.beginAtZero).toBe(true)
  })

  it('merges doughnut options for doughnut chart', () => {
    const { container } = render(<Chart data={mockData} type="doughnut" />)
    
    const doughnutChart = container.querySelector('[data-testid="doughnut-chart"]')
    const chartOptions = JSON.parse(doughnutChart.getAttribute('data-chart-options'))
    
    expect(chartOptions.responsive).toBe(true)
    expect(chartOptions.maintainAspectRatio).toBe(false)
    expect(chartOptions.plugins.legend.position).toBe('bottom')
    // Doughnut charts shouldn't have scales
    expect(chartOptions.scales).toBeUndefined()
  })

  it('merges custom options with defaults', () => {
    const customOptions = {
      plugins: {
        title: {
          display: true,
          text: 'Custom Chart Title',
        },
      },
    }

    const { container } = render(<Chart data={mockData} options={customOptions} />)
    
    const lineChart = container.querySelector('[data-testid="line-chart"]')
    const chartOptions = JSON.parse(lineChart.getAttribute('data-chart-options'))
    
    // Should have custom options
    expect(chartOptions.plugins.title?.display).toBe(true) // Custom
    expect(chartOptions.plugins.title?.text).toBe('Custom Chart Title') // Custom
    
    // Should maintain responsive settings
    expect(chartOptions.responsive).toBe(true)
    expect(chartOptions.maintainAspectRatio).toBe(false)
  })

  it('applies default container styling', () => {
    const { container } = render(<Chart data={mockData} />)
    
    const chartContainer = container.querySelector('.relative.h-64')
    expect(chartContainer).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const customClassName = 'custom-chart-class'
    const { container } = render(<Chart data={mockData} className={customClassName} />)
    
    const chartContainer = container.querySelector(`.relative.h-64.${customClassName}`)
    expect(chartContainer).toBeInTheDocument()
  })

  it('renders only the specified chart type', () => {
    const { container } = render(<Chart data={mockData} type="bar" />)
    
    // Should have bar chart
    expect(container.querySelector('[data-testid="bar-chart"]')).toBeInTheDocument()
    
    // Should not have other chart types
    expect(container.querySelector('[data-testid="line-chart"]')).not.toBeInTheDocument()
    expect(container.querySelector('[data-testid="doughnut-chart"]')).not.toBeInTheDocument()
  })

  it('handles empty data gracefully', () => {
    const emptyData = {
      labels: [],
      datasets: [],
    }

    const { container } = render(<Chart data={emptyData} />)
    
    const lineChart = container.querySelector('[data-testid="line-chart"]')
    expect(lineChart).toBeInTheDocument()
    
    const chartData = JSON.parse(lineChart.getAttribute('data-chart-data'))
    expect(chartData.labels).toEqual([])
    expect(chartData.datasets).toEqual([])
  })

  it('preserves data structure integrity', () => {
    const complexData = {
      labels: ['Q1', 'Q2', 'Q3', 'Q4'],
      datasets: [
        {
          label: 'Revenue',
          data: [10000, 15000, 12000, 18000],
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
          borderWidth: 2,
        },
        {
          label: 'Expenses',
          data: [8000, 11000, 9000, 13000],
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
        },
      ],
    }

    const { container } = render(<Chart data={complexData} />)
    
    const lineChart = container.querySelector('[data-testid="line-chart"]')
    const chartData = JSON.parse(lineChart.getAttribute('data-chart-data'))
    
    expect(chartData).toEqual(complexData)
    expect(chartData.datasets).toHaveLength(2)
    expect(chartData.datasets[0].label).toBe('Revenue')
    expect(chartData.datasets[1].label).toBe('Expenses')
  })
})