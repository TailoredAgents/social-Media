import React, { useState } from 'react'
import { 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  XMarkIcon,
  BellIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline'

const alertTypeConfig = {
  error: {
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    iconColor: 'text-red-500',
    icon: XCircleIcon,
    actionBg: 'bg-red-100 hover:bg-red-200',
    actionText: 'text-red-800'
  },
  warning: {
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800',
    iconColor: 'text-yellow-500',
    icon: ExclamationTriangleIcon,
    actionBg: 'bg-yellow-100 hover:bg-yellow-200',
    actionText: 'text-yellow-800'
  },
  info: {
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    iconColor: 'text-blue-500',
    icon: InformationCircleIcon,
    actionBg: 'bg-blue-100 hover:bg-blue-200',
    actionText: 'text-blue-800'
  },
  success: {
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    iconColor: 'text-green-500',
    icon: CheckCircleIcon,
    actionBg: 'bg-green-100 hover:bg-green-200',
    actionText: 'text-green-800'
  },
  insight: {
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-800',
    iconColor: 'text-purple-500',
    icon: LightBulbIcon,
    actionBg: 'bg-purple-100 hover:bg-purple-200',
    actionText: 'text-purple-800'
  }
}

const PerformanceAlert = React.memo(function PerformanceAlert({ 
  type = 'info', 
  title, 
  message, 
  action, 
  onAction,
  onDismiss,
  dismissible = true,
  persistent = false,
  timestamp = null,
  metric = null,
  threshold = null,
  currentValue = null
}) {
  const [isVisible, setIsVisible] = useState(true)
  
  if (!isVisible) return null
  
  const config = alertTypeConfig[type] || alertTypeConfig.info
  const AlertIcon = config.icon
  
  const handleDismiss = () => {
    setIsVisible(false)
    if (onDismiss) onDismiss()
  }
  
  const handleAction = () => {
    if (onAction) onAction()
  }
  
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return null
    const now = new Date()
    const alertTime = new Date(timestamp)
    const diffMs = now - alertTime
    const diffMinutes = Math.floor(diffMs / 60000)
    
    if (diffMinutes < 1) return 'Just now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`
    return alertTime.toLocaleDateString()
  }
  
  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4 transition-all duration-300 hover:shadow-md`}>
      <div className="flex items-start space-x-3">
        {/* Alert Icon */}
        <div className={`flex-shrink-0 ${config.iconColor}`}>
          <AlertIcon className="h-5 w-5" />
        </div>
        
        {/* Alert Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {/* Title and Message */}
              <h4 className={`text-sm font-medium ${config.textColor}`}>
                {title}
              </h4>
              {message && (
                <p className={`mt-1 text-sm ${config.textColor} opacity-90`}>
                  {message}
                </p>
              )}
              
              {/* Metric Details */}
              {metric && (
                <div className={`mt-2 text-xs ${config.textColor} opacity-75`}>
                  <div className="flex items-center space-x-4">
                    <span><strong>Metric:</strong> {metric}</span>
                    {currentValue && <span><strong>Current:</strong> {currentValue}</span>}
                    {threshold && <span><strong>Threshold:</strong> {threshold}</span>}
                  </div>
                </div>
              )}
              
              {/* Timestamp */}
              {timestamp && (
                <div className={`mt-1 text-xs ${config.textColor} opacity-60 flex items-center space-x-1`}>
                  <BellIcon className="h-3 w-3" />
                  <span>{formatTimestamp(timestamp)}</span>
                </div>
              )}
            </div>
            
            {/* Dismiss Button */}
            {dismissible && !persistent && (
              <button
                onClick={handleDismiss}
                className={`ml-3 flex-shrink-0 ${config.iconColor} hover:opacity-75 transition-opacity`}
                aria-label="Dismiss alert"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            )}
          </div>
          
          {/* Action Button */}
          {action && (
            <div className="mt-3">
              <button
                onClick={handleAction}
                className={`text-xs font-medium px-3 py-1 rounded-md transition-colors ${config.actionBg} ${config.actionText}`}
              >
                {action}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
})

export default PerformanceAlert

// Specialized alert components for common use cases
export function PerformanceMetricAlert({ metric, currentValue, threshold, comparison = 'above', ...props }) {
  const isTriggered = comparison === 'above' ? currentValue > threshold : currentValue < threshold
  const alertType = isTriggered ? 'warning' : 'success'
  
  return (
    <PerformanceAlert
      type={alertType}
      metric={metric}
      currentValue={currentValue}
      threshold={threshold}
      timestamp={new Date().toISOString()}
      {...props}
    />
  )
}

export function SystemHealthAlert({ component, status, uptime, ...props }) {
  const getAlertType = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy': return 'success'
      case 'degraded': return 'warning'
      case 'down': return 'error'
      default: return 'info'
    }
  }
  
  return (
    <PerformanceAlert
      type={getAlertType(status)}
      title={`${component} Status: ${status}`}
      message={uptime ? `Uptime: ${uptime}` : undefined}
      timestamp={new Date().toISOString()}
      {...props}
    />
  )
}

export function EngagementAlert({ platform, engagementRate, previousRate, ...props }) {
  const change = engagementRate - previousRate
  const changePercent = ((change / previousRate) * 100).toFixed(1)
  const isImprovement = change > 0
  
  return (
    <PerformanceAlert
      type={isImprovement ? 'success' : 'warning'}
      title={`${platform} Engagement ${isImprovement ? 'Increase' : 'Decrease'}`}
      message={`Engagement rate ${isImprovement ? 'improved' : 'dropped'} by ${Math.abs(changePercent)}% (${engagementRate}%)`}
      action={isImprovement ? 'Analyze Success Factors' : 'Review Content Strategy'}
      timestamp={new Date().toISOString()}
      {...props}
    />
  )
}

export function ViralAlert({ contentTitle, platform, viralScore, growth, ...props }) {
  return (
    <PerformanceAlert
      type="insight"
      title="Content Going Viral!"
      message={`"${contentTitle}" on ${platform} has a viral score of ${viralScore}/10 with +${growth}% growth`}
      action="Boost Similar Content"
      timestamp={new Date().toISOString()}
      persistent={true}
      {...props}
    />
  )
}

export function OptimizationAlert({ recommendation, confidence, platform, ...props }) {
  return (
    <PerformanceAlert
      type="insight"
      title="AI Optimization Suggestion"
      message={recommendation}
      action="Apply Suggestion"
      metric={`${platform} - Confidence: ${confidence}%`}
      timestamp={new Date().toISOString()}
      {...props}
    />
  )
}