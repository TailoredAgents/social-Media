// Preload critical routes for better performance
export const preloadOverview = () => import('../pages/Overview')
export const preloadCalendar = () => import('../pages/Calendar')
export const preloadAnalytics = () => import('../pages/Analytics')

// Preload based on user navigation patterns
export const preloadAfterAuth = () => {
  // Preload most commonly accessed routes after authentication
  requestIdleCallback(() => {
    preloadOverview()
    preloadCalendar()
  })
}

export const preloadOnHover = (route) => {
  // Preload when user hovers over navigation items
  switch (route) {
    case 'overview':
      return preloadOverview()
    case 'calendar':
      return preloadCalendar()
    case 'analytics':
      return preloadAnalytics()
    case 'content':
      return import('../pages/Content')
    case 'memory':
      return import('../pages/MemoryExplorer')
    case 'goals':
      return import('../pages/GoalTracking')
    case 'settings':
      return import('../pages/Settings')
    default:
      return Promise.resolve()
  }
}