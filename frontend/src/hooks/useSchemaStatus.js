import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'

/**
 * Hook to check database schema status and throttle polling when schema is incomplete
 * 
 * This prevents infinite error loops when the database is missing tables/columns
 * and provides graceful degradation for dashboard components.
 */
export const useSchemaStatus = () => {
  const [schemaStatus, setSchemaStatus] = useState({
    isHealthy: false,
    isChecking: true,
    missingTables: [],
    lastChecked: null,
    retryCount: 0
  })
  
  const { isAuthenticated } = useAuth()
  
  const checkSchemaHealth = useCallback(async () => {
    if (!isAuthenticated) {
      setSchemaStatus(prev => ({ 
        ...prev, 
        isHealthy: false, 
        isChecking: false,
        lastChecked: new Date()
      }))
      return
    }
    
    try {
      setSchemaStatus(prev => ({ ...prev, isChecking: true }))
      
      // Check database health endpoint
      const response = await fetch('/api/database/health', {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        }
      })
      
      if (response.ok) {
        const healthData = await response.json()
        const isHealthy = healthData.status === 'healthy' && healthData.database_connected
        
        setSchemaStatus(prev => ({
          isHealthy,
          isChecking: false,
          missingTables: healthData.tables?.missing_tables || [],
          lastChecked: new Date(),
          retryCount: isHealthy ? 0 : Math.min(prev.retryCount + 1, 10)
        }))
        
        return isHealthy
      } else if (response.status === 503) {
        // Service unavailable - likely schema issue
        const errorData = await response.json().catch(() => ({}))
        
        setSchemaStatus(prev => ({
          isHealthy: false,
          isChecking: false,
          missingTables: errorData.missing_tables || ['unknown'],
          lastChecked: new Date(),
          retryCount: Math.min(prev.retryCount + 1, 10)
        }))
        
        return false
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.warn('Schema health check failed:', error.message)
      
      // Don't increment retry count for network errors
      setSchemaStatus(prev => ({
        isHealthy: false,
        isChecking: false,
        missingTables: ['connection_error'],
        lastChecked: new Date(),
        retryCount: prev.retryCount
      }))
      
      return false
    }
  }, [isAuthenticated])
  
  // Initial check and periodic verification
  useEffect(() => {
    if (!isAuthenticated) return
    
    checkSchemaHealth()
    
    // Check schema health every 2 minutes (less frequent than API polling)
    const interval = setInterval(checkSchemaHealth, 120000)
    
    return () => clearInterval(interval)
  }, [checkSchemaHealth, isAuthenticated])
  
  /**
   * Get appropriate polling interval based on schema health
   * @param {number} normalInterval - Normal polling interval in ms
   * @param {number} degradedInterval - Degraded polling interval in ms  
   * @returns {number} Recommended polling interval
   */
  const getPollingInterval = useCallback((normalInterval = 30000, degradedInterval = 300000) => {
    if (!schemaStatus.isHealthy) {
      // If schema is unhealthy, use much longer interval (5 minutes default)
      // or exponential backoff based on retry count
      const backoffMultiplier = Math.min(Math.pow(2, schemaStatus.retryCount), 32)
      return Math.max(degradedInterval, degradedInterval * backoffMultiplier)
    }
    
    return normalInterval
  }, [schemaStatus.isHealthy, schemaStatus.retryCount])
  
  /**
   * Check if polling should be enabled
   * @returns {boolean} Whether components should poll APIs
   */
  const shouldPoll = useCallback(() => {
    if (!isAuthenticated) return false
    
    // Allow polling if schema is healthy or if we haven't exceeded retry limit
    return schemaStatus.isHealthy || schemaStatus.retryCount < 5
  }, [isAuthenticated, schemaStatus.isHealthy, schemaStatus.retryCount])
  
  /**
   * Get user-friendly status message
   * @returns {string} Status message for UI display
   */
  const getStatusMessage = useCallback(() => {
    if (!isAuthenticated) return 'Not authenticated'
    if (schemaStatus.isChecking) return 'Checking database status...'
    if (schemaStatus.isHealthy) return 'Database connection healthy'
    
    if (schemaStatus.missingTables.includes('connection_error')) {
      return 'Database connection error - some features may be unavailable'
    }
    
    if (schemaStatus.missingTables.length > 0) {
      return `Database updating - ${schemaStatus.missingTables.length} table(s) being created`
    }
    
    return 'Database schema incomplete - features may be limited'
  }, [isAuthenticated, schemaStatus])
  
  return {
    ...schemaStatus,
    checkSchemaHealth,
    getPollingInterval,
    shouldPoll,
    getStatusMessage
  }
}