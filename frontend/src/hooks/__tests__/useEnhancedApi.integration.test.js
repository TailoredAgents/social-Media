import { renderHook, act, waitFor } from '@testing-library/react'
import { useEnhancedApi } from '../useEnhancedApi'

// Mock dependencies
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: jest.fn()
}))

jest.mock('../../services/api', () => ({
  setToken: jest.fn(),
  getHealth: jest.fn(),
  getContent: jest.fn(),
  createContent: jest.fn(),
  updateContent: jest.fn(),
  getMetrics: jest.fn()
}))

jest.mock('../useNotifications', () => ({
  useNotifications: jest.fn()
}))

jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn()
}))

import { useAuth } from '../../contexts/AuthContext'
import apiService from '../../services/api'
import { useNotifications } from '../useNotifications'
import { error as logError } from '../../utils/logger.js'

describe('useEnhancedApi Integration Tests', () => {
  const mockUseAuth = useAuth
  const mockUseNotifications = useNotifications
  const mockRefreshToken = jest.fn()
  const mockLogout = jest.fn()
  const mockShowError = jest.fn()
  const mockShowSuccess = jest.fn()
  const mockNotifyApiError = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    
    // Default mocks
    mockUseAuth.mockReturnValue({
      accessToken: 'valid-token',
      refreshToken: mockRefreshToken,
      isAuthenticated: true,
      logout: mockLogout
    })

    mockUseNotifications.mockReturnValue({
      showError: mockShowError,
      showSuccess: mockShowSuccess,
      notifyApiError: mockNotifyApiError
    })

    apiService.getHealth.mockResolvedValue({ status: 'healthy', timestamp: Date.now() })
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('Initialization and Health Checks', () => {
    it('sets token and checks health when authenticated', async () => {
      renderHook(() => useEnhancedApi())

      expect(apiService.setToken).toHaveBeenCalledWith('valid-token')
      
      await waitFor(() => {
        expect(apiService.getHealth).toHaveBeenCalled()
      })
    })

    it('clears token when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        accessToken: null,
        refreshToken: mockRefreshToken,
        isAuthenticated: false,
        logout: mockLogout
      })

      renderHook(() => useEnhancedApi())

      expect(apiService.setToken).toHaveBeenCalledWith(null)
      expect(apiService.getHealth).not.toHaveBeenCalled()
    })

    it('sets connection status based on health check result', async () => {
      const { result } = renderHook(() => useEnhancedApi())

      await waitFor(() => {
        expect(result.current.connectionStatus).toBe('connected')
      })
    })

    it('handles health check failure', async () => {
      apiService.getHealth.mockRejectedValue(new Error('Health check failed'))
      
      const { result } = renderHook(() => useEnhancedApi())

      await waitFor(() => {
        expect(result.current.connectionStatus).toBe('disconnected')
      })
    })
  })

  describe('Enhanced Request Functionality', () => {
    it('successfully executes enhanced request', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'success' })
      
      let response
      await act(async () => {
        response = await result.current.makeEnhancedRequest(mockRequestFn)
      })
      
      expect(mockRequestFn).toHaveBeenCalled()
      expect(response).toEqual({ data: 'success' })
    })

    it('implements retry logic on failure', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ data: 'success after retry' })
      
      let response
      await act(async () => {
        response = await result.current.makeEnhancedRequest(mockRequestFn, { retries: 3 })
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(3)
      expect(response).toEqual({ data: 'success after retry' })
    })

    it('respects retry delay', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn()
        .mockRejectedValueOnce(new Error('Temp failure'))
        .mockResolvedValueOnce({ data: 'delayed success' })
      
      let response
      await act(async () => {
        const requestPromise = result.current.makeEnhancedRequest(mockRequestFn, { 
          retries: 2, 
          retryDelay: 1000 
        })
        
        // Fast forward through retry delay
        jest.advanceTimersByTime(1000)
        
        response = await requestPromise
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(2)
      expect(response).toEqual({ data: 'delayed success' })
    })

    it('implements caching functionality', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'cached data' })
      
      // First request - should call function
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'test-key'
        })
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(1)
      
      // Second request - should use cache
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'test-key'
        })
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(1) // Still only called once
    })

    it('bypasses cache when cache option is false', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'fresh data' })
      
      // First request
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, { cache: false })
      })
      
      // Second request - should not use cache
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, { cache: false })
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(2)
    })
  })

  describe('Error Handling and Notifications', () => {
    it('shows error notification on request failure', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockRejectedValue(new Error('Request failed'))
      
      await act(async () => {
        try {
          await result.current.makeEnhancedRequest(mockRequestFn, { 
            retries: 1,
            showErrorNotification: true 
          })
        } catch (error) {
          // Expected to throw
        }
      })
      
      expect(mockNotifyApiError).toHaveBeenCalled()
    })

    it('handles 401 errors with token refresh', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn()
        .mockRejectedValueOnce(new Error('401 Unauthorized'))
        .mockResolvedValueOnce({ data: 'success after refresh' })
      
      mockRefreshToken.mockResolvedValue('new-token')
      
      let response
      await act(async () => {
        response = await result.current.makeEnhancedRequest(mockRequestFn)
      })
      
      expect(mockRefreshToken).toHaveBeenCalled()
      expect(apiService.setToken).toHaveBeenCalledWith('new-token')
      expect(response).toEqual({ data: 'success after refresh' })
    })

    it('logs out user when token refresh fails', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockRejectedValue(new Error('401 Unauthorized'))
      mockRefreshToken.mockRejectedValue(new Error('Refresh failed'))
      
      await act(async () => {
        try {
          await result.current.makeEnhancedRequest(mockRequestFn)
        } catch (error) {
          // Expected to throw
        }
      })
      
      expect(mockLogout).toHaveBeenCalled()
    })
  })

  describe('Connection Status Management', () => {
    it('updates connection status on successful requests', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'success' })
      
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn)
      })
      
      expect(result.current.connectionStatus).toBe('connected')
    })

    it('updates connection status on network failures', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockRejectedValue(new Error('Network error'))
      
      await act(async () => {
        try {
          await result.current.makeEnhancedRequest(mockRequestFn, { retries: 1 })
        } catch (error) {
          // Expected to throw
        }
      })
      
      expect(result.current.connectionStatus).toBe('disconnected')
    })

    it('provides manual health check function', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      await act(async () => {
        await result.current.checkApiHealth()
      })
      
      expect(apiService.getHealth).toHaveBeenCalled()
      expect(result.current.connectionStatus).toBe('connected')
    })
  })

  describe('Cache Management', () => {
    it('provides cache clearing functionality', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'test' })
      
      // Cache a request
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'clear-test'
        })
      })
      
      // Clear cache
      await act(async () => {
        result.current.clearCache('clear-test')
      })
      
      // Request again - should call function again
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'clear-test'
        })
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(2)
    })

    it('provides clear all cache functionality', async () => {
      const { result } = renderHook(() => useEnhancedApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'test' })
      
      // Cache multiple requests
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'key1'
        })
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'key2'
        })
      })
      
      // Clear all cache
      await act(async () => {
        result.current.clearAllCache()
      })
      
      // Both requests should call function again
      await act(async () => {
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'key1'
        })
        await result.current.makeEnhancedRequest(mockRequestFn, {
          cache: true,
          cacheKey: 'key2'
        })
      })
      
      expect(mockRequestFn).toHaveBeenCalledTimes(4) // 2 initial + 2 after clear
    })
  })
})