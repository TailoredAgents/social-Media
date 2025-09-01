import { useState, useEffect } from 'react'
import { 
  ArrowUpIcon, 
  ArrowDownIcon,
  MinusIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

const colorThemes = {
  blue: {
    bg: 'bg-blue-100',
    icon: 'text-blue-600',
    accent: 'text-blue-600',
    gradient: 'from-blue-50 to-blue-100'
  },
  green: {
    bg: 'bg-green-100',
    icon: 'text-green-600',
    accent: 'text-green-600',
    gradient: 'from-green-50 to-green-100'
  },
  purple: {
    bg: 'bg-purple-100',
    icon: 'text-purple-600',
    accent: 'text-purple-600',
    gradient: 'from-purple-50 to-purple-100'
  },
  orange: {
    bg: 'bg-orange-100',
    icon: 'text-orange-600',
    accent: 'text-orange-600',
    gradient: 'from-orange-50 to-orange-100'
  },
  red: {
    bg: 'bg-red-100',
    icon: 'text-red-600',
    accent: 'text-red-600',
    gradient: 'from-red-50 to-red-100'
  },
  yellow: {
    bg: 'bg-yellow-100',
    icon: 'text-yellow-600',
    accent: 'text-yellow-600',
    gradient: 'from-yellow-50 to-yellow-100'
  },
  indigo: {
    bg: 'bg-indigo-100',
    icon: 'text-indigo-600',
    accent: 'text-indigo-600',
    gradient: 'from-indigo-50 to-indigo-100'
  }
}

export default function MetricCard({
  title,
  value,
  change = null,
  icon: Icon,
  color = 'blue',
  isLive = false,
  reversed = false, // true if lower values are better (like response time)
  format = 'number', // 'number', 'percentage', 'currency', 'time'
  precision = 1,
  threshold = null,
  status = null, // 'good', 'warning', 'critical'
  onClick = null,
  loading = false,
  subtitle = null,
  trend = null, // array of recent values for sparkline
  target = null,
  unit = null
}) {
  const [previousValue, setPreviousValue] = useState(value)
  const [isAnimating, setIsAnimating] = useState(false)
  
  const theme = colorThemes[color] || colorThemes.blue
  
  // Animate value changes
  useEffect(() => {
    if (value !== previousValue) {
      setIsAnimating(true)
      const timer = setTimeout(() => {
        setIsAnimating(false)
        setPreviousValue(value)
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [value, previousValue])
  
  // Format the display value
  const formatValue = (val) => {
    if (val === null || val === undefined) return '—'
    
    switch (format) {
      case 'percentage':
        return `${val.toFixed(precision)}%`
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(val)
      case 'time':
        if (val < 1000) return `${val}ms`
        return `${(val / 1000).toFixed(precision)}s`
      default:
        if (typeof val === 'number') {
          if (val >= 1000000) return `${(val / 1000000).toFixed(precision)}M`
          if (val >= 1000) return `${(val / 1000).toFixed(precision)}K`
          return val.toLocaleString()
        }
        return val
    }
  }
  
  // Get change indicators
  const getChangeIcon = (changeValue) => {
    if (changeValue === null || changeValue === undefined || changeValue === 0) {
      return <MinusIcon className="h-4 w-4 text-gray-500" />
    }
    
    const isPositive = reversed ? changeValue < 0 : changeValue > 0
    return isPositive ? (
      <ArrowUpIcon className="h-4 w-4 text-green-500" />
    ) : (
      <ArrowDownIcon className="h-4 w-4 text-red-500" />
    )
  }
  
  const getChangeColor = (changeValue) => {
    if (changeValue === null || changeValue === undefined || changeValue === 0) {
      return 'text-gray-600'
    }
    
    const isPositive = reversed ? changeValue < 0 : changeValue > 0
    return isPositive ? 'text-green-600' : 'text-red-600'
  }
  
  // Get status indicator
  const getStatusIndicator = () => {
    if (!status) return null
    
    const statusConfig = {
      good: { icon: CheckCircleIcon, color: 'text-green-500' },
      warning: { icon: ExclamationTriangleIcon, color: 'text-yellow-500' },
      critical: { icon: ExclamationTriangleIcon, color: 'text-red-500' }
    }
    
    const config = statusConfig[status]
    if (!config) return null
    
    const StatusIcon = config.icon
    return <StatusIcon className={`h-4 w-4 ${config.color}`} />
  }
  
  // Calculate progress toward target
  const getTargetProgress = () => {
    if (!target || !value) return null
    
    const progress = Math.min((value / target) * 100, 100)
    return Math.round(progress)
  }
  
  const targetProgress = getTargetProgress()
  
  return (
    <div 
      className={`bg-white rounded-lg shadow p-6 relative overflow-hidden transition-all duration-200 hover:shadow-lg ${
        onClick ? 'cursor-pointer hover:bg-gray-50' : ''
      } ${isAnimating ? 'ring-2 ring-blue-200' : ''}`}
      onClick={onClick}
    >
      {/* Loading state */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      )}
      
      {/* Live indicator */}
      {isLive && (
        <div className="absolute top-2 right-2 flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Live data"></div>
          <span className="text-xs text-gray-500">LIVE</span>
        </div>
      )}
      
      {/* Status indicator */}
      {status && (
        <div className="absolute top-2 left-2">
          {getStatusIndicator()}
        </div>
      )}
      
      {/* Main content */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-500">{title}</p>
            {change !== null && change !== undefined && (
              <div className="flex items-center space-x-1">
                {getChangeIcon(change)}
                <span className={`text-xs font-medium ${getChangeColor(change)}`}>
                  {Math.abs(change)}%
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-baseline space-x-2">
            <p className={`text-3xl font-bold text-gray-900 transition-all duration-300 ${
              isAnimating ? 'scale-110' : ''
            }`}>
              {formatValue(value)}
            </p>
            {unit && (
              <span className="text-sm text-gray-500">{unit}</span>
            )}
          </div>
          
          {subtitle && (
            <p className="text-xs text-gray-600 mt-1">{subtitle}</p>
          )}
          
          {/* Target progress */}
          {target && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>Progress to target</span>
                <span>{targetProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className={`bg-gradient-to-r ${theme.gradient} h-1.5 rounded-full transition-all duration-500`}
                  style={{ width: `${targetProgress}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Change details */}
          {change !== null && change !== undefined && (
            <div className="flex items-center mt-2">
              <span className="text-xs text-gray-500">vs last period</span>
              {trend && trend.length > 1 && (
                <div className="ml-2 flex items-center space-x-1">
                  {trend[trend.length - 1] > trend[trend.length - 2] ? (
                    <ArrowTrendingUpIcon className="h-3 w-3 text-green-500" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-3 w-3 text-red-500" />
                  )}
                  <span className="text-xs text-gray-500">trending</span>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Icon */}
        <div className={`p-3 ${theme.bg} rounded-full flex-shrink-0`}>
          {Icon && <Icon className={`h-6 w-6 ${theme.icon}`} />}
        </div>
      </div>
      
      {/* Sparkline trend */}
      {trend && trend.length > 1 && (
        <div className="mt-4">
          <div className="flex items-end justify-between h-8 space-x-1">
            {trend.map((point, index) => {
              const height = Math.max(4, (point / Math.max(...trend)) * 32)
              return (
                <div
                  key={index}
                  className={`bg-gradient-to-t ${theme.gradient} rounded-t transition-all duration-300`}
                  style={{ height: `${height}px`, width: `${100 / trend.length}%` }}
                />
              )
            })}
          </div>
        </div>
      )}
      
      {/* Threshold indicator */}
      {threshold && (
        <div className="absolute bottom-0 left-0 right-0 h-1">
          {value > threshold ? (
            <div className="w-full h-full bg-green-200"></div>
          ) : (
            <div className="w-full h-full bg-red-200"></div>
          )}
        </div>
      )}
    </div>
  )
}

// Specialized metric card variants
export function EngagementMetricCard({ platform, rate, previousRate, ...props }) {
  const change = previousRate ? ((rate - previousRate) / previousRate) * 100 : null
  
  return (
    <MetricCard
      title={`${platform} Engagement`}
      value={rate}
      change={change}
      format="percentage"
      color="green"
      subtitle="Average engagement rate"
      {...props}
    />
  )
}

export function PerformanceMetricCard({ metric, current, target, threshold, ...props }) {
  const progress = target ? (current / target) * 100 : null
  const status = threshold ? (current > threshold ? 'good' : 'warning') : null
  
  return (
    <MetricCard
      title={metric}
      value={current}
      target={target}
      threshold={threshold}
      status={status}
      subtitle={progress ? `${Math.round(progress)}% of target` : undefined}
      {...props}
    />
  )
}

export function SystemMetricCard({ systemName, value, unit, status, uptime, ...props }) {
  return (
    <MetricCard
      title={systemName}
      value={value}
      unit={unit}
      status={status}
      subtitle={uptime ? `Uptime: ${uptime}` : undefined}
      color={status === 'good' ? 'green' : status === 'warning' ? 'yellow' : 'red'}
      {...props}
    />
  )
}