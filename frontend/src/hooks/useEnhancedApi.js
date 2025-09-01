import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'
import { useNotifications } from './useNotifications'
import { error as logError, debug as logDebug } from '../utils/logger.js'

// Enhanced API hook with better error handling, caching, and state management
export const useEnhancedApi = () => {
  const { accessToken, refreshToken, isAuthenticated, logout } = useAuth()
  const [connectionStatus, setConnectionStatus] = useState('connected') // connected, disconnected, reconnecting
  const [apiHealth, setApiHealth] = useState(null)
  const retryTimeouts = useRef(new Map())
  const cache = useRef(new Map())
  const { showError, showSuccess, notifyApiError } = useNotifications()
  
  // Initialize API service with token
  useEffect(() => {
    if (accessToken && isAuthenticated) {
      apiService.setToken(accessToken)
      checkApiHealth()
    } else {
      apiService.setToken(null)
    }
  }, [accessToken, isAuthenticated])

  // Health check function
  const checkApiHealth = useCallback(async () => {
    try {
      const health = await apiService.getHealth()
      setApiHealth(health)
      setConnectionStatus('connected')
      return health
    } catch (error) {
      logError('API health check failed:', error)
      setConnectionStatus('disconnected') 
      setApiHealth(null)
      return null
    }
  }, [])

  // Enhanced request function with retry logic and caching
  const makeEnhancedRequest = useCallback(async (
    requestFn, 
    options = {}
  ) => {
    const {
      retries = 0, // Disable retries to prevent cascading
      retryDelay = 5000, // Longer delays if retries happen
      cache: shouldCache = false,
      cacheKey = null,
      cacheTTL = 300000, // 5 minutes
      showNotification = false, // Disable notifications to reduce noise
      onSuccess = null,
      onError = null,
      requestArgs = []
    } = options

    // Check cache first
    if (shouldCache && cacheKey) {
      const cached = cache.current.get(cacheKey)
      if (cached && Date.now() - cached.timestamp < cacheTTL) {
        return cached.data
      }
    }

    const executeRequest = async (attempt = 1) => {
      try {
        // Skip request if backend is known to be down
        if (connectionStatus === 'disconnected') {
          throw new Error('Backend is down - skipping request to prevent CORS errors')
        }
        
        setConnectionStatus('connected')
        const result = await requestFn(...requestArgs)
        
        // Cache successful results
        if (shouldCache && cacheKey) {
          cache.current.set(cacheKey, {
            data: result,
            timestamp: Date.now()
          })
        }
        
        // Call success callback if provided
        if (onSuccess) {
          onSuccess(result)
        }
        
        return result
      } catch (error) {
        logError(`API request failed (attempt ${attempt}):`, error)
        
        // Handle authentication errors
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          try {
            logDebug('Token expired, attempting refresh...')
            const newToken = await refreshToken()
            if (newToken) {
              apiService.setToken(newToken)
              return await requestFn(...requestArgs)
            } else {
              // If refresh fails, logout user
              logout()
              showError('Session expired. Please log in again.', 'Authentication Error')
              throw new Error('Authentication failed. Please log in again.')
            }
          } catch (refreshError) {
            logError('Token refresh failed:', refreshError)
            logout()
            showError('Session expired. Please log in again.', 'Authentication Error')
            throw new Error('Session expired. Please log in again.')
          }
        }

        // Handle network errors with retry logic
        if (attempt < retries && (
          error.message.includes('NetworkError') ||
          error.message.includes('Failed to fetch') ||
          error.message.includes('500') ||
          error.message.includes('502') ||
          error.message.includes('503')
        )) {
          setConnectionStatus('reconnecting')
          
          // Clear any existing timeout for this request
          const timeoutKey = `${requestFn.name}_${attempt}`
          if (retryTimeouts.current.has(timeoutKey)) {
            clearTimeout(retryTimeouts.current.get(timeoutKey))
          }
          
          // Set new timeout with exponential backoff
          const delay = retryDelay * Math.pow(2, attempt - 1)
          
          return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(async () => {
              retryTimeouts.current.delete(timeoutKey)
              try {
                const result = await executeRequest(attempt + 1)
                resolve(result)
              } catch (retryError) {
                reject(retryError)
              }
            }, delay)
            
            retryTimeouts.current.set(timeoutKey, timeoutId)
          })
        }

        // Set disconnected status for persistent failures
        if (attempt >= retries) {
          setConnectionStatus('disconnected')
          
          // Only show error notifications for important operations (not for background polling)
          if (showNotification) {
            notifyApiError(
              error.message || 'Request failed after multiple attempts',
              () => executeRequest(1)
            )
          }
        }
        
        throw error
      }
    }

    return executeRequest()
  }, [accessToken, refreshToken, logout])

  // Specific API methods with enhanced features - memoized to prevent recreation
  const api = useMemo(() => ({
    // Memory operations
    memory: {
      search: (query, limit = 5) => makeEnhancedRequest(
        apiService.searchMemory.bind(apiService),
        { 
          requestArgs: [query, limit], 
          cache: true, 
          cacheKey: `memory_search_${query}_${limit}`,
          cacheTTL: 60000 // 1 minute cache for searches
        }
      ),
      
      getAll: (page = 1, limit = 20) => makeEnhancedRequest(
        apiService.getAllMemory.bind(apiService),
        { 
          requestArgs: [page, limit], 
          cache: true, 
          cacheKey: `memory_all_${page}_${limit}`,
          cacheTTL: 120000 // 2 minutes
        }
      ),
      
      store: (content, metadata) => makeEnhancedRequest(
        apiService.storeMemory.bind(apiService),
        { requestArgs: [content, metadata], retries: 2 }
      ),
      
      update: (contentId, data) => makeEnhancedRequest(
        apiService.updateMemory.bind(apiService),
        { requestArgs: [contentId, data], retries: 2 }
      ),
      
      delete: (contentId) => makeEnhancedRequest(
        apiService.deleteMemory.bind(apiService),
        { requestArgs: [contentId], retries: 2 }
      ),
      
      getAnalytics: () => makeEnhancedRequest(
        apiService.getMemoryAnalytics.bind(apiService),
        { cache: true, cacheKey: 'memory_analytics', cacheTTL: 300000 }
      )
    },

    // Goals operations  
    goals: {
      getAll: async () => {
        const response = await makeEnhancedRequest(
          apiService.getGoals.bind(apiService),
          { cache: true, cacheKey: 'goals_all', cacheTTL: 120000 }
        )
        // Extract goals array from API response {goals: [], count: number}
        return response?.goals || []
      },
      
      create: (goalData) => makeEnhancedRequest(
        apiService.createGoal.bind(apiService),
        { 
          requestArgs: [goalData], 
          retries: 2,
          onSuccess: () => showSuccess('Goal created successfully!')
        }
      ),
      
      update: (goalId, goalData) => makeEnhancedRequest(
        apiService.updateGoal.bind(apiService),
        { requestArgs: [goalId, goalData], retries: 2 }
      ),
      
      updateProgress: (goalId, progressData) => makeEnhancedRequest(
        apiService.updateGoalProgress.bind(apiService),
        { requestArgs: [goalId, progressData], retries: 2 }
      ),
      
      delete: (goalId) => makeEnhancedRequest(
        apiService.deleteGoal.bind(apiService),
        { requestArgs: [goalId], retries: 2 }
      ),
      
      getDashboard: () => makeEnhancedRequest(
        apiService.getGoalsDashboard.bind(apiService),
        { cache: true, cacheKey: 'goals_dashboard', cacheTTL: 180000 }
      )
    },

    // Content operations
    content: {
      getAll: (page = 1, limit = 20) => makeEnhancedRequest(
        apiService.getContent.bind(apiService),
        { 
          requestArgs: [page, limit], 
          cache: true, 
          cacheKey: `content_all_${page}_${limit}`,
          cacheTTL: 120000 
        }
      ),
      
      create: (contentData) => makeEnhancedRequest(
        apiService.createContent.bind(apiService),
        { requestArgs: [contentData], retries: 2 }
      ),
      
      update: (contentId, contentData) => makeEnhancedRequest(
        apiService.updateContent.bind(apiService),
        { requestArgs: [contentId, contentData], retries: 2 }
      ),
      
      delete: (contentId) => makeEnhancedRequest(
        apiService.deleteContent.bind(apiService),
        { requestArgs: [contentId], retries: 2 }
      ),
      
      getUpcoming: () => makeEnhancedRequest(
        apiService.getUpcomingContent.bind(apiService),
        { cache: true, cacheKey: 'content_upcoming', cacheTTL: 60000 }
      ),
      
      generate: (prompt, contentType, platform = 'twitter') => makeEnhancedRequest(
        apiService.generateContent.bind(apiService),
        { requestArgs: [prompt, contentType, platform], retries: 1, retryDelay: 2000 }
      ),
      
      generateImage: (prompt, contentContext, platform, industryContext) => makeEnhancedRequest(
        apiService.generateImage.bind(apiService),
        { requestArgs: [prompt, contentContext, platform, industryContext], retries: 1, retryDelay: 3000 }
      ),
      
      getAnalytics: () => makeEnhancedRequest(
        apiService.getContentAnalytics.bind(apiService),
        { cache: true, cacheKey: 'content_analytics', cacheTTL: 300000 }
      )
    },

    // Analytics operations
    analytics: {
      getMetrics: () => makeEnhancedRequest(
        apiService.getMetrics.bind(apiService),
        { cache: true, cacheKey: 'analytics_metrics', cacheTTL: 60000 }
      ),
      
      getPerformance: (platform = 'all') => makeEnhancedRequest(
        apiService.getPerformanceMetrics.bind(apiService),
        { 
          requestArgs: [platform], 
          cache: true, 
          cacheKey: `analytics_performance_${platform}`,
          cacheTTL: 60000 
        }
      ),
      
      getAnalytics: (timeframe = '7d') => makeEnhancedRequest(
        apiService.getAnalytics.bind(apiService),
        { 
          requestArgs: [timeframe], 
          cache: true, 
          cacheKey: `analytics_${timeframe}`,
          cacheTTL: 180000 
        }
      )
    },

    // Workflow operations
    workflow: {
      execute: (workflowData) => makeEnhancedRequest(
        apiService.executeWorkflow.bind(apiService),
        { requestArgs: [workflowData], retries: 1, retryDelay: 3000 }
      ),
      
      getExecutions: () => makeEnhancedRequest(
        apiService.getWorkflowExecutions.bind(apiService),
        { cache: true, cacheKey: 'workflow_executions', cacheTTL: 30000 }
      ),
      
      getStatusSummary: () => makeEnhancedRequest(
        apiService.getWorkflowStatusSummary.bind(apiService),
        { cache: true, cacheKey: 'workflow_status', cacheTTL: 30000 }
      ),
      
      executeDailyWorkflow: () => makeEnhancedRequest(
        apiService.executeDailyWorkflow.bind(apiService),
        { retries: 1, retryDelay: 5000 }
      )
    },

    // Notifications operations
    notifications: {
      getAll: () => makeEnhancedRequest(
        apiService.getNotifications.bind(apiService),
        { cache: true, cacheKey: 'notifications_all', cacheTTL: 30000 }
      ),
      
      getSummary: () => makeEnhancedRequest(
        apiService.getNotificationsSummary.bind(apiService),
        { cache: true, cacheKey: 'notifications_summary', cacheTTL: 30000 }
      ),
      
      markRead: (notificationId) => makeEnhancedRequest(
        apiService.markNotificationRead.bind(apiService),
        { requestArgs: [notificationId], retries: 2 }
      ),
      
      markAllRead: () => makeEnhancedRequest(
        apiService.markAllNotificationsRead.bind(apiService),
        { retries: 2 }
      )
    },

    // Autonomous operations
    autonomous: {
      getLatestResearch: () => makeEnhancedRequest(
        apiService.getLatestResearch.bind(apiService),
        { cache: true, cacheKey: 'autonomous_research', cacheTTL: 300000 }
      ),
      
      getStatus: () => makeEnhancedRequest(
        apiService.getAutonomousStatus.bind(apiService),
        { cache: true, cacheKey: 'autonomous_status', cacheTTL: 60000 }
      ),
      
      executeeCycle: () => makeEnhancedRequest(
        apiService.executeAutonomousCycle.bind(apiService),
        { retries: 1, retryDelay: 3000 }
      ),

      researchCompany: (companyName) => makeEnhancedRequest(
        () => apiService.researchCompany(companyName),
        { retries: 2, retryDelay: 2000 }
      )
    },

    // User Settings operations
    settings: {
      get: () => makeEnhancedRequest(
        apiService.getUserSettings.bind(apiService),
        { cache: true, cacheKey: 'user_settings', cacheTTL: 300000 }
      ),
      
      update: (settings) => makeEnhancedRequest(
        apiService.updateUserSettings.bind(apiService),
        { 
          requestArgs: [settings], 
          retries: 2,
          onSuccess: () => {
            // Clear settings cache after update
            cache.current.delete('user_settings')
            showSuccess('Settings updated successfully!')
          }
        }
      ),
      
      getDefaults: () => makeEnhancedRequest(
        apiService.getDefaultSettings.bind(apiService),
        { cache: true, cacheKey: 'default_settings', cacheTTL: 3600000 }
      )
    },

    // AI Suggestions operations
    ai: {
      getContextualSuggestions: (request) => makeEnhancedRequest(
        apiService.getContextualSuggestions.bind(apiService),
        { 
          requestArgs: [request], 
          cache: true, 
          cacheKey: `ai_suggestions_${request.type}_${JSON.stringify(request.context).slice(0, 50)}`,
          cacheTTL: 300000  // 5 minutes cache for AI suggestions
        }
      ),
      
      getSuggestionTypes: () => makeEnhancedRequest(
        apiService.getSuggestionTypes.bind(apiService),
        { cache: true, cacheKey: 'ai_suggestion_types', cacheTTL: 3600000 }
      )
    }
  }), [makeEnhancedRequest, showSuccess]) // Only recreate when dependencies change

  // Utility functions
  const clearCache = useCallback((pattern = null) => {
    if (pattern) {
      // Clear cache entries matching pattern
      for (const key of cache.current.keys()) {
        if (key.includes(pattern)) {
          cache.current.delete(key)
        }
      }
    } else {
      // Clear all cache
      cache.current.clear()
    }
  }, [])

  const getCacheStats = useCallback(() => {
    return {
      size: cache.current.size,
      keys: Array.from(cache.current.keys())
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clear all retry timeouts
      for (const timeoutId of retryTimeouts.current.values()) {
        clearTimeout(timeoutId)
      }
      retryTimeouts.current.clear()
    }
  }, [])

  return {
    api,
    connectionStatus,
    apiHealth,
    checkApiHealth,
    clearCache,
    getCacheStats,
    makeEnhancedRequest
  }
}

export default useEnhancedApi