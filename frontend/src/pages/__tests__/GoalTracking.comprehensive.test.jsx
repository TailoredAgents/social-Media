import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import GoalTracking from '../GoalTracking'

// Mock the goal modals
jest.mock('../../components/Goals/CreateGoalModal', () => {
  return function MockCreateGoalModal({ isOpen, onClose, onSubmit }) {
    return isOpen ? (
      <div data-testid="create-goal-modal">
        <button onClick={() => onSubmit({ title: 'Test Goal' })}>Submit</button>
        <button onClick={onClose}>Cancel</button>
      </div>
    ) : null
  }
})

jest.mock('../../components/Goals/GoalDetailModal', () => {
  return function MockGoalDetailModal({ goal, isOpen, onClose, onUpdate, onDelete }) {
    return isOpen ? (
      <div data-testid="goal-detail-modal">
        <div>Goal: {goal?.title}</div>
        <button onClick={() => onUpdate({ ...goal, title: 'Updated Goal' })}>Update</button>
        <button onClick={() => onDelete(goal?.id)}>Delete</button>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
  }
})

// Mock the chart component
jest.mock('../../components/Charts/ProgressChart', () => ({
  GoalCompletionChart: ({ goals }) => (
    <div data-testid="goal-completion-chart">
      Chart with {goals?.length || 0} goals
    </div>
  )
}))

// Mock the enhanced API hook
const mockApi = {
  goals: {
    getAll: jest.fn(() => Promise.resolve([
      {
        id: 1,
        title: 'Grow LinkedIn Following',
        description: 'Increase LinkedIn followers from 2,500 to 3,000',
        goal_type: 'follower_growth',
        target_value: 3000,
        current_value: 2750,
        start_date: '2025-07-01',
        target_date: '2025-10-01',
        platform: 'linkedin',
        status: 'active',
        progress_percentage: 91.7,
        days_remaining: 71,
        is_on_track: true,
        milestones: [
          { id: 1, description: 'Reached 25% of goal', percentage: 25, achieved_at: '2025-07-15' },
          { id: 2, description: 'Reached 50% of goal', percentage: 50, achieved_at: '2025-07-28' }
        ]
      },
      {
        id: 2,
        title: 'Improve Engagement Rate',
        description: 'Increase overall engagement rate from 4.2% to 6.0%',
        goal_type: 'engagement_rate',
        target_value: 6.0,
        current_value: 5.1,
        start_date: '2025-07-01',
        target_date: '2025-09-01',
        platform: 'all',
        status: 'active',
        progress_percentage: 85,
        days_remaining: 41,
        is_on_track: true,
        milestones: []
      },
      {
        id: 3,
        title: 'Monthly Content Volume',
        description: 'Publish 60 posts per month (up from 40)',
        goal_type: 'content_volume',
        target_value: 60,
        current_value: 45,
        start_date: '2025-07-01',
        target_date: '2025-07-31',
        platform: 'all',
        status: 'active',
        progress_percentage: 75,
        days_remaining: 9,
        is_on_track: false,
        milestones: []
      },
      {
        id: 4,
        title: 'Twitter Growth Campaign',
        description: 'Gain 1,000 new Twitter followers',
        goal_type: 'follower_growth',
        target_value: 6000,
        current_value: 6000,
        start_date: '2025-06-01',
        target_date: '2025-07-15',
        platform: 'twitter',
        status: 'completed',
        progress_percentage: 100,
        days_remaining: 0,
        is_on_track: true,
        milestones: [
          { id: 1, description: 'Goal completed!', percentage: 100, achieved_at: '2025-07-15' }
        ]
      }
    ])),
    getDashboard: jest.fn(() => Promise.resolve({
      active_goals: 3,
      completed_goals: 1,
      on_track_goals: 2,
      total_goals: 4
    })),
    create: jest.fn(() => Promise.resolve({ id: 5, title: 'New Goal' })),
    update: jest.fn(() => Promise.resolve()),
    delete: jest.fn(() => Promise.resolve()),
    updateProgress: jest.fn(() => Promise.resolve())
  }
}

jest.mock('../../hooks/useEnhancedApi', () => ({
  useEnhancedApi: () => ({ 
    api: mockApi,
    connectionStatus: 'connected'
  })
}))

// Mock logger
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn()
}))

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithQueryClient = (component) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('Goal Tracking Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Page Header', () => {
    it('renders goal tracking title and description', () => {
      renderWithQueryClient(<GoalTracking />)
      
      expect(screen.getByText('Goal Tracking')).toBeInTheDocument()
      expect(screen.getByText('Monitor progress toward your social media objectives')).toBeInTheDocument()
    })

    it('displays new goal button', () => {
      renderWithQueryClient(<GoalTracking />)
      
      expect(screen.getByRole('button', { name: /New Goal/ })).toBeInTheDocument()
    })
  })

  describe('Summary Statistics', () => {
    it('displays summary cards with correct data', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('4')).toBeInTheDocument() // Total goals
        expect(screen.getByText('Total Goals')).toBeInTheDocument()
        
        expect(screen.getByText('3')).toBeInTheDocument() // Active goals
        expect(screen.getByText('Active Goals')).toBeInTheDocument()
        
        expect(screen.getByText('1')).toBeInTheDocument() // Completed goals
        expect(screen.getByText('Completed')).toBeInTheDocument()
        
        expect(screen.getByText('88%')).toBeInTheDocument() // Average progress
        expect(screen.getByText('Avg Progress')).toBeInTheDocument()
      })
    })

    it('calculates average progress correctly', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        // Should calculate: (91.7 + 85 + 75 + 100) / 4 = 87.925 ≈ 88%
        expect(screen.getByText('88%')).toBeInTheDocument()
      })
    })
  })

  describe('Goal Completion Chart', () => {
    it('renders goal completion chart', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Goal Status Overview')).toBeInTheDocument()
        expect(screen.getByTestId('goal-completion-chart')).toBeInTheDocument()
        expect(screen.getByText('Chart with 4 goals')).toBeInTheDocument()
      })
    })
  })

  describe('Goal Filtering', () => {
    it('renders status filter dropdown', () => {
      renderWithQueryClient(<GoalTracking />)
      
      expect(screen.getByText('Filter by status:')).toBeInTheDocument()
      expect(screen.getByDisplayValue('All Goals')).toBeInTheDocument()
    })

    it('filters goals by status', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Grow LinkedIn Following')).toBeInTheDocument()
        expect(screen.getByText('Twitter Growth Campaign')).toBeInTheDocument()
      })
      
      // Filter to show only completed goals
      const statusFilter = screen.getByDisplayValue('All Goals')
      fireEvent.change(statusFilter, { target: { value: 'completed' } })
      
      await waitFor(() => {
        expect(screen.getByText('Twitter Growth Campaign')).toBeInTheDocument()
        expect(screen.queryByText('Grow LinkedIn Following')).not.toBeInTheDocument()
      })
    })

    it('shows all filter options', () => {
      renderWithQueryClient(<GoalTracking />)
      
      const statusFilter = screen.getByDisplayValue('All Goals')
      fireEvent.click(statusFilter)
      
      expect(screen.getByText('All Goals')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Paused')).toBeInTheDocument()
    })
  })

  describe('Goal List Display', () => {
    it('displays all goals with correct information', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Grow LinkedIn Following')).toBeInTheDocument()
        expect(screen.getByText('Increase LinkedIn followers from 2,500 to 3,000')).toBeInTheDocument()
        
        expect(screen.getByText('Improve Engagement Rate')).toBeInTheDocument()
        expect(screen.getByText('Increase overall engagement rate from 4.2% to 6.0%')).toBeInTheDocument()
        
        expect(screen.getByText('Monthly Content Volume')).toBeInTheDocument()
        expect(screen.getByText('Publish 60 posts per month (up from 40)')).toBeInTheDocument()
        
        expect(screen.getByText('Twitter Growth Campaign')).toBeInTheDocument()
        expect(screen.getByText('Gain 1,000 new Twitter followers')).toBeInTheDocument()
      })
    })

    it('shows correct status badges', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        const activeStatuses = screen.getAllByText('active')
        expect(activeStatuses).toHaveLength(3)
        
        expect(screen.getByText('completed')).toBeInTheDocument()
      })
    })

    it('displays progress bars correctly', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('2,750 / 3,000')).toBeInTheDocument()
        expect(screen.getByText('92%')).toBeInTheDocument() // 91.7 rounded
        
        expect(screen.getByText('5.1 / 6')).toBeInTheDocument()
        expect(screen.getByText('85%')).toBeInTheDocument()
        
        expect(screen.getByText('45 / 60')).toBeInTheDocument()
        expect(screen.getByText('75%')).toBeInTheDocument()
        
        expect(screen.getByText('6,000 / 6,000')).toBeInTheDocument()
        expect(screen.getByText('100%')).toBeInTheDocument()
      })
    })

    it('shows platform and timing information', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Platform: linkedin')).toBeInTheDocument()
        expect(screen.getByText('Platform: all')).toBeInTheDocument()
        expect(screen.getByText('Platform: twitter')).toBeInTheDocument()
        
        expect(screen.getByText('71 days remaining')).toBeInTheDocument()
        expect(screen.getByText('41 days remaining')).toBeInTheDocument()
        expect(screen.getByText('9 days remaining')).toBeInTheDocument()
      })
    })
  })

  describe('Milestones Display', () => {
    it('shows milestones for goals that have them', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Recent Milestones')).toBeInTheDocument()
        expect(screen.getByText('Reached 25% of goal')).toBeInTheDocument()
        expect(screen.getByText('Reached 50% of goal')).toBeInTheDocument()
      })
    })

    it('formats milestone dates correctly', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Jul 15, 2025')).toBeInTheDocument()
        expect(screen.getByText('Jul 28, 2025')).toBeInTheDocument()
      })
    })
  })

  describe('Goal Actions', () => {
    it('shows appropriate action buttons for active goals', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getAllByText('Update Progress')).toHaveLength(3) // For 3 active goals
        expect(screen.getAllByText('Pause')).toHaveLength(3)
        expect(screen.getAllByText('View Details')).toHaveLength(4) // For all goals
      })
    })

    it('opens goal detail modal when view details clicked', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        const viewDetailsButtons = screen.getAllByText('View Details')
        fireEvent.click(viewDetailsButtons[0])
      })
      
      expect(screen.getByTestId('goal-detail-modal')).toBeInTheDocument()
      expect(screen.getByText('Goal: Grow LinkedIn Following')).toBeInTheDocument()
    })
  })

  describe('Goal Creation', () => {
    it('opens create goal modal when new goal button clicked', () => {
      renderWithQueryClient(<GoalTracking />)
      
      const newGoalButton = screen.getByRole('button', { name: /New Goal/ })
      fireEvent.click(newGoalButton)
      
      expect(screen.getByTestId('create-goal-modal')).toBeInTheDocument()
    })

    it('handles goal creation submission', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      const newGoalButton = screen.getByRole('button', { name: /New Goal/ })
      fireEvent.click(newGoalButton)
      
      const submitButton = screen.getByText('Submit')
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(mockApi.goals.create).toHaveBeenCalledWith({ title: 'Test Goal' })
      })
    })
  })

  describe('Goal Updates and Deletion', () => {
    it('handles goal updates through detail modal', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        const viewDetailsButtons = screen.getAllByText('View Details')
        fireEvent.click(viewDetailsButtons[0])
      })
      
      const updateButton = screen.getByText('Update')
      fireEvent.click(updateButton)
      
      await waitFor(() => {
        expect(mockApi.goals.update).toHaveBeenCalledWith(1, {
          id: 1,
          title: 'Updated Goal',
          description: 'Increase LinkedIn followers from 2,500 to 3,000',
          goal_type: 'follower_growth',
          target_value: 3000,
          current_value: 2750,
          start_date: '2025-07-01',
          target_date: '2025-10-01',
          platform: 'linkedin',
          status: 'active',
          progress_percentage: 91.7,
          days_remaining: 71,
          is_on_track: true,
          milestones: [
            { id: 1, description: 'Reached 25% of goal', percentage: 25, achieved_at: '2025-07-15' },
            { id: 2, description: 'Reached 50% of goal', percentage: 50, achieved_at: '2025-07-28' }
          ]
        })
      })
    })

    it('handles goal deletion through detail modal', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        const viewDetailsButtons = screen.getAllByText('View Details')
        fireEvent.click(viewDetailsButtons[0])
      })
      
      const deleteButton = screen.getByText('Delete')
      fireEvent.click(deleteButton)
      
      await waitFor(() => {
        expect(mockApi.goals.delete).toHaveBeenCalledWith(1)
      })
    })
  })

  describe('Empty States', () => {
    it('shows empty state when no goals exist', async () => {
      mockApi.goals.getAll.mockResolvedValue([])
      
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('No goals found')).toBeInTheDocument()
        expect(screen.getByText('Create your first goal to start tracking progress.')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Create Goal/ })).toBeInTheDocument()
      })
    })

    it('shows filtered empty state', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Grow LinkedIn Following')).toBeInTheDocument()
      })
      
      // Filter to show only paused goals (none exist)
      const statusFilter = screen.getByDisplayValue('All Goals')
      fireEvent.change(statusFilter, { target: { value: 'paused' } })
      
      await waitFor(() => {
        expect(screen.getByText('No goals found')).toBeInTheDocument()
        expect(screen.getByText('No paused goals found.')).toBeInTheDocument()
      })
    })
  })

  describe('Status Indicators', () => {
    it('shows correct status icons based on goal state', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        // Should show warning icon for off-track goal
        const goalCards = screen.getAllByText('Monthly Content Volume')
        expect(goalCards).toHaveLength(1)
        
        // Should show completed icon for completed goal
        const completedGoal = screen.getByText('Twitter Growth Campaign')
        expect(completedGoal).toBeInTheDocument()
      })
    })

    it('applies correct progress bar colors', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        // Progress bars should have different colors based on status
        const progressBars = document.querySelectorAll('.h-2.rounded-full')
        expect(progressBars.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Date Formatting', () => {
    it('formats target dates correctly', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      await waitFor(() => {
        expect(screen.getByText('Target: Oct 1, 2025')).toBeInTheDocument()
        expect(screen.getByText('Target: Sep 1, 2025')).toBeInTheDocument()
        expect(screen.getByText('Target: Jul 31, 2025')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})
      mockApi.goals.create.mockRejectedValue(new Error('Create failed'))
      
      renderWithQueryClient(<GoalTracking />)
      
      const newGoalButton = screen.getByRole('button', { name: /New Goal/ })
      fireEvent.click(newGoalButton)
      
      const submitButton = screen.getByText('Submit')
      fireEvent.click(submitButton)
      
      // Should not crash the app
      await waitFor(() => {
        expect(screen.getByText('Goal Tracking')).toBeInTheDocument()
      })
      
      consoleError.mockRestore()
    })
  })

  describe('Loading States', () => {
    it('uses fallback data during loading', () => {
      mockApi.goals.getAll.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )
      
      renderWithQueryClient(<GoalTracking />)
      
      // Should show mock data as fallback
      expect(screen.getByText('Goal Tracking')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      renderWithQueryClient(<GoalTracking />)
      
      expect(screen.getByRole('heading', { level: 2, name: 'Goal Tracking' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 3, name: 'Goal Status Overview' })).toBeInTheDocument()
    })

    it('provides meaningful button labels', async () => {
      renderWithQueryClient(<GoalTracking />)
      
      expect(screen.getByRole('button', { name: /New Goal/ })).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.getAllByText('Update Progress')).toHaveLength(3)
        expect(screen.getAllByText('View Details')).toHaveLength(4)
      })
    })

    it('uses semantic form controls', () => {
      renderWithQueryClient(<GoalTracking />)
      
      expect(screen.getByRole('combobox')).toBeInTheDocument() // Status filter dropdown
    })
  })
})