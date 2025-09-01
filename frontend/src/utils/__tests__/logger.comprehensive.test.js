import { describe, it, expect, beforeEach, afterEach, vi } from '@jest/globals'

describe('Logger', () => {
  let originalConsoleLog
  let originalConsoleWarn
  let originalConsoleError
  let originalEnv

  beforeEach(() => {
    // Mock console methods
    originalConsoleLog = console.log
    originalConsoleWarn = console.warn
    originalConsoleError = console.error
    console.log = vi.fn()
    console.warn = vi.fn()
    console.error = vi.fn()

    // Store original env
    originalEnv = import.meta.env.MODE

    // Clear module cache to allow re-import with new env
    vi.resetModules()
  })

  afterEach(() => {
    // Restore console methods
    console.log = originalConsoleLog
    console.warn = originalConsoleWarn
    console.error = originalConsoleError

    // Restore env
    import.meta.env.MODE = originalEnv

    vi.clearAllMocks()
  })

  describe('in development mode', () => {
    beforeEach(() => {
      import.meta.env.MODE = 'development'
    })

    it('should log info messages to console', async () => {
      const { logger } = await import('../logger.js')
      logger.info('Test info message', { data: 'test' })
      
      expect(console.log).toHaveBeenCalledWith('[INFO] Test info message', { data: 'test' })
    })

    it('should log warning messages to console', async () => {
      const { logger } = await import('../logger.js')
      logger.warn('Test warning message', 'extra data')
      
      expect(console.warn).toHaveBeenCalledWith('[WARN] Test warning message', 'extra data')
    })

    it('should log error messages to console', async () => {
      const { logger } = await import('../logger.js')
      const error = new Error('Test error')
      logger.error('Test error message', error, 'context')
      
      expect(console.error).toHaveBeenCalledWith('[ERROR] Test error message', error, 'context')
    })

    it('should log debug messages to console', async () => {
      const { logger } = await import('../logger.js')
      logger.debug('Debug info', { debug: true })
      
      expect(console.log).toHaveBeenCalledWith('[DEBUG] Debug info', { debug: true })
    })
  })

  describe('in test mode', () => {
    beforeEach(() => {
      import.meta.env.MODE = 'test'
    })

    it('should not log to console in test mode', async () => {
      const { logger } = await import('../logger.js')
      
      logger.info('Test info')
      logger.warn('Test warning')
      logger.error('Test error', new Error())
      logger.debug('Test debug')
      
      expect(console.log).not.toHaveBeenCalled()
      expect(console.warn).not.toHaveBeenCalled()
      expect(console.error).not.toHaveBeenCalled()
    })
  })

  describe('in production mode', () => {
    beforeEach(() => {
      import.meta.env.MODE = 'production'
    })

    it('should not log to console in production mode', async () => {
      const { logger } = await import('../logger.js')
      
      logger.info('Test info')
      logger.warn('Test warning')
      logger.error('Test error', new Error())
      logger.debug('Test debug')
      
      expect(console.log).not.toHaveBeenCalled()
      expect(console.warn).not.toHaveBeenCalled()
      expect(console.error).not.toHaveBeenCalled()
    })

    it('should have monitoring integration hook for production', async () => {
      const { logger } = await import('../logger.js')
      
      // Spy on the private monitoring method
      const sendToMonitoringSpy = vi.spyOn(logger, '_sendToMonitoring')
      
      logger.error('Production error', new Error('test'))
      
      expect(sendToMonitoringSpy).toHaveBeenCalledWith(
        'error',
        'Production error',
        { error: new Error('test'), args: [] }
      )
    })
  })

  describe('exported convenience functions', () => {
    beforeEach(() => {
      import.meta.env.MODE = 'development'
    })

    it('should export individual logger methods', async () => {
      const { info, warn, error, debug } = await import('../logger.js')
      
      expect(typeof info).toBe('function')
      expect(typeof warn).toBe('function')
      expect(typeof error).toBe('function')
      expect(typeof debug).toBe('function')
    })

    it('should work when called as standalone functions', async () => {
      const { info, warn, error, debug } = await import('../logger.js')
      
      info('Standalone info')
      warn('Standalone warn')
      error('Standalone error', new Error())
      debug('Standalone debug')
      
      expect(console.log).toHaveBeenCalledWith('[INFO] Standalone info')
      expect(console.warn).toHaveBeenCalledWith('[WARN] Standalone warn')
      expect(console.error).toHaveBeenCalledWith('[ERROR] Standalone error', new Error())
      expect(console.log).toHaveBeenCalledWith('[DEBUG] Standalone debug')
    })
  })

  describe('Logger class instantiation', () => {
    it('should create a singleton instance', async () => {
      const { logger } = await import('../logger.js')
      const { logger: logger2 } = await import('../logger.js')
      
      expect(logger).toBe(logger2)
    })

    it('should have isEnabled property set correctly', async () => {
      import.meta.env.MODE = 'development'
      const { logger } = await import('../logger.js')
      
      expect(logger.isEnabled).toBe(true)
    })
  })

  describe('error handling edge cases', () => {
    beforeEach(() => {
      import.meta.env.MODE = 'development'
    })

    it('should handle null/undefined errors gracefully', async () => {
      const { logger } = await import('../logger.js')
      
      expect(() => {
        logger.error('Error with null', null)
        logger.error('Error with undefined', undefined)
      }).not.toThrow()
    })

    it('should handle complex objects in log messages', async () => {
      const { logger } = await import('../logger.js')
      const complexObject = {
        nested: { data: 'value' },
        array: [1, 2, 3],
        fn: () => 'test'
      }
      
      expect(() => {
        logger.info('Complex object log', complexObject)
      }).not.toThrow()
      
      expect(console.log).toHaveBeenCalledWith('[INFO] Complex object log', complexObject)
    })
  })
})