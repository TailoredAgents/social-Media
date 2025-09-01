import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'
import { Line, Doughnut } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

export const GoalProgressChart = React.memo(function GoalProgressChart({ goal }) {
  const data = {
    labels: ['Start', 'Current', 'Target'],
    datasets: [
      {
        label: 'Progress',
        data: [0, goal.current_value, goal.target_value],
        borderColor: goal.is_on_track ? 'rgb(59, 130, 246)' : 'rgb(245, 158, 11)',
        backgroundColor: goal.is_on_track ? 'rgba(59, 130, 246, 0.1)' : 'rgba(245, 158, 11, 0.1)',
        fill: true,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
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
    elements: {
      point: {
        radius: 4,
        hoverRadius: 6,
      },
      line: {
        tension: 0.4,
      },
    },
  }

  return (
    <div className="h-40">
      <Line data={data} options={options} />
    </div>
  )
})

export const GoalCompletionChart = React.memo(function GoalCompletionChart({ goals }) {
  const statusCounts = goals.reduce((acc, goal) => {
    acc[goal.status] = (acc[goal.status] || 0) + 1
    return acc
  }, {})

  const data = {
    labels: ['Completed', 'Active', 'Paused', 'Failed'],
    datasets: [
      {
        data: [
          statusCounts.completed || 0,
          statusCounts.active || 0,
          statusCounts.paused || 0,
          statusCounts.failed || 0,
        ],
        backgroundColor: [
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 0,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
        },
      },
    },
  }

  return (
    <div className="h-64">
      <Doughnut data={data} options={options} />
    </div>
  )
})

export const ProgressTimelineChart = React.memo(function ProgressTimelineChart({ goal }) {
  // Generate mock timeline data based on milestones
  const generateTimelineData = () => {
    const startDate = new Date(goal.start_date)
    const targetDate = new Date(goal.target_date)
    const currentDate = new Date()
    
    const labels = []
    const progressData = []
    const projectedData = []
    
    // Add milestone points
    goal.milestones.forEach((milestone, index) => {
      const date = new Date(milestone.achieved_at)
      labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
      progressData.push((goal.target_value * milestone.percentage) / 100)
      projectedData.push(null)
    })
    
    // Add current point
    labels.push('Now')
    progressData.push(goal.current_value)
    projectedData.push(null)
    
    // Add projected completion
    if (goal.status === 'active') {
      labels.push(targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
      progressData.push(null)
      projectedData.push(goal.target_value)
    }
    
    return { labels, progressData, projectedData }
  }

  const { labels, progressData, projectedData } = generateTimelineData()

  const data = {
    labels,
    datasets: [
      {
        label: 'Actual Progress',
        data: progressData,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: false,
        tension: 0.3,
      },
      {
        label: 'Projected',
        data: projectedData,
        borderColor: 'rgb(156, 163, 175)',
        backgroundColor: 'rgba(156, 163, 175, 0.1)',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
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

  return (
    <div className="h-64">
      <Line data={data} options={options} />
    </div>
  )
})