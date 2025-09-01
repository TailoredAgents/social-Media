import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEnhancedApi } from '../hooks/useEnhancedApi'
import { error as logError } from '../utils/logger.js'
import AIEmptyStateSuggestions from '../components/AIEmptyStatesSuggestions'
import { 
  TrophyIcon,
  PlusIcon,
  ChartBarIcon,
  CalendarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PauseIcon,
  PlayIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import CreateGoalModal from '../components/Goals/CreateGoalModal'
import GoalDetailModal from '../components/Goals/GoalDetailModal'
import { GoalCompletionChart } from '../components/Charts/ProgressChart'

// Empty goals data - real data should come from API  
const emptyGoals = []

const goalTypes = [
  { value: 'follower_growth', label: 'Follower Growth', icon: ChartBarIcon },
  { value: 'engagement_rate', label: 'Engagement Rate', icon: TrophyIcon },
  { value: 'content_volume', label: 'Content Volume', icon: CalendarIcon },
  { value: 'reach_increase', label: 'Reach Increase', icon: ChartBarIcon }
]

export default function GoalTracking() {
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedGoal, setSelectedGoal] = useState(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  
  const { api, connectionStatus } = useEnhancedApi()
  const queryClient = useQueryClient()

  // Fetch goals with React Query
  const { 
    data: goals = [], 
    isLoading: goalsLoading, 
    error: goalsError, 
    refetch: refetchGoals 
  } = useQuery({
    queryKey: ['goals'],
    queryFn: api.goals.getAll,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
    fallbackData: emptyGoals // Use empty data as fallback
  })

  // Fetch goals dashboard data
  const { 
    data: dashboardData, 
    isLoading: dashboardLoading 
  } = useQuery({
    queryKey: ['goals-dashboard'],
    queryFn: api.goals.getDashboard,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2
  })

  // Create goal mutation
  const createGoalMutation = useMutation({
    mutationFn: api.goals.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['goals-dashboard'] })
      setShowCreateModal(false)
    },
    onError: (error) => {
      logError('Failed to create goal:', error)
    }
  })

  // Update goal mutation
  const updateGoalMutation = useMutation({
    mutationFn: ({ goalId, goalData }) => api.goals.update(goalId, goalData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['goals-dashboard'] })
      setShowDetailModal(false)
    },
    onError: (error) => {
      logError('Failed to update goal:', error)
    }
  })

  // Delete goal mutation
  const deleteGoalMutation = useMutation({
    mutationFn: api.goals.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['goals-dashboard'] })
      setShowDetailModal(false)
    },
    onError: (error) => {
      logError('Failed to delete goal:', error)
    }
  })

  // Update progress mutation
  const updateProgressMutation = useMutation({
    mutationFn: ({ goalId, progressData }) => api.goals.updateProgress(goalId, progressData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['goals-dashboard'] })
    },
    onError: (error) => {
      logError('Failed to update progress:', error)
    }
  })

  // Ensure goals is always an array
  const goalsArray = Array.isArray(goals) ? goals : (goals?.goals || [])
  
  const filteredGoals = goalsArray.filter(goal => 
    selectedStatus === 'all' || goal.status === selectedStatus
  )

  const handleCreateGoal = async (goalData) => {
    try {
      await createGoalMutation.mutateAsync(goalData)
    } catch (error) {
      logError('Create goal error:', error)
    }
  }

  const handleUpdateGoal = async (updatedGoal) => {
    try {
      await updateGoalMutation.mutateAsync({ 
        goalId: updatedGoal.id, 
        goalData: updatedGoal 
      })
    } catch (error) {
      logError('Update goal error:', error)
    }
  }

  const handleDeleteGoal = async (goalId) => {
    try {
      await deleteGoalMutation.mutateAsync(goalId)
    } catch (error) {
      logError('Delete goal error:', error)
    }
  }

  const handleUpdateProgress = async (goalId, progressData) => {
    try {
      await updateProgressMutation.mutateAsync({ goalId, progressData })
    } catch (error) {
      logError('Update progress error:', error)
    }
  }

  const openGoalDetail = (goal) => {
    setSelectedGoal(goal)
    setShowDetailModal(true)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'active':
        return 'bg-blue-100 text-blue-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (goal) => {
    if (goal.status === 'completed') {
      return <CheckCircleIcon className="h-5 w-5 text-green-600" />
    }
    if (!goal.is_on_track && goal.status === 'active') {
      return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
    }
    return <ChartBarIcon className="h-5 w-5 text-blue-600" />
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Calculate summary stats
  const totalGoals = goalsArray.length
  const activeGoals = goalsArray.filter(g => g.status === 'active').length
  const completedGoals = goalsArray.filter(g => g.status === 'completed').length
  const onTrackGoals = goalsArray.filter(g => g.is_on_track && g.status === 'active').length
  const avgProgress = goalsArray.length > 0 ? goalsArray.reduce((sum, g) => sum + g.progress_percentage, 0) / goalsArray.length : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Goal Tracking</h2>
          <p className="text-sm text-gray-600">
            Monitor progress toward your social media objectives
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md flex items-center space-x-2 hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          <span>New Goal</span>
        </button>
      </div>

      {/* Summary Cards and Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-gray-900">{totalGoals}</div>
              <div className="text-sm text-gray-600">Total Goals</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-blue-600">{activeGoals}</div>
              <div className="text-sm text-gray-600">Active Goals</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-green-600">{completedGoals}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-orange-600">{Math.round(avgProgress)}%</div>
              <div className="text-sm text-gray-600">Avg Progress</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Goal Status Overview</h3>
          <GoalCompletionChart goals={goals} />
        </div>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by status:</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Goals</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="paused">Paused</option>
          </select>
        </div>
      </div>

      {/* Goals List */}
      <div className="space-y-4">
        {filteredGoals.map((goal) => (
          <div key={goal.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start space-x-3">
                {getStatusIcon(goal)}
                <div>
                  <h3 className="font-semibold text-gray-900">{goal.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{goal.description}</p>
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span>Platform: {goal.platform}</span>
                    <span>Target: {formatDate(goal.target_date)}</span>
                    {goal.days_remaining > 0 && (
                      <span>{goal.days_remaining} days remaining</span>
                    )}
                  </div>
                </div>
              </div>
              
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(goal.status)}`}>
                {goal.status}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">
                  {goal.current_value.toLocaleString()} / {goal.target_value.toLocaleString()}
                </span>
                <span className={`font-medium ${goal.is_on_track ? 'text-green-600' : 'text-yellow-600'}`}>
                  {Math.round(goal.progress_percentage)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    goal.status === 'completed' 
                      ? 'bg-green-500' 
                      : goal.is_on_track 
                        ? 'bg-blue-500' 
                        : 'bg-yellow-500'
                  }`}
                  style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                />
              </div>
            </div>

            {/* Milestones */}
            {goal.milestones.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Milestones</h4>
                <div className="space-y-1">
                  {goal.milestones.slice(-3).map((milestone) => (
                    <div key={milestone.id} className="flex items-center text-xs text-gray-600">
                      <CheckCircleIcon className="h-3 w-3 text-green-500 mr-2" />
                      <span>{milestone.description}</span>
                      <span className="ml-auto">{formatDate(milestone.achieved_at)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-2">
              {goal.status === 'active' && (
                <>
                  <button className="text-sm bg-blue-50 text-blue-600 px-3 py-1 rounded-md hover:bg-blue-100 transition-colors">
                    Update Progress
                  </button>
                  <button className="text-sm bg-yellow-50 text-yellow-600 px-3 py-1 rounded-md hover:bg-yellow-100 transition-colors flex items-center space-x-1">
                    <PauseIcon className="h-3 w-3" />
                    <span>Pause</span>
                  </button>
                </>
              )}
              
              {goal.status === 'paused' && (
                <button className="text-sm bg-green-50 text-green-600 px-3 py-1 rounded-md hover:bg-green-100 transition-colors flex items-center space-x-1">
                  <PlayIcon className="h-3 w-3" />
                  <span>Resume</span>
                </button>
              )}

              <button 
                onClick={() => openGoalDetail(goal)}
                className="text-sm text-gray-600 px-3 py-1 rounded-md hover:bg-gray-50 transition-colors flex items-center space-x-1"
              >
                <EyeIcon className="h-3 w-3" />
                <span>View Details</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredGoals.length === 0 && (
        <AIEmptyStateSuggestions 
          type="goals"
          context={{ 
            hasFilters: selectedStatus !== 'all',
            selectedStatus
          }}
          onSuggestionClick={(suggestion) => {
            switch(suggestion.id) {
              case 'growth-goals':
              case 'engagement-goals':
              case 'smart-goals':
              default:
                setShowCreateModal(true)
                break
            }
          }}
        />
      )}

      {/* Modals */}
      <CreateGoalModal 
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateGoal}
      />
      
      <GoalDetailModal
        goal={selectedGoal}
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        onUpdate={handleUpdateGoal}
        onDelete={handleDeleteGoal}
      />
    </div>
  )
}