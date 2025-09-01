import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock logger before importing useRealTimeData
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
}))

// Mock the Auth context first
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    accessToken: 'test-token',
    refreshToken: jest.fn(),
    isAuthenticated: true
  })
}))

import { useRealTimeData } from '../useRealTimeData'

// Mock the API service
jest.mock('../../services/api.js', () => ({
  __esModule: true,
  default: {
    getMetrics: jest.fn(),
    getAnalytics: jest.fn(),
    getPerformanceMetrics: jest.fn(),
    getNotifications: jest.fn()
  }
}))

// Mock the logger
jest.mock('../../utils/logger.js', () => ({
  info: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  warn: jest.fn()
}))

import apiService from '../../services/api.js'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })
  
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useRealTimeData Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('initializes with default state', () => {
    const { result } = renderHook(() => useRealTimeData('metrics'), {
      wrapper: createWrapper()
    })

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(true)
    expect(result.current.error).toBeNull()
    expect(result.current.isConnected).toBe(false)
    expect(result.current.lastUpdated).toBeNull()
  })

  it('fetches initial data on mount', async () => {
    const mockData = { views: 1000, clicks: 50 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRealTimeData('metrics'), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockData)
    expect(result.current.error).toBeNull()
    expect(apiService.getMetrics).toHaveBeenCalledTimes(1)
  })

  it('handles API errors gracefully', async () => {
    const error = new Error('API Error')
    apiService.getMetrics.mockRejectedValue(error)

    const { result } = renderHook(() => useRealTimeData('metrics'), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toBeNull()
    expect(result.current.error).toEqual(error)
  })

  it('sets up polling with specified interval', async () => {
    const mockData = { views: 1000, clicks: 50 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRealTimeData('metrics', { 
      pollingInterval: 5000 
    }), {
      wrapper: createWrapper()
    })

    // Initial fetch
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(apiService.getMetrics).toHaveBeenCalledTimes(1)

    // Fast-forward time to trigger polling
    act(() => {
      jest.advanceTimersByTime(5000)
    })

    await waitFor(() => {
      expect(apiService.getMetrics).toHaveBeenCalledTimes(2)
    })
  })

  it('handles different data types correctly', async () => {
    // Test analytics data
    const mockAnalytics = { period: '7d', data: [1, 2, 3] }
    apiService.getAnalytics.mockResolvedValue(mockAnalytics)

    const { result } = renderHook(() => useRealTimeData('analytics'), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.data).toEqual(mockAnalytics)
    })

    expect(apiService.getAnalytics).toHaveBeenCalledWith('7d')
  })

  it('handles performance data with platform filter', async () => {
    const mockPerformance = { platform: 'twitter', metrics: {} }
    apiService.getPerformanceMetrics.mockResolvedValue(mockPerformance)

    const { result } = renderHook(() => useRealTimeData('performance', {
      platform: 'twitter'
    }), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.data).toEqual(mockPerformance)
    })

    expect(apiService.getPerformanceMetrics).toHaveBeenCalledWith('twitter')
  })

  it('provides manual refresh functionality', async () => {
    const initialData = { views: 1000 }
    const refreshedData = { views: 1500 }
    
    apiService.getMetrics
      .mockResolvedValueOnce(initialData)
      .mockResolvedValueOnce(refreshedData)

    const { result } = renderHook(() => useRealTimeData('metrics'), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.data).toEqual(initialData)
    })

    // Manual refresh
    act(() => {
      result.current.refresh()
    })

    await waitFor(() => {
      expect(result.current.data).toEqual(refreshedData)
    })

    expect(apiService.getMetrics).toHaveBeenCalledTimes(2)
  })

  it('tracks connection status', async () => {
    const mockData = { views: 1000 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRealTimeData('metrics'), {
      wrapper: createWrapper()
    })

    // Initially not connected
    expect(result.current.isConnected).toBe(false)

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('updates lastUpdated timestamp', async () => {
    const mockData = { views: 1000 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRealTimeData('metrics'), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.lastUpdated).toBeInstanceOf(Date)
    })

    const firstUpdate = result.current.lastUpdated

    // Trigger refresh and check timestamp updated
    act(() => {
      result.current.refresh()
    })

    await waitFor(() => {
      expect(result.current.lastUpdated).not.toEqual(firstUpdate)
    })
  })

  it('handles WebSocket connection simulation', async () => {
    const mockData = { views: 1000 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRealTimeData('metrics', {
      enableWebSocket: true
    }), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    // In a real implementation, this would test WebSocket events
    // For now, we test that the option is passed through
    expect(result.current.data).toEqual(mockData)
  })

  it('cleans up on unmount', async () => {
    const mockData = { views: 1000 }
    apiService.getMetrics.mockResolvedValue(mockData)
    
    const clearIntervalSpy = jest.spyOn(global, 'clearInterval')

    const { result, unmount } = renderHook(() => useRealTimeData('metrics', {
      pollingInterval: 1000
    }), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    unmount()

    expect(clearIntervalSpy).toHaveBeenCalled()
  })

  it('pauses and resumes polling', async () => {
    const mockData = { views: 1000 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result } = renderHook(() => useRealTimeData('metrics', {
      pollingInterval: 1000
    }), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Pause polling
    act(() => {
      result.current.pause()
    })

    expect(result.current.isPaused).toBe(true)

    // Advance time - should not trigger new fetch
    const callCountAfterPause = apiService.getMetrics.mock.calls.length
    
    act(() => {
      jest.advanceTimersByTime(2000)
    })

    expect(apiService.getMetrics).toHaveBeenCalledTimes(callCountAfterPause)

    // Resume polling
    act(() => {
      result.current.resume()
    })

    expect(result.current.isPaused).toBe(false)

    // Now polling should work again
    act(() => {
      jest.advanceTimersByTime(1000)
    })

    await waitFor(() => {
      expect(apiService.getMetrics).toHaveBeenCalledTimes(callCountAfterPause + 1)
    })
  })

  it('handles configuration changes', async () => {
    const mockData = { views: 1000 }
    apiService.getMetrics.mockResolvedValue(mockData)

    const { result, rerender } = renderHook(({ interval }) => 
      useRealTimeData('metrics', { pollingInterval: interval }), {
      wrapper: createWrapper(),
      initialProps: { interval: 1000 }
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Change polling interval
    rerender({ interval: 2000 })

    // Verify the new interval is applied
    const initialCallCount = apiService.getMetrics.mock.calls.length

    act(() => {
      jest.advanceTimersByTime(1000)
    })

    // Should not call with 1000ms anymore
    expect(apiService.getMetrics).toHaveBeenCalledTimes(initialCallCount)

    act(() => {
      jest.advanceTimersByTime(1000) // Total 2000ms
    })

    // Should call with 2000ms interval
    await waitFor(() => {
      expect(apiService.getMetrics).toHaveBeenCalledTimes(initialCallCount + 1)
    })
  })

  it('handles notifications data type', async () => {
    const mockNotifications = [
      { id: 1, message: 'Test notification', read: false }
    ]
    apiService.getNotifications.mockResolvedValue(mockNotifications)

    const { result } = renderHook(() => useRealTimeData('notifications'), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.data).toEqual(mockNotifications)
    })

    expect(apiService.getNotifications).toHaveBeenCalledTimes(1)
  })
})