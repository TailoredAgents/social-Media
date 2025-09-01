// Production-ready logging utility with backend monitoring integration
// Console logs in development, forwards all logs to backend monitoring service in production

const isDevelopment = import.meta.env.MODE === 'development'
const isTest = import.meta.env.MODE === 'test'

class Logger {
  constructor() {
    this.isEnabled = isDevelopment && !isTest
  }

  info(message, ...args) {
    if (this.isEnabled) {
      console.log(`[INFO] ${message}`, ...args)
    }
    // Send to monitoring service in production (fire and forget)
    this._sendToMonitoring('info', message, args).catch(() => {})
  }

  warn(message, ...args) {
    if (this.isEnabled) {
      console.warn(`[WARN] ${message}`, ...args)
    }
    // Send to monitoring service (fire and forget)
    this._sendToMonitoring('warn', message, args).catch(() => {})
  }

  error(message, error, ...args) {
    if (this.isEnabled) {
      console.error(`[ERROR] ${message}`, error, ...args)
    }
    // Always log errors for monitoring in production (fire and forget)
    this._sendToMonitoring('error', message, { error, args }).catch(() => {})
  }

  debug(message, ...args) {
    if (this.isEnabled) {
      console.log(`[DEBUG] ${message}`, ...args)
    }
    // Debug logs only in development
  }

  async _sendToMonitoring(level, message, data) {
    // Send logs to backend monitoring service in production
    if (isDevelopment) {
      return // Only send in production
    }
    
    try {
      const logEntry = {
        level,
        message: typeof message === 'string' ? message : JSON.stringify(message),
        data: data || {},
        timestamp: new Date().toISOString(),
        session_id: this._getSessionId(),
        url: typeof window !== 'undefined' ? window.location.href : '',
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : ''
      }
      
      // Send to backend monitoring endpoint
      const response = await fetch('/api/monitoring/frontend-logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logEntry)
      })
      
      if (!response.ok) {
        // Silently fail - don't create log loops
        console.warn(`Failed to send log to backend: ${response.status}`)
      }
    } catch (error) {
      // Silently fail to prevent infinite loops
      console.warn('Failed to send log to monitoring service:', error.message)
    }
  }

  _mapLevelToSentryLevel(level) {
    const levelMap = {
      'error': 'error',
      'warn': 'warning', 
      'info': 'info',
      'debug': 'debug'
    }
    return levelMap[level] || 'info'
  }

  _sendToCustomEndpoint(level, message, data) {
    // Alternative endpoint for custom monitoring services (if needed)
    // Currently using _sendToMonitoring for backend integration
    return
  }

  _getSessionId() {
    // Simple session ID generation for tracking
    if (typeof window !== 'undefined') {
      let sessionId = sessionStorage.getItem('logger-session-id')
      if (!sessionId) {
        sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2)
        sessionStorage.setItem('logger-session-id', sessionId)
      }
      return sessionId
    }
    return 'unknown'
  }
}

// Export singleton instance
export const logger = new Logger()

// Export logger methods for convenience - defensive destructuring
export const info = (...args) => logger?.info?.(...args) || console.log(...args)
export const warn = (...args) => logger?.warn?.(...args) || console.warn(...args)
export const error = (...args) => logger?.error?.(...args) || console.error(...args)
export const debug = (...args) => logger?.debug?.(...args) || console.log(...args)

export default logger