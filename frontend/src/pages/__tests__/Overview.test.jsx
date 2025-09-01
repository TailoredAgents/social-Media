import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Overview from '../Overview'

// Mock the hooks
const mockEnhancedApi = {
  connectionStatus: 'connected',
  makeEnhancedRequest: jest.fn()
}

const mockRealTimeData = {
  data: {
    total_posts: 145,
    engagement_rate: 4.2,
    followers: 2850,
    content_scheduled: 12
  },
  isLoading: false,
  error: null
}

jest.mock('../../hooks/useEnhancedApi', () => ({
  useEnhancedApi: () => mockEnhancedApi
}))

jest.mock('../../hooks/useRealTimeData', () => ({
  useRealTimeData: () => mockRealTimeData
}))

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }) => (
    <div data-testid="line-chart">
      Chart: {data.datasets[0].label}
    </div>
  ),
  Bar: ({ data, options }) => (
    <div data-testid="bar-chart">
      Chart: {data.datasets[0].label}
    </div>
  ),
  Doughnut: ({ data, options }) => (
    <div data-testid="doughnut-chart">
      Chart: {data.labels[0]}
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
  ArcElement: {}
}))

// Mock MetricsCard component
jest.mock('../../components/MetricsCard', () => {
  return function MockMetricsCard({ title, value, change, trend, icon }) {
    return (
      <div data-testid="metrics-card">
        <div data-testid="metrics-title">{title}</div>
        <div data-testid="metrics-value">{value}</div>
        <div data-testid="metrics-change">{change}</div>
        <div data-testid="metrics-trend">{trend}</div>
      </div>
    )
  }
})

// Mock RecentActivity component
jest.mock('../../components/RecentActivity', () => {
  return function MockRecentActivity() {
    return <div data-testid="recent-activity">Recent Activity</div>
  }
})

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithQueryClient = (component) => {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('Overview Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the page title and description', () => {
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument()
    expect(screen.getByText(/Real-time insights/)).toBeInTheDocument()
  })

  it('displays metrics cards with real-time data', () => {
    renderWithQueryClient(<Overview />)
    
    const metricsCards = screen.getAllByTestId('metrics-card')
    expect(metricsCards).toHaveLength(4) // Total Posts, Engagement Rate, Followers, Scheduled
    
    expect(screen.getByTestId('metrics-value')).toHaveTextContent('145')
  })

  it('shows loading state when data is loading', () => {
    jest.mocked(require('../../hooks/useRealTimeData').useRealTimeData).mockReturnValue({
      data: null,
      isLoading: true,
      error: null
    })
    
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByText(/Loading/)).toBeInTheDocument()
  })

  it('displays error state when data fetch fails', () => {
    jest.mocked(require('../../hooks/useRealTimeData').useRealTimeData).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('API Error')
    })
    
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByText(/Error loading dashboard data/)).toBeInTheDocument()
  })

  it('renders charts when data is available', () => {
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument()
  })

  it('displays recent activity component', () => {
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByTestId('recent-activity')).toBeInTheDocument()
  })

  it('shows connection status indicator', () => {
    renderWithQueryClient(<Overview />)
    
    // Should show connected status
    expect(screen.getByText(/Connected/)).toBeInTheDocument()
  })

  it('handles disconnected state', () => {
    jest.mocked(require('../../hooks/useEnhancedApi').useEnhancedApi).mockReturnValue({
      connectionStatus: 'disconnected',
      makeEnhancedRequest: jest.fn()
    })
    
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByText(/Disconnected/)).toBeInTheDocument()
  })

  it('updates data in real-time', async () => {
    const { rerender } = renderWithQueryClient(<Overview />)
    
    expect(screen.getByTestId('metrics-value')).toHaveTextContent('145')
    
    // Simulate data update
    jest.mocked(require('../../hooks/useRealTimeData').useRealTimeData).mockReturnValue({
      data: {
        total_posts: 150,
        engagement_rate: 4.5,
        followers: 2900,
        content_scheduled: 15
      },
      isLoading: false,
      error: null
    })
    
    rerender(
      <QueryClientProvider client={createQueryClient()}>
        <Overview />
      </QueryClientProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByTestId('metrics-value')).toHaveTextContent('150')
    })
  })

  it('calculates trend changes correctly', () => {
    renderWithQueryClient(<Overview />)
    
    // Should show positive trends for growth metrics
    const trendElements = screen.getAllByTestId('metrics-trend')
    expect(trendElements.some(el => el.textContent === 'up')).toBe(true)
  })

  it('formats large numbers correctly', () => {
    jest.mocked(require('../../hooks/useRealTimeData').useRealTimeData).mockReturnValue({
      data: {
        total_posts: 1500,
        engagement_rate: 4.2,
        followers: 28500,
        content_scheduled: 12
      },
      isLoading: false,
      error: null
    })
    
    renderWithQueryClient(<Overview />)
    
    expect(screen.getByText('28.5K')).toBeInTheDocument() // Followers formatted
  })
})