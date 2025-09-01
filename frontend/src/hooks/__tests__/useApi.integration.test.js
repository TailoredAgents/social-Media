import { renderHook, act } from '@testing-library/react'
import { useApi } from '../useApi'

// Mock dependencies
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: jest.fn()
}))

jest.mock('../../services/api', () => ({
  setToken: jest.fn(),
  getContent: jest.fn(),
  createContent: jest.fn(),
  updateContent: jest.fn(),
  deleteContent: jest.fn(),
  getMetrics: jest.fn(),
  getGoals: jest.fn(),
  createGoal: jest.fn()
}))

jest.mock('../../utils/logger.js', () => ({
  error: jest.fn()
}))

import { useAuth } from '../../contexts/AuthContext'
import apiService from '../../services/api'
import { error as logError } from '../../utils/logger.js'

describe('useApi Integration Tests', () => {
  const mockUseAuth = useAuth
  const mockRefreshToken = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default mock for useAuth
    mockUseAuth.mockReturnValue({
      accessToken: 'valid-token',
      refreshToken: mockRefreshToken,
      isAuthenticated: true
    })
  })

  describe('Token Management', () => {
    it('sets token when authenticated with valid token', () => {
      renderHook(() => useApi())

      expect(apiService.setToken).toHaveBeenCalledWith('valid-token')
    })

    it('clears token when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        accessToken: null,
        refreshToken: mockRefreshToken,
        isAuthenticated: false
      })

      renderHook(() => useApi())

      expect(apiService.setToken).toHaveBeenCalledWith(null)
    })

    it('updates token when accessToken changes', () => {
      const { rerender } = renderHook(() => useApi())

      expect(apiService.setToken).toHaveBeenCalledWith('valid-token')

      // Simulate token change
      mockUseAuth.mockReturnValue({
        accessToken: 'new-token',
        refreshToken: mockRefreshToken,
        isAuthenticated: true
      })

      rerender()

      expect(apiService.setToken).toHaveBeenCalledWith('new-token')
    })
  })

  describe('makeAuthenticatedRequest', () => {
    it('successfully executes authenticated request', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn = jest.fn().mockResolvedValue({ data: 'success' })
      
      const response = await result.current.makeAuthenticatedRequest(mockRequestFn, 'arg1', 'arg2')
      
      expect(mockRequestFn).toHaveBeenCalledWith('arg1', 'arg2')
      expect(response).toEqual({ data: 'success' })
    })

    it('handles 401 error with token refresh and retry', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn = jest.fn()
        .mockRejectedValueOnce(new Error('401 Unauthorized'))
        .mockResolvedValueOnce({ data: 'success after refresh' })
      
      mockRefreshToken.mockResolvedValue('new-refreshed-token')
      
      const response = await result.current.makeAuthenticatedRequest(mockRequestFn, 'test-arg')
      
      expect(mockRequestFn).toHaveBeenCalledTimes(2)
      expect(mockRefreshToken).toHaveBeenCalled()
      expect(apiService.setToken).toHaveBeenCalledWith('new-refreshed-token')
      expect(response).toEqual({ data: 'success after refresh' })
    })

    it('handles failed token refresh', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn = jest.fn().mockRejectedValue(new Error('401 Unauthorized'))
      mockRefreshToken.mockRejectedValue(new Error('Refresh failed'))
      
      await expect(
        result.current.makeAuthenticatedRequest(mockRequestFn)
      ).rejects.toThrow('Refresh failed')
      
      expect(logError).toHaveBeenCalledWith('Token refresh failed:', expect.any(Error))
    })

    it('passes through non-401 errors without refresh attempt', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn = jest.fn().mockRejectedValue(new Error('500 Server Error'))
      
      await expect(
        result.current.makeAuthenticatedRequest(mockRequestFn)
      ).rejects.toThrow('500 Server Error')
      
      expect(mockRefreshToken).not.toHaveBeenCalled()
    })
  })

  describe('API Service Integration', () => {
    it('provides access to apiService', () => {
      const { result } = renderHook(() => useApi())
      
      expect(result.current.apiService).toBe(apiService)
    })

    it('can make content requests through apiService', async () => {
      const { result } = renderHook(() => useApi())
      
      apiService.getContent.mockResolvedValue({ content: 'test data' })
      
      const response = await result.current.makeAuthenticatedRequest(apiService.getContent)
      
      expect(apiService.getContent).toHaveBeenCalled()
      expect(response).toEqual({ content: 'test data' })
    })

    it('can make metrics requests through apiService', async () => {
      const { result } = renderHook(() => useApi())
      
      apiService.getMetrics.mockResolvedValue({ metrics: 'analytics data' })
      
      const response = await result.current.makeAuthenticatedRequest(apiService.getMetrics, '7d')
      
      expect(apiService.getMetrics).toHaveBeenCalledWith('7d')
      expect(response).toEqual({ metrics: 'analytics data' })
    })

    it('can make goal management requests', async () => {
      const { result } = renderHook(() => useApi())
      
      const newGoal = { title: 'Test Goal', target: 1000 }
      apiService.createGoal.mockResolvedValue({ id: 1, ...newGoal })
      
      const response = await result.current.makeAuthenticatedRequest(apiService.createGoal, newGoal)
      
      expect(apiService.createGoal).toHaveBeenCalledWith(newGoal)
      expect(response).toEqual({ id: 1, ...newGoal })
    })
  })

  describe('Error Handling Edge Cases', () => {
    it('handles malformed 401 error messages', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn = jest.fn()
        .mockRejectedValueOnce(new Error('Request failed with status 401'))
        .mockResolvedValueOnce({ data: 'recovered' })
      
      mockRefreshToken.mockResolvedValue('new-token')
      
      const response = await result.current.makeAuthenticatedRequest(mockRequestFn)
      
      expect(mockRefreshToken).toHaveBeenCalled()
      expect(response).toEqual({ data: 'recovered' })
    })

    it('handles Unauthorized keyword in error message', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn = jest.fn()
        .mockRejectedValueOnce(new Error('Access Unauthorized for this resource'))
        .mockResolvedValueOnce({ data: 'success' })
      
      mockRefreshToken.mockResolvedValue('refreshed-token')
      
      const response = await result.current.makeAuthenticatedRequest(mockRequestFn)
      
      expect(mockRefreshToken).toHaveBeenCalled()
      expect(response).toEqual({ data: 'success' })
    })

    it('handles concurrent requests during token refresh', async () => {
      const { result } = renderHook(() => useApi())
      
      const mockRequestFn1 = jest.fn().mockRejectedValue(new Error('401'))
      const mockRequestFn2 = jest.fn().mockRejectedValue(new Error('401'))
      
      mockRefreshToken.mockResolvedValue('new-token')
      
      // Simulate concurrent requests both getting 401
      const promises = [
        result.current.makeAuthenticatedRequest(mockRequestFn1),
        result.current.makeAuthenticatedRequest(mockRequestFn2)
      ]
      
      await expect(Promise.allSettled(promises)).resolves.toBeDefined()
      
      // Both should attempt refresh (though implementation may optimize this)
      expect(mockRefreshToken).toHaveBeenCalled()
    })
  })

  describe('Authentication State Changes', () => {
    it('handles authentication state change from authenticated to unauthenticated', () => {
      const { rerender } = renderHook(() => useApi())
      
      // Initially authenticated
      expect(apiService.setToken).toHaveBeenCalledWith('valid-token')
      
      // Change to unauthenticated
      mockUseAuth.mockReturnValue({
        accessToken: null,
        refreshToken: mockRefreshToken,
        isAuthenticated: false
      })
      
      rerender()
      
      expect(apiService.setToken).toHaveBeenCalledWith(null)
    })

    it('handles authentication state change from unauthenticated to authenticated', () => {
      // Start unauthenticated
      mockUseAuth.mockReturnValue({
        accessToken: null,
        refreshToken: mockRefreshToken,
        isAuthenticated: false
      })
      
      const { rerender } = renderHook(() => useApi())
      
      expect(apiService.setToken).toHaveBeenCalledWith(null)
      
      // Change to authenticated
      mockUseAuth.mockReturnValue({
        accessToken: 'new-user-token',
        refreshToken: mockRefreshToken,
        isAuthenticated: true
      })
      
      rerender()
      
      expect(apiService.setToken).toHaveBeenCalledWith('new-user-token')
    })
  })
})