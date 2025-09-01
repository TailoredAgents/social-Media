import React, { useState, useEffect, useRef, useMemo } from 'react'
import { 
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale,
  Filler
} from 'chart.js'
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2'
import { 
  PlayIcon,
  PauseIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale,
  Filler
)

const chartTypes = {
  line: { component: Line, name: 'Line Chart' },
  bar: { component: Bar, name: 'Bar Chart' },
  doughnut: { component: Doughnut, name: 'Doughnut Chart' },
  radar: { component: Radar, name: 'Radar Chart' }
}

const LiveChart = React.memo(function LiveChart({
  title,
  type = 'line',
  data: initialData,
  options: customOptions = {},
  updateInterval = 5000,
  maxDataPoints = 20,
  autoUpdate = true,
  height = 300,
  showControls = true,
  showTypeSelector = false,
  onDataUpdate = null,
  className = ''
}) {
  const [data, setData] = useState(initialData)
  const [isPlaying, setIsPlaying] = useState(autoUpdate)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [currentType, setCurrentType] = useState(type)
  const [showSettings, setShowSettings] = useState(false)
  
  const chartRef = useRef(null)
  const intervalRef = useRef(null)
  
  // Default chart options with live chart enhancements
  const defaultOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: isPlaying ? 750 : 0,
      easing: 'easeInOutQuart'
    },
    interaction: {
      intersect: false,
      mode: 'index'
    },
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          usePointStyle: true,
          padding: 20
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context) {
            const label = context.dataset.label || ''
            const value = typeof context.parsed.y === 'number' 
              ? context.parsed.y.toLocaleString()
              : context.parsed.y
            return `${label}: ${value}`
          },
          afterLabel: function(context) {
            if (context.dataset.change) {
              const change = context.dataset.change[context.dataIndex]
              if (change !== undefined) {
                return `Change: ${change > 0 ? '+' : ''}${change.toFixed(1)}%`
              }
            }
            return ''
          }
        }
      }
    },
    scales: currentType === 'line' || currentType === 'bar' ? {
      x: {
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          maxTicksLimit: 8
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
            return value.toLocaleString()
          }
        }
      }
    } : {},
    ...customOptions
  }), [currentType, isPlaying, customOptions])
  
  // Simulate real-time data updates
  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }
    
    intervalRef.current = setInterval(() => {
      setData(prevData => {
        if (!prevData || !prevData.datasets) return prevData
        
        const newData = { ...prevData }
        
        // Add new data point and remove old ones if exceeding max
        newData.datasets = prevData.datasets.map(dataset => {
          const newDataset = { ...dataset }
          
          // Generate new data point (simulation)
          const lastValue = dataset.data[dataset.data.length - 1] || 0
          const variation = (Math.random() - 0.5) * (lastValue * 0.1)
          const newValue = Math.max(0, lastValue + variation)
          
          newDataset.data = [...dataset.data, newValue]
          
          // Maintain max data points
          if (newDataset.data.length > maxDataPoints) {
            newDataset.data = newDataset.data.slice(-maxDataPoints)
          }
          
          return newDataset
        })
        
        // Update labels
        if (newData.labels) {
          const now = new Date()
          const timeLabel = now.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
          })
          
          newData.labels = [...prevData.labels, timeLabel]
          
          if (newData.labels.length > maxDataPoints) {
            newData.labels = newData.labels.slice(-maxDataPoints)
          }
        }
        
        // Callback for data updates
        if (onDataUpdate) {
          onDataUpdate(newData)
        }
        
        return newData
      })
    }, updateInterval)
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isPlaying, updateInterval, maxDataPoints, onDataUpdate])
  
  // Update data when initialData changes
  useEffect(() => {
    setData(initialData)
  }, [initialData])
  
  const togglePlayPause = () => {
    setIsPlaying(!isPlaying)
  }
  
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }
  
  const handleTypeChange = (newType) => {
    setCurrentType(newType)
  }
  
  const resetData = () => {
    setData(initialData)
  }
  
  const exportChart = () => {
    if (chartRef.current) {
      const canvas = chartRef.current.canvas
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `${title.replace(/\s+/g, '_').toLowerCase()}_chart.png`
      link.href = url
      link.click()
    }
  }
  
  const ChartComponent = chartTypes[currentType]?.component || Line
  
  return (
    <div className={`bg-white rounded-lg shadow ${className} ${
      isFullscreen ? 'fixed inset-4 z-50' : ''
    }`}>
      {/* Chart Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          {isPlaying && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-600 font-medium">LIVE</span>
            </div>
          )}
        </div>
        
        {showControls && (
          <div className="flex items-center space-x-2">
            {/* Type Selector */}
            {showTypeSelector && (
              <select
                value={currentType}
                onChange={(e) => handleTypeChange(e.target.value)}
                className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {Object.entries(chartTypes).map(([key, config]) => (
                  <option key={key} value={key}>
                    {config.name}
                  </option>
                ))}
              </select>
            )}
            
            {/* Settings */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
              title="Chart settings"
            >
              <AdjustmentsHorizontalIcon className="h-4 w-4" />
            </button>
            
            {/* Play/Pause */}
            <button
              onClick={togglePlayPause}
              className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
              title={isPlaying ? 'Pause updates' : 'Resume updates'}
            >
              {isPlaying ? (
                <PauseIcon className="h-4 w-4" />
              ) : (
                <PlayIcon className="h-4 w-4" />
              )}
            </button>
            
            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            >
              {isFullscreen ? (
                <ArrowsPointingInIcon className="h-4 w-4" />
              ) : (
                <ArrowsPointingOutIcon className="h-4 w-4" />
              )}
            </button>
          </div>
        )}
      </div>
      
      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div>
              <label className="block text-gray-700 mb-1">Update Interval</label>
              <select
                value={updateInterval}
                onChange={(e) => setUpdateInterval(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value={1000}>1 second</option>
                <option value={5000}>5 seconds</option>
                <option value={10000}>10 seconds</option>
                <option value={30000}>30 seconds</option>
              </select>
            </div>
            
            <div>
              <label className="block text-gray-700 mb-1">Max Data Points</label>
              <select
                value={maxDataPoints}
                onChange={(e) => setMaxDataPoints(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value={10}>10 points</option>
                <option value={20}>20 points</option>
                <option value={50}>50 points</option>
                <option value={100}>100 points</option>
              </select>
            </div>
            
            <div className="flex items-end space-x-2">
              <button
                onClick={resetData}
                className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
              >
                Reset Data
              </button>
              <button
                onClick={exportChart}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Export PNG
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Chart Container */}
      <div className="p-4">
        <div style={{ height: isFullscreen ? 'calc(100vh - 200px)' : `${height}px` }}>
          <ChartComponent
            ref={chartRef}
            data={data}
            options={defaultOptions}
          />
        </div>
      </div>
      
      {/* Chart Footer */}
      <div className="px-4 pb-4">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
            <span>{data?.datasets?.[0]?.data?.length || 0} data points</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>Auto-update: {isPlaying ? 'ON' : 'OFF'}</span>
            <span>•</span>
            <span>Interval: {updateInterval / 1000}s</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Specialized live chart components
export function LiveMetricsChart({ metrics, timeframe = '1h', ...props }) {
  const data = {
    labels: metrics?.labels || [],
    datasets: metrics?.datasets || []
  }
  
  return (
    <LiveChart
      title="Live Metrics"
      type="line"
      data={data}
      updateInterval={30000} // 30 seconds
      maxDataPoints={24} // 24 hours of data
      {...props}
    />
  )
}

export function LiveEngagementChart({ platforms, ...props }) {
  const data = {
    labels: platforms?.map(p => p.name) || [],
    datasets: [{
      label: 'Engagement Rate',
      data: platforms?.map(p => p.engagement) || [],
      backgroundColor: platforms?.map(p => p.color + '80') || [],
      borderColor: platforms?.map(p => p.color) || [],
      borderWidth: 2
    }]
  }
  
  return (
    <LiveChart
      title="Live Platform Engagement"
      type="bar"
      data={data}
      updateInterval={60000} // 1 minute
      maxDataPoints={5} // 5 platforms
      {...props}
    />
  )
}

export function LivePerformanceRadar({ performanceData, ...props }) {
  const data = {
    labels: ['Engagement', 'Reach', 'Growth', 'Quality', 'Consistency'],
    datasets: [{
      label: 'Performance Score',
      data: performanceData || [0, 0, 0, 0, 0],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      pointBackgroundColor: 'rgb(59, 130, 246)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgb(59, 130, 246)'
    }]
  }
  
  return (
    <LiveChart
      title="Performance Radar"
      type="radar"
      data={data}
      updateInterval={120000} // 2 minutes
      options={{
        scales: {
          r: {
            beginAtZero: true,
            max: 10
          }
        }
      }}
      {...props}
    />
  )
})

export default LiveChart