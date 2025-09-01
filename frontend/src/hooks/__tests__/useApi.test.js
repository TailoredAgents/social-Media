import { renderHook, act } from '@testing-library/react'

// Mock logger before importing useApi
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
}))

import { useApi } from '../useApi'

// Mock the auth context
const mockAuthContext = {
  accessToken: 'test-access-token',
  refreshToken: jest.fn(),
  isAuthenticated: true
}

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

// Mock the API service
jest.mock('../../services/api', () => ({
  __esModule: true,
  default: {
    setToken: jest.fn(),
    get: jest.fn(),
    post: jest.fn()
  }
}))

describe('useApi Hook', () => {
  let mockApiService
  
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiService = require('../../services/api').default
  })

  it('sets token when authenticated', () => {
    renderHook(() => useApi())
    
    expect(mockApiService.setToken).toHaveBeenCalledWith('test-access-token')
  })

  it('clears token when not authenticated', () => {
    mockAuthContext.isAuthenticated = false
    mockAuthContext.accessToken = null
    
    renderHook(() => useApi())
    
    expect(mockApiService.setToken).toHaveBeenCalledWith(null)
  })

  it('updates token when accessToken changes', () => {
    const { rerender } = renderHook(() => useApi())
    
    expect(mockApiService.setToken).toHaveBeenCalledWith('test-access-token')
    
    // Simulate token change
    mockAuthContext.accessToken = 'new-access-token'
    rerender()
    
    expect(mockApiService.setToken).toHaveBeenCalledWith('new-access-token')
  })

  it('makes authenticated request successfully', async () => {
    const { result } = renderHook(() => useApi())
    
    const mockRequestFn = jest.fn().mockResolvedValue({ data: 'success' })
    
    await act(async () => {
      const response = await result.current.makeAuthenticatedRequest(mockRequestFn, 'arg1', 'arg2')
      expect(response).toEqual({ data: 'success' })
      expect(mockRequestFn).toHaveBeenCalledWith('arg1', 'arg2')
    })
  })

  it('refreshes token and retries on 401 error', async () => {
    const { result } = renderHook(() => useApi())
    
    const mockRequestFn = jest.fn()
      .mockRejectedValueOnce(new Error('401 Unauthorized'))
      .mockResolvedValueOnce({ data: 'success after refresh' })
    
    mockAuthContext.refreshToken.mockResolvedValue('new-refreshed-token')
    
    await act(async () => {
      const response = await result.current.makeAuthenticatedRequest(mockRequestFn)
      
      expect(response).toEqual({ data: 'success after refresh' })
      expect(mockAuthContext.refreshToken).toHaveBeenCalledTimes(1)
      expect(mockApiService.setToken).toHaveBeenCalledWith('new-refreshed-token')
      expect(mockRequestFn).toHaveBeenCalledTimes(2)
    })
  })

  it('throws error if token refresh fails', async () => {
    const { result } = renderHook(() => useApi())
    
    const mockRequestFn = jest.fn().mockRejectedValue(new Error('401 Unauthorized'))
    mockAuthContext.refreshToken.mockRejectedValue(new Error('Refresh failed'))
    
    await act(async () => {
      await expect(
        result.current.makeAuthenticatedRequest(mockRequestFn)
      ).rejects.toThrow('Refresh failed')
    })
  })

  it('throws original error for non-401 errors', async () => {
    const { result } = renderHook(() => useApi())
    
    const mockRequestFn = jest.fn().mockRejectedValue(new Error('500 Server Error'))
    
    await act(async () => {
      await expect(
        result.current.makeAuthenticatedRequest(mockRequestFn)
      ).rejects.toThrow('500 Server Error')
    })
    
    expect(mockAuthContext.refreshToken).not.toHaveBeenCalled()
  })

  it('returns apiService instance', () => {
    const { result } = renderHook(() => useApi())
    
    expect(result.current.apiService).toBe(mockApiService)
  })
})