import { renderHook, act, waitFor } from '@testing-library/react'

// Mock logger before importing useEnhancedApi
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
}))

import { useEnhancedApi } from '../useEnhancedApi'

// Mock dependencies
const mockAuthContext = {
  accessToken: 'test-access-token',
  refreshToken: jest.fn().mockResolvedValue('new-token'),
  isAuthenticated: true,
  logout: jest.fn()
}

const mockNotifications = {
  showError: jest.fn(),
  showSuccess: jest.fn(),
  notifyApiError: jest.fn()
}

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

jest.mock('../useNotifications', () => ({
  useNotifications: () => mockNotifications
}))

// Mock API service
jest.mock('../../services/api', () => ({
  __esModule: true,
  default: {
    setToken: jest.fn(),
    getHealth: jest.fn()
  }
}))

describe('useEnhancedApi Hook', () => {
  let mockApiService
  
  beforeEach(() => {
    jest.clearAllMocks()
    // Get the mocked API service
    mockApiService = require('../../services/api').default
    mockApiService.getHealth.mockResolvedValue({ status: 'healthy' })
  })

  it('initializes with token when authenticated', () => {
    renderHook(() => useEnhancedApi())
    
    expect(mockApiService.setToken).toHaveBeenCalledWith('test-access-token')
  })

  it('clears token when not authenticated', () => {
    const notAuthenticatedContext = {
      ...mockAuthContext,
      accessToken: null,
      isAuthenticated: false
    }
    
    jest.mocked(require('../../contexts/AuthContext').useAuth).mockReturnValue(notAuthenticatedContext)
    
    renderHook(() => useEnhancedApi())
    
    expect(mockApiService.setToken).toHaveBeenCalledWith(null)
  })

  it('performs health check on initialization', async () => {
    const { result } = renderHook(() => useEnhancedApi())
    
    await waitFor(() => {
      expect(mockApiService.getHealth).toHaveBeenCalled()
    })
    
    expect(result.current.apiHealth).toEqual({ status: 'healthy' })
  })

  it('sets connection status to disconnected on health check failure', async () => {
    mockApiService.getHealth.mockRejectedValue(new Error('API Error'))
    
    const { result } = renderHook(() => useEnhancedApi())
    
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('disconnected')
    })
  })

  it('handles API request with retry logic', async () => {
    const mockRequest = jest.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: 'success' })
    
    const { result } = renderHook(() => useEnhancedApi())
    
    let requestResult
    await act(async () => {
      requestResult = await result.current.makeEnhancedRequest(mockRequest, {
        retries: 2,
        retryDelay: 100
      })
    })
    
    expect(mockRequest).toHaveBeenCalledTimes(2)
    expect(requestResult).toEqual({ data: 'success' })
  })

  it('handles authentication errors with token refresh', async () => {
    const mockRequest = jest.fn()
      .mockRejectedValueOnce(new Error('401 Unauthorized'))
      .mockResolvedValueOnce({ data: 'success after refresh' })
    
    const { result } = renderHook(() => useEnhancedApi())
    
    let requestResult
    await act(async () => {
      requestResult = await result.current.makeEnhancedRequest(mockRequest)
    })
    
    expect(mockAuthContext.refreshToken).toHaveBeenCalled()
    expect(mockApiService.setToken).toHaveBeenCalledWith('new-token')
    expect(requestResult).toEqual({ data: 'success after refresh' })
  })

  it('handles failed token refresh by logging out user', async () => {
    mockAuthContext.refreshToken.mockRejectedValue(new Error('Refresh failed'))
    
    const mockRequest = jest.fn().mockRejectedValue(new Error('401 Unauthorized'))
    
    const { result } = renderHook(() => useEnhancedApi())
    
    await act(async () => {
      try {
        await result.current.makeEnhancedRequest(mockRequest)
      } catch (error) {
        // Expected to throw
      }
    })
    
    expect(mockAuthContext.logout).toHaveBeenCalled()
    expect(mockNotifications.showError).toHaveBeenCalledWith(
      'Session expired. Please log in again.',
      'Authentication Error'
    )
  })

  it('caches successful requests when enabled', async () => {
    const mockRequest = jest.fn().mockResolvedValue({ data: 'cached data' })
    
    const { result } = renderHook(() => useEnhancedApi())
    
    // First request
    let firstResult
    await act(async () => {
      firstResult = await result.current.makeEnhancedRequest(mockRequest, {
        cache: true,
        cacheKey: 'test-key'
      })
    })
    
    // Second request with same cache key
    let secondResult
    await act(async () => {
      secondResult = await result.current.makeEnhancedRequest(mockRequest, {
        cache: true,
        cacheKey: 'test-key'
      })
    })
    
    expect(mockRequest).toHaveBeenCalledTimes(1) // Only called once due to caching
    expect(firstResult).toEqual(secondResult)
  })

  it('calls success callback on successful request', async () => {
    const mockRequest = jest.fn().mockResolvedValue({ data: 'success' })
    const onSuccess = jest.fn()
    
    const { result } = renderHook(() => useEnhancedApi())
    
    await act(async () => {
      await result.current.makeEnhancedRequest(mockRequest, {
        onSuccess
      })
    })
    
    expect(onSuccess).toHaveBeenCalledWith({ data: 'success' })
  })

  it('calls error callback on failed request', async () => {
    const mockRequest = jest.fn().mockRejectedValue(new Error('API Error'))
    const onError = jest.fn()
    
    const { result } = renderHook(() => useEnhancedApi())
    
    await act(async () => {
      try {
        await result.current.makeEnhancedRequest(mockRequest, {
          onError,
          retries: 0 // Disable retries for this test
        })
      } catch (error) {
        // Expected to throw
      }
    })
    
    expect(onError).toHaveBeenCalledWith(expect.any(Error))
  })
})