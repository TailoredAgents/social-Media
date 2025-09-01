import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import InfiniteScroll from 'react-infinite-scroll-component'

// Empty alerts data - replace with API calls
const generateEmptyAlerts = (startIndex = 0, count = 0) => {
  return []
}

// Alert Card Component
const AlertCard = ({ alert, onAction, onMarkAsRead, darkMode }) => {
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'border-l-red-500'
      case 'medium': return 'border-l-yellow-500'
      case 'low': return 'border-l-green-500'
      default: return 'border-l-gray-500'
    }
  }

  const getColorClasses = (color) => {
    switch (color) {
      case 'green': return 'bg-green-50 text-green-800 border-green-200'
      case 'yellow': return 'bg-yellow-50 text-yellow-800 border-yellow-200'
      case 'blue': return 'bg-blue-50 text-blue-800 border-blue-200'
      case 'red': return 'bg-red-50 text-red-800 border-red-200'
      case 'purple': return 'bg-purple-50 text-purple-800 border-purple-200'
      default: return 'bg-gray-50 text-gray-800 border-gray-200'
    }
  }

  const formatTimeAgo = (timestamp) => {
    const now = new Date()
    const diff = now - timestamp
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'Just now'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className={`p-4 rounded-lg border-l-4 ${getPriorityColor(alert.priority)} ${
        darkMode 
          ? `bg-gray-800/80 border-r border-t border-b border-gray-700 ${!alert.read ? 'bg-gray-800' : ''}` 
          : `bg-white/80 border-r border-t border-b border-gray-200 ${!alert.read ? 'bg-blue-50/30' : ''}`
      } backdrop-blur-sm shadow-sm hover:shadow-md transition-all cursor-pointer`}
      onClick={() => !alert.read && onMarkAsRead(alert.id)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{alert.icon}</span>
          <div>
            <h3 className={`font-semibold ${
              darkMode ? 'text-white' : 'text-gray-900'
            } ${!alert.read ? 'font-bold' : ''}`}>
              {alert.title}
            </h3>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`px-2 py-1 rounded-full text-xs ${getColorClasses(alert.color)}`}>
                {alert.platform}
              </span>
              <span className={`text-xs ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                {formatTimeAgo(alert.timestamp)}
              </span>
              {!alert.read && (
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            alert.priority === 'high' ? 'bg-red-100 text-red-800' :
            alert.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            {alert.priority}
          </span>
        </div>
      </div>

      <p className={`text-sm mb-4 ${
        darkMode ? 'text-gray-300' : 'text-gray-700'
      }`}>
        {alert.message}
      </p>

      <div className="flex flex-wrap gap-2">
        {alert.actions.map((action, index) => (
          <button
            key={index}
            onClick={(e) => {
              e.stopPropagation()
              onAction(alert.id, action)
            }}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              index === 0
                ? 'bg-teal-500 text-white hover:bg-teal-600'
                : darkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {action}
          </button>
        ))}
      </div>
    </motion.div>
  )
}

// Filter Component
const AlertFilters = ({ filters, setFilters, darkMode }) => {
  const filterOptions = {
    type: ['All', 'Engagement', 'Approval', 'Milestone', 'Error', 'Trending'],
    priority: ['All', 'High', 'Medium', 'Low'],
    platform: ['All', 'LinkedIn', 'Twitter', 'Instagram', 'Facebook'],
    status: ['All', 'Unread', 'Read']
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className={`p-4 rounded-xl backdrop-blur-md ${
        darkMode ? 'bg-gray-800/80' : 'bg-white/80'
      } border border-gray-200/20 shadow-lg`}
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(filterOptions).map(([key, options]) => (
          <div key={key}>
            <label className={`block text-sm font-medium mb-1 capitalize ${
              darkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              {key}
            </label>
            <select
              value={filters[key]}
              onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
              className={`w-full p-2 rounded-lg border text-sm ${
                darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-900'
              } focus:outline-none focus:ring-2 focus:ring-teal-500`}
            >
              {options.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// Main Alerts Feed Component
const AlertsFeed = ({ darkMode, searchQuery }) => {
  const [alerts, setAlerts] = useState([])
  const [hasMore, setHasMore] = useState(true)
  const [filters, setFilters] = useState({
    type: 'All',
    priority: 'All',
    platform: 'All',
    status: 'All'
  })

  // Initialize alerts
  useEffect(() => {
    const initialAlerts = generateEmptyAlerts(0, 20)
    setAlerts(initialAlerts)
  }, [])

  // Load more alerts for infinite scroll
  const loadMoreAlerts = useCallback(() => {
    setTimeout(() => {
      const newAlerts = generateEmptyAlerts(alerts.length, 10)
      setAlerts(prev => [...prev, ...newAlerts])
      
      // Simulate end of data after 100 items
      if (alerts.length >= 90) {
        setHasMore(false)
      }
    }, 1000)
  }, [alerts.length])

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    const matchesType = filters.type === 'All' || alert.type === filters.type.toLowerCase()
    const matchesPriority = filters.priority === 'All' || alert.priority === filters.priority.toLowerCase()
    const matchesPlatform = filters.platform === 'All' || alert.platform === filters.platform
    const matchesStatus = filters.status === 'All' || 
      (filters.status === 'Read' && alert.read) || 
      (filters.status === 'Unread' && !alert.read)
    const matchesSearch = !searchQuery || 
      alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.message.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesType && matchesPriority && matchesPlatform && matchesStatus && matchesSearch
  })

  // Handle alert actions
  const handleAction = (alertId, action) => {
    console.log(`Action "${action}" performed on alert ${alertId}`)
    // Here you would typically make an API call
    
    // If action is dismissive, remove the alert
    if (['Approve', 'Reject', 'Retry'].includes(action)) {
      setAlerts(prev => prev.filter(alert => alert.id !== alertId))
    }
  }

  // Mark alert as read
  const markAsRead = (alertId) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId ? { ...alert, read: true } : alert
      )
    )
  }

  // Mark all as read
  const markAllAsRead = () => {
    setAlerts(prev => prev.map(alert => ({ ...alert, read: true })))
  }

  // Stats
  const unreadCount = alerts.filter(alert => !alert.read).length
  const highPriorityCount = alerts.filter(alert => alert.priority === 'high').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className={`text-3xl font-bold ${
            darkMode ? 'text-white' : 'text-gray-900'
          }`}>
            Alerts Feed
          </h1>
          <p className={`text-lg ${
            darkMode ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Stay updated with real-time notifications and alerts
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-center">
            <p className={`text-2xl font-bold ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              {unreadCount}
            </p>
            <p className={`text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Unread
            </p>
          </div>
          <div className="text-center">
            <p className={`text-2xl font-bold text-red-500`}>
              {highPriorityCount}
            </p>
            <p className={`text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              High Priority
            </p>
          </div>
          <button
            onClick={markAllAsRead}
            className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
          >
            Mark All Read
          </button>
        </div>
      </motion.div>

      {/* Filters */}
      <AlertFilters filters={filters} setFilters={setFilters} darkMode={darkMode} />

      {/* Alerts List with Infinite Scroll */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <InfiniteScroll
          dataLength={filteredAlerts.length}
          next={loadMoreAlerts}
          hasMore={hasMore}
          loader={
            <div className="flex justify-center py-4">
              <motion.div
                className="w-8 h-8 border-4 border-teal-200 border-t-teal-600 rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
            </div>
          }
          endMessage={
            <p className={`text-center py-4 ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              No more alerts to load
            </p>
          }
          height={600}
          className="space-y-4"
        >
          <AnimatePresence>
            {filteredAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAction={handleAction}
                onMarkAsRead={markAsRead}
                darkMode={darkMode}
              />
            ))}
          </AnimatePresence>
        </InfiniteScroll>

        {filteredAlerts.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`text-center py-12 ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}
          >
            <div className="text-6xl mb-4">🔔</div>
            <p className="text-lg font-medium mb-2">No alerts found</p>
            <p>Try adjusting your filters or check back later</p>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}

export default AlertsFeed