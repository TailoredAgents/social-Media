import { describe, it, expect, beforeEach, afterEach, vi } from '@jest/globals'

// Mock dynamic imports
const mockImport = vi.fn()
vi.mock('../pages/Overview', () => ({ default: 'OverviewComponent' }))
vi.mock('../pages/Calendar', () => ({ default: 'CalendarComponent' }))
vi.mock('../pages/Analytics', () => ({ default: 'AnalyticsComponent' }))
vi.mock('../pages/Content', () => ({ default: 'ContentComponent' }))
vi.mock('../pages/MemoryExplorer', () => ({ default: 'MemoryExplorerComponent' }))
vi.mock('../pages/GoalTracking', () => ({ default: 'GoalTrackingComponent' }))
vi.mock('../pages/Settings', () => ({ default: 'SettingsComponent' }))

// Mock requestIdleCallback
global.requestIdleCallback = vi.fn((callback) => {
  setTimeout(callback, 0)
})

describe('PreloadRoutes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Individual preload functions', () => {
    it('should preload Overview page', async () => {
      const { preloadOverview } = await import('../preloadRoutes.js')
      const result = await preloadOverview()
      
      expect(result).toBeDefined()
      expect(result.default).toBe('OverviewComponent')
    })

    it('should preload Calendar page', async () => {
      const { preloadCalendar } = await import('../preloadRoutes.js')
      const result = await preloadCalendar()
      
      expect(result).toBeDefined()
      expect(result.default).toBe('CalendarComponent')
    })

    it('should preload Analytics page', async () => {
      const { preloadAnalytics } = await import('../preloadRoutes.js')
      const result = await preloadAnalytics()
      
      expect(result).toBeDefined()
      expect(result.default).toBe('AnalyticsComponent')
    })
  })

  describe('preloadAfterAuth', () => {
    it('should preload common routes after authentication', async () => {
      const { preloadAfterAuth } = await import('../preloadRoutes.js')
      
      preloadAfterAuth()
      
      expect(requestIdleCallback).toHaveBeenCalledWith(expect.any(Function))
      
      // Execute the callback
      const callback = requestIdleCallback.mock.calls[0][0]
      await callback()
      
      // Advance timers to ensure promises resolve
      vi.runAllTimers()
    })

    it('should use requestIdleCallback for performance', async () => {
      const { preloadAfterAuth } = await import('../preloadRoutes.js')
      
      preloadAfterAuth()
      
      expect(requestIdleCallback).toHaveBeenCalledTimes(1)
      expect(typeof requestIdleCallback.mock.calls[0][0]).toBe('function')
    })
  })

  describe('preloadOnHover', () => {
    it('should preload Overview on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('overview')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('OverviewComponent')
    })

    it('should preload Calendar on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('calendar')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('CalendarComponent')
    })

    it('should preload Analytics on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('analytics')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('AnalyticsComponent')
    })

    it('should preload Content page on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('content')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('ContentComponent')
    })

    it('should preload Memory Explorer on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('memory')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('MemoryExplorerComponent')
    })

    it('should preload Goal Tracking on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('goals')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('GoalTrackingComponent')
    })

    it('should preload Settings on hover', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('settings')
      
      expect(result).toBeDefined()
      expect(result.default).toBe('SettingsComponent')
    })

    it('should handle unknown routes gracefully', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const result = await preloadOnHover('unknown-route')
      
      expect(result).toBeUndefined()
    })

    it('should return resolved promise for unknown routes', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      const promise = preloadOnHover('unknown-route')
      
      expect(promise).toBeInstanceOf(Promise)
      await expect(promise).resolves.toBeUndefined()
    })
  })

  describe('Performance considerations', () => {
    it('should not block main thread during preloading', async () => {
      const { preloadAfterAuth } = await import('../preloadRoutes.js')
      
      const startTime = performance.now()
      preloadAfterAuth()
      const endTime = performance.now()
      
      // Should complete quickly without blocking
      expect(endTime - startTime).toBeLessThan(10)
    })

    it('should handle multiple concurrent preload requests', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      
      const promises = [
        preloadOnHover('overview'),
        preloadOnHover('calendar'),
        preloadOnHover('analytics'),
        preloadOnHover('content')
      ]
      
      const results = await Promise.all(promises)
      
      expect(results).toHaveLength(4)
      results.forEach(result => {
        expect(result).toBeDefined()
        expect(result.default).toBeTruthy()
      })
    })

    it('should handle failed imports gracefully', async () => {
      // Mock a failed import
      vi.doMock('../pages/BrokenPage', () => {
        throw new Error('Import failed')
      })

      const { preloadOnHover } = await import('../preloadRoutes.js')
      
      // Modify the function to import a broken page for testing
      const originalPreload = preloadOnHover
      const testPreload = (route) => {
        if (route === 'broken') {
          return import('../pages/BrokenPage')
        }
        return originalPreload(route)
      }
      
      await expect(testPreload('broken')).rejects.toThrow('Import failed')
    })
  })

  describe('Route mapping completeness', () => {
    const expectedRoutes = [
      'overview',
      'calendar',
      'analytics',
      'content',
      'memory',
      'goals',
      'settings'
    ]

    it('should support all expected routes', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      
      for (const route of expectedRoutes) {
        const result = await preloadOnHover(route)
        expect(result).toBeDefined()
        expect(typeof result.default).toBe('string')
      }
    })

    it('should have consistent naming convention', async () => {
      const { preloadOnHover } = await import('../preloadRoutes.js')
      
      const contentResult = await preloadOnHover('content')
      const memoryResult = await preloadOnHover('memory')
      const goalsResult = await preloadOnHover('goals')
      
      expect(contentResult.default).toBe('ContentComponent')
      expect(memoryResult.default).toBe('MemoryExplorerComponent')
      expect(goalsResult.default).toBe('GoalTrackingComponent')
    })
  })
})