import { useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'
import { error as logError } from '../utils/logger.js'

export const useApi = () => {
  const { accessToken, refreshToken, isAuthenticated } = useAuth()

  useEffect(() => {
    if (accessToken && isAuthenticated) {
      apiService.setToken(accessToken)
    } else {
      apiService.setToken(null)
    }
  }, [accessToken, isAuthenticated])

  const makeAuthenticatedRequest = async (requestFn, ...args) => {
    try {
      return await requestFn(...args)
    } catch (error) {
      // If token expired, try to refresh and retry
      if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        try {
          const newToken = await refreshToken()
          apiService.setToken(newToken)
          return await requestFn(...args)
        } catch (refreshError) {
          logError('Token refresh failed:', refreshError)
          throw refreshError
        }
      }
      throw error
    }
  }

  return {
    apiService,
    makeAuthenticatedRequest
  }
}