import React, { useState, useEffect } from 'react'
import { 
  ArrowUpIcon, 
  ArrowDownIcon,
  EyeIcon,
  HeartIcon,
  ChatBubbleLeftIcon,
  ShareIcon,
  ClockIcon,
  SignalIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { useRealTimeAnalytics, useRealTimePerformance } from '../../hooks/useRealTimeData'

const RealTimeMetrics = React.memo(function RealTimeMetrics({ timeframe = '7d' }) {
  const [connectionStatus, setConnectionStatus] = useState('connected')
  const { 
    data: analyticsData, 
    isLoading: analyticsLoading, 
    error: analyticsError,
    lastUpdated: analyticsLastUpdated 
  } = useRealTimeAnalytics(timeframe)
  
  const { 
    data: performanceData, 
    isLoading: performanceLoading, 
    error: performanceError,
    lastUpdated: performanceLastUpdated 
  } = useRealTimePerformance()

  // Simulate real-time metrics updates (will be replaced with actual data)
  const [liveMetrics, setLiveMetrics] = useState({
    totalViews: 125000,
    totalEngagement: 8500,
    totalFollowers: 15200,
    engagementRate: 6.8,
    viewsChange: 12.5,
    engagementChange: -2.3,
    followersChange: 8.2,
    engagementRateChange: 1.4,
    activeUsers: 142,
    postsToday: 8,
    avgResponseTime: 1.2
  })

  useEffect(() => {
    // Update connection status based on data freshness
    const now = new Date()
    const lastUpdate = analyticsLastUpdated || performanceLastUpdated
    
    if (!lastUpdate) {
      setConnectionStatus('connecting')
    } else {
      const timeDiff = now - lastUpdate
      if (timeDiff > 300000) { // 5 minutes
        setConnectionStatus('stale')
      } else if (timeDiff > 60000) { // 1 minute
        setConnectionStatus('delayed')
      } else {
        setConnectionStatus('connected')
      }
    }
  }, [analyticsLastUpdated, performanceLastUpdated])

  // Simulate real-time updates for demo (remove when real data is connected)
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveMetrics(prev => ({
        ...prev,
        totalViews: prev.totalViews + Math.floor(Math.random() * 50) + 10,
        totalEngagement: prev.totalEngagement + Math.floor(Math.random() * 10) + 1,
        activeUsers: Math.floor(Math.random() * 50) + 100,
        avgResponseTime: Math.random() * 2 + 0.5
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toLocaleString()
  }

  const getChangeIcon = (change) => {
    return change >= 0 ? (
      <ArrowUpIcon className="h-4 w-4 text-green-500" />
    ) : (
      <ArrowDownIcon className="h-4 w-4 text-red-500" />
    )
  }

  const getChangeColor = (change) => {
    return change >= 0 ? 'text-green-600' : 'text-red-600'
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600'
      case 'delayed': return 'text-yellow-600'
      case 'stale': return 'text-red-600'
      case 'connecting': return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <SignalIcon className="h-4 w-4" />
      case 'delayed': return <ClockIcon className="h-4 w-4" />
      case 'stale': return <ExclamationTriangleIcon className="h-4 w-4" />
      case 'connecting': return <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
      default: return <SignalIcon className="h-4 w-4" />
    }
  }

  const getLastUpdatedText = () => {
    const lastUpdate = analyticsLastUpdated || performanceLastUpdated
    if (!lastUpdate) return 'Never updated'
    
    const now = new Date()
    const diffMs = now - lastUpdate
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    
    if (diffSeconds < 30) return 'Just updated'
    if (diffSeconds < 60) return `${diffSeconds}s ago`
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    return lastUpdate.toLocaleTimeString()
  }

  return (
    <div className="space-y-6">
      {/* Connection Status Header */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-2 ${getConnectionStatusColor()}`}>
              {getConnectionStatusIcon()}
              <span className="text-sm font-medium capitalize">{connectionStatus}</span>
            </div>
            <div className="text-sm text-gray-500">
              Last updated: {getLastUpdatedText()}
            </div>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>{liveMetrics.activeUsers} active users</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>{liveMetrics.postsToday} posts today</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>{liveMetrics.avgResponseTime.toFixed(1)}s avg response</span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-Time Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Views</p>
              <p className="text-3xl font-bold text-gray-900">
                {formatNumber(liveMetrics.totalViews)}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <EyeIcon className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="flex items-center mt-4">
            {getChangeIcon(liveMetrics.viewsChange)}
            <span className={`text-sm font-medium ml-1 ${getChangeColor(liveMetrics.viewsChange)}`}>
              {Math.abs(liveMetrics.viewsChange)}%
            </span>
            <span className="text-sm text-gray-500 ml-1">vs last period</span>
          </div>
          
          {/* Live indicator */}
          <div className="absolute top-2 right-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Live data"></div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Engagement</p>
              <p className="text-3xl font-bold text-gray-900">
                {formatNumber(liveMetrics.totalEngagement)}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <HeartIcon className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <div className="flex items-center mt-4">
            {getChangeIcon(liveMetrics.engagementChange)}
            <span className={`text-sm font-medium ml-1 ${getChangeColor(liveMetrics.engagementChange)}`}>
              {Math.abs(liveMetrics.engagementChange)}%
            </span>
            <span className="text-sm text-gray-500 ml-1">vs last period</span>
          </div>
          
          {/* Live indicator */}
          <div className="absolute top-2 right-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Live data"></div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Followers</p>
              <p className="text-3xl font-bold text-gray-900">
                {formatNumber(liveMetrics.totalFollowers)}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <ChatBubbleLeftIcon className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <div className="flex items-center mt-4">
            {getChangeIcon(liveMetrics.followersChange)}
            <span className={`text-sm font-medium ml-1 ${getChangeColor(liveMetrics.followersChange)}`}>
              {Math.abs(liveMetrics.followersChange)}%
            </span>
            <span className="text-sm text-gray-500 ml-1">vs last period</span>
          </div>
          
          {/* Live indicator */}
          <div className="absolute top-2 right-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Live data"></div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Engagement Rate</p>
              <p className="text-3xl font-bold text-gray-900">
                {liveMetrics.engagementRate}%
              </p>
            </div>
            <div className="p-3 bg-orange-100 rounded-full">
              <ShareIcon className="h-6 w-6 text-orange-600" />
            </div>
          </div>
          <div className="flex items-center mt-4">
            {getChangeIcon(liveMetrics.engagementRateChange)}
            <span className={`text-sm font-medium ml-1 ${getChangeColor(liveMetrics.engagementRateChange)}`}>
              {Math.abs(liveMetrics.engagementRateChange)}%
            </span>
            <span className="text-sm text-gray-500 ml-1">vs last period</span>
          </div>
          
          {/* Live indicator */}
          <div className="absolute top-2 right-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Live data"></div>
          </div>
        </div>
      </div>

      {/* Error States */}
      {(analyticsError || performanceError) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
            <span className="text-red-700 font-medium">Data Connection Issues</span>
          </div>
          <p className="text-red-600 text-sm mt-2">
            Some real-time data may be unavailable. Retrying connection...
          </p>
        </div>
      )}
    </div>
  )
})

export default RealTimeMetrics