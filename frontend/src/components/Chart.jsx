import React, { useMemo } from 'react'
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
} from 'chart.js'
import { Line, Bar, Doughnut } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
    },
    x: {
      grid: {
        display: false,
      },
    },
  },
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
    },
  },
}

const Chart = React.memo(function Chart({ data, type = 'line', options = {}, className = '', ariaLabel, ariaDescription }) {
  const mergedOptions = useMemo(() => {
    const baseOptions = type === 'doughnut' 
      ? { ...doughnutOptions, ...options }
      : { ...defaultOptions, ...options }
    
    // Add accessibility options
    return {
      ...baseOptions,
      plugins: {
        ...baseOptions.plugins,
        tooltip: {
          ...baseOptions.plugins?.tooltip,
          enabled: true,
          intersect: false
        }
      }
    }
  }, [type, options])

  const chartProps = useMemo(() => ({
    data,
    options: mergedOptions,
  }), [data, mergedOptions])

  return (
    <div 
      className={`relative h-64 ${className}`}
      role="img"
      aria-label={ariaLabel || `${type} chart`}
      aria-describedby={ariaDescription ? `chart-desc-${type}` : undefined}
    >
      {ariaDescription && (
        <div id={`chart-desc-${type}`} className="sr-only">
          {ariaDescription}
        </div>
      )}
      {type === 'line' && <Line {...chartProps} />}
      {type === 'bar' && <Bar {...chartProps} />}
      {type === 'doughnut' && <Doughnut {...chartProps} />}
    </div>
  )
})

export default Chart