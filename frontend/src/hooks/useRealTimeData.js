import { useState, useEffect, useRef, useCallback } from 'react'
import { useApi } from './useApi'
import { useSchemaStatus } from './useSchemaStatus'
import { error as logError, debug as logDebug } from '../utils/logger.js'

export const useRealTimeData = (endpoint, options = {}) => {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  
  const { apiService, makeAuthenticatedRequest } = useApi()
  const { shouldPoll, getPollingInterval } = useSchemaStatus()
  const intervalRef = useRef(null)
  const mountedRef = useRef(true)
  
  const {
    refreshInterval = 30000, // 30 seconds default
    enabled = true,
    onDataUpdate = null,
    retryAttempts = 3,
    retryDelay = 1000
  } = options

  const fetchData = useCallback(async (attemptCount = 0) => {
    if (!mountedRef.current || !enabled || !shouldPoll()) return

    try {
      setError(null)
      
      let result
      if (typeof endpoint === 'function') {
        result = await makeAuthenticatedRequest(endpoint)
      } else {
        // Handle different endpoint types
        switch (endpoint) {
          case 'analytics':
            result = await makeAuthenticatedRequest(apiService.getMetrics)
            break
          case 'performance':
            result = await makeAuthenticatedRequest(apiService.getPerformanceMetrics)
            break
          case 'goals':
            result = await makeAuthenticatedRequest(apiService.getGoalsDashboard)
            break
          case 'content':
            result = await makeAuthenticatedRequest(apiService.getUpcomingContent)
            break
          case 'memory':
            result = await makeAuthenticatedRequest(apiService.getMemoryAnalytics)
            break
          case 'notifications':
            result = await makeAuthenticatedRequest(apiService.getNotificationsSummary)
            break
          case 'workflow':
            result = await makeAuthenticatedRequest(apiService.getWorkflowStatusSummary)
            break
          default:
            throw new Error(`Unknown endpoint: ${endpoint}`)
        }
      }
      
      if (mountedRef.current) {
        setData(result)
        setLastUpdated(new Date())
        setIsLoading(false)
        
        if (onDataUpdate) {
          onDataUpdate(result)
        }
      }
    } catch (err) {
      logError(`Real-time data fetch failed for ${endpoint}:`, err)
      
      if (attemptCount < retryAttempts) {
        setTimeout(() => {
          fetchData(attemptCount + 1)
        }, retryDelay * Math.pow(2, attemptCount)) // Exponential backoff
      } else {
        if (mountedRef.current) {
          setError(err)
          setIsLoading(false)
        }
      }
    }
  }, [endpoint, enabled, apiService, makeAuthenticatedRequest, onDataUpdate, retryAttempts, retryDelay, shouldPoll])

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    
    // Use schema-aware polling interval
    const dynamicInterval = getPollingInterval(refreshInterval, refreshInterval * 10)
    logDebug(`useRealTimeData: Polling ${endpoint} every ${dynamicInterval / 1000}s`)
    
    intervalRef.current = setInterval(fetchData, dynamicInterval)
  }, [fetchData, refreshInterval, getPollingInterval, endpoint])

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const refreshNow = useCallback(() => {
    setIsLoading(true)
    fetchData()
  }, [fetchData])

  useEffect(() => {
    mountedRef.current = true
    
    // Only start polling if schema allows it
    if (enabled && shouldPoll()) {
      fetchData() // Initial fetch
      startPolling() // Start polling
    } else if (!shouldPoll()) {
      logDebug(`useRealTimeData: Polling disabled for ${endpoint} due to database schema issues`)
      setData(null)
      setIsLoading(false)
      setError(null)
    }

    return () => {
      mountedRef.current = false
      stopPolling()
    }
  }, [enabled, fetchData, startPolling, stopPolling, shouldPoll, endpoint])

  useEffect(() => {
    // Handle visibility change to pause/resume polling when tab is hidden
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopPolling()
      } else if (enabled && shouldPoll()) {
        refreshNow()
        startPolling()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [enabled, refreshNow, startPolling, stopPolling, shouldPoll])

  return {
    data,
    isLoading,
    error,
    lastUpdated,
    refreshNow,
    startPolling,
    stopPolling
  }
}

export const useRealTimeAnalytics = (timeframe = '7d') => {
  return useRealTimeData('analytics', {
    refreshInterval: 30000, // 30 seconds
    onDataUpdate: (data) => {
      logDebug('Analytics updated:', data)
    }
  })
}

export const useRealTimePerformance = (platform = 'all') => {
  return useRealTimeData('performance', {
    refreshInterval: 60000, // 1 minute
    onDataUpdate: (data) => {
      logDebug('Performance metrics updated:', data)
    }
  })
}

export const useRealTimeGoals = () => {
  return useRealTimeData('goals', {
    refreshInterval: 120000, // 2 minutes
    onDataUpdate: (data) => {
      logDebug('Goals updated:', data)
    }
  })
}

export const useRealTimeMemory = () => {
  return useRealTimeData('memory', {
    refreshInterval: 300000, // 5 minutes
    onDataUpdate: (data) => {
      logDebug('Memory analytics updated:', data)
    }
  })
}

export const useRealTimeNotifications = () => {
  return useRealTimeData('notifications', {
    refreshInterval: 60000, // 1 minute
    onDataUpdate: (data) => {
      logDebug('Notifications updated:', data)
    }
  })
}

export const useRealTimeWorkflow = () => {
  return useRealTimeData('workflow', {
    refreshInterval: 30000, // 30 seconds
    onDataUpdate: (data) => {
      logDebug('Workflow status updated:', data)
    }
  })
}

export const useRealTimeContent = () => {
  return useRealTimeData('content', {
    refreshInterval: 60000, // 1 minute
    onDataUpdate: (data) => {
      logDebug('Content updated:', data)
    }
  })
}

export const useRealTimeMetrics = () => {
  return useRealTimeData('analytics', {
    refreshInterval: 30000, // 30 seconds
    onDataUpdate: (data) => {
      logDebug('Real-time metrics updated:', data)
    }
  })
}