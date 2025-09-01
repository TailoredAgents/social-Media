import React from 'react'
import { render, screen } from '@testing-library/react'
import { 
  GoalProgressChart, 
  GoalCompletionChart, 
  ProgressTimelineChart 
} from '../ProgressChart'

// Mock Chart.js to avoid canvas issues in tests
jest.mock('react-chartjs-2', () => ({
  Line: jest.fn(({ data, options }) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Line Chart Mock
    </div>
  )),
  Doughnut: jest.fn(({ data, options }) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Doughnut Chart Mock
    </div>
  ))
}))

// Mock Chart.js register function
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn()
  },
  CategoryScale: {},
  LinearScale: {},
  PointElement: {},
  LineElement: {},
  Title: {},
  Tooltip: {},
  Legend: {},
  ArcElement: {}
}))

describe('GoalProgressChart', () => {
  const mockGoal = {
    id: 1,
    current_value: 75,
    target_value: 100,
    is_on_track: true
  }

  const mockOffTrackGoal = {
    id: 2,
    current_value: 25,
    target_value: 100,
    is_on_track: false
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<GoalProgressChart goal={mockGoal} />)
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  it('displays correct chart data for on-track goal', () => {
    render(<GoalProgressChart goal={mockGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    expect(chartData.labels).toEqual(['Start', 'Current', 'Target'])
    expect(chartData.datasets[0].data).toEqual([0, 75, 100])
    expect(chartData.datasets[0].borderColor).toBe('rgb(59, 130, 246)') // Blue for on-track
  })

  it('displays correct chart data for off-track goal', () => {
    render(<GoalProgressChart goal={mockOffTrackGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    expect(chartData.datasets[0].data).toEqual([0, 25, 100])
    expect(chartData.datasets[0].borderColor).toBe('rgb(245, 158, 11)') // Orange for off-track
  })

  it('has correct chart options configured', () => {
    render(<GoalProgressChart goal={mockGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartOptions = JSON.parse(chartElement.getAttribute('data-chart-options'))
    
    expect(chartOptions.responsive).toBe(true)
    expect(chartOptions.maintainAspectRatio).toBe(false)
    expect(chartOptions.plugins.legend.display).toBe(false)
    expect(chartOptions.scales.y.beginAtZero).toBe(true)
  })

  it('memoizes component correctly', () => {
    const { rerender } = render(<GoalProgressChart goal={mockGoal} />)
    const firstRender = screen.getByTestId('line-chart')
    
    // Re-render with same props
    rerender(<GoalProgressChart goal={mockGoal} />)
    const secondRender = screen.getByTestId('line-chart')
    
    expect(firstRender).toBe(secondRender)
  })
})

describe('GoalCompletionChart', () => {
  const mockGoals = [
    { id: 1, status: 'completed' },
    { id: 2, status: 'completed' },
    { id: 3, status: 'active' },
    { id: 4, status: 'paused' },
    { id: 5, status: 'failed' }
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<GoalCompletionChart goals={mockGoals} />)
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument()
  })

  it('calculates status counts correctly', () => {
    render(<GoalCompletionChart goals={mockGoals} />)
    const chartElement = screen.getByTestId('doughnut-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    expect(chartData.labels).toEqual(['Completed', 'Active', 'Paused', 'Failed'])
    expect(chartData.datasets[0].data).toEqual([2, 1, 1, 1]) // 2 completed, 1 active, 1 paused, 1 failed
  })

  it('handles empty goals array', () => {
    render(<GoalCompletionChart goals={[]} />)
    const chartElement = screen.getByTestId('doughnut-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    expect(chartData.datasets[0].data).toEqual([0, 0, 0, 0])
  })

  it('has correct colors for each status', () => {
    render(<GoalCompletionChart goals={mockGoals} />)
    const chartElement = screen.getByTestId('doughnut-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    expect(chartData.datasets[0].backgroundColor).toEqual([
      'rgb(34, 197, 94)',   // Green for completed
      'rgb(59, 130, 246)',  // Blue for active
      'rgb(245, 158, 11)',  // Yellow for paused
      'rgb(239, 68, 68)'    // Red for failed
    ])
  })

  it('has correct chart options', () => {
    render(<GoalCompletionChart goals={mockGoals} />)
    const chartElement = screen.getByTestId('doughnut-chart')
    const chartOptions = JSON.parse(chartElement.getAttribute('data-chart-options'))
    
    expect(chartOptions.responsive).toBe(true)
    expect(chartOptions.maintainAspectRatio).toBe(false)
    expect(chartOptions.plugins.legend.position).toBe('bottom')
  })
})

describe('ProgressTimelineChart', () => {
  const mockGoal = {
    id: 1,
    current_value: 75,
    target_value: 100,
    start_date: '2024-01-01',
    target_date: '2024-12-31',
    status: 'active',
    milestones: [
      {
        id: 1,
        percentage: 25,
        achieved_at: '2024-03-01'
      },
      {
        id: 2,
        percentage: 50,
        achieved_at: '2024-06-01'
      }
    ]
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock current date for consistent testing
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2024-09-01'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders without crashing', () => {
    render(<ProgressTimelineChart goal={mockGoal} />)
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  it('generates correct timeline data with milestones', () => {
    render(<ProgressTimelineChart goal={mockGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    // Should have milestone dates + 'Now' + projected date
    expect(chartData.labels.length).toBeGreaterThanOrEqual(4)
    expect(chartData.labels).toContain('Now')
    
    // Should have actual and projected datasets
    expect(chartData.datasets).toHaveLength(2)
    expect(chartData.datasets[0].label).toBe('Actual Progress')
    expect(chartData.datasets[1].label).toBe('Projected')
  })

  it('calculates milestone progress correctly', () => {
    render(<ProgressTimelineChart goal={mockGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    const actualData = chartData.datasets[0].data
    // First milestone: 25% of 100 = 25
    expect(actualData[0]).toBe(25)
    // Second milestone: 50% of 100 = 50
    expect(actualData[1]).toBe(50)
    // Current value
    expect(actualData[2]).toBe(75)
  })

  it('handles goal without milestones', () => {
    const goalWithoutMilestones = {
      ...mockGoal,
      milestones: []
    }
    
    render(<ProgressTimelineChart goal={goalWithoutMilestones} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    // Should still have 'Now' and projected date
    expect(chartData.labels).toHaveLength(2)
    expect(chartData.labels).toContain('Now')
  })

  it('handles inactive goal correctly', () => {
    const inactiveGoal = {
      ...mockGoal,
      status: 'completed'
    }
    
    render(<ProgressTimelineChart goal={inactiveGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    // Should not add projected completion for inactive goals
    const projectedData = chartData.datasets[1].data
    expect(projectedData.filter(d => d !== null)).toHaveLength(0)
  })

  it('has correct chart styling', () => {
    render(<ProgressTimelineChart goal={mockGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data'))
    
    // Check actual progress styling
    expect(chartData.datasets[0].borderColor).toBe('rgb(34, 197, 94)')
    expect(chartData.datasets[0].fill).toBe(false)
    
    // Check projected styling
    expect(chartData.datasets[1].borderColor).toBe('rgb(156, 163, 175)')
    expect(chartData.datasets[1].borderDash).toEqual([5, 5])
  })

  it('has correct chart options', () => {
    render(<ProgressTimelineChart goal={mockGoal} />)
    const chartElement = screen.getByTestId('line-chart')
    const chartOptions = JSON.parse(chartElement.getAttribute('data-chart-options'))
    
    expect(chartOptions.responsive).toBe(true)
    expect(chartOptions.maintainAspectRatio).toBe(false)
    expect(chartOptions.interaction.mode).toBe('index')
    expect(chartOptions.plugins.legend.position).toBe('top')
  })
})

// Integration tests
describe('Chart Components Integration', () => {
  it('all chart components render together without conflicts', () => {
    const mockGoal = {
      id: 1,
      current_value: 75,
      target_value: 100,
      is_on_track: true,
      start_date: '2024-01-01',
      target_date: '2024-12-31',
      status: 'active',
      milestones: []
    }
    
    const mockGoals = [mockGoal]
    
    render(
      <div>
        <GoalProgressChart goal={mockGoal} />
        <GoalCompletionChart goals={mockGoals} />
        <ProgressTimelineChart goal={mockGoal} />
      </div>
    )
    
    expect(screen.getAllByTestId('line-chart')).toHaveLength(2)
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument()
  })
  
  it('handles missing or undefined props gracefully', () => {
    // This should not crash the component
    expect(() => {
      render(<GoalProgressChart goal={{}} />)
    }).not.toThrow()
    
    expect(() => {
      render(<GoalCompletionChart goals={[]} />)
    }).not.toThrow()
  })
})