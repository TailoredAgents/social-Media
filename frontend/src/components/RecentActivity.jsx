import React, { useMemo, useCallback } from 'react'
import { ClockIcon } from '@heroicons/react/24/outline'

const activities = [
  {
    id: 1,
    type: 'content_generated',
    message: 'AI generated 3 new posts about industry trends',
    time: '2 minutes ago',
    status: 'success',
  },
  {
    id: 2,
    type: 'post_published',
    message: 'LinkedIn post published: "The Future of AI in Marketing"',
    time: '15 minutes ago',
    status: 'success',
  },
  {
    id: 3,
    type: 'research_completed',
    message: 'Research agent analyzed 50+ trending topics',
    time: '1 hour ago',
    status: 'info',
  },
  {
    id: 4,
    type: 'optimization',
    message: 'Performance optimization recommendations generated',
    time: '2 hours ago',
    status: 'info',
  },
  {
    id: 5,
    type: 'post_scheduled',
    message: 'Twitter thread scheduled for 3:00 PM',
    time: '3 hours ago',
    status: 'pending',
  },
]

const getStatusColor = (status) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'info':
      return 'bg-blue-100 text-blue-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'error':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getStatusDot = (status) => {
  switch (status) {
    case 'success':
      return 'bg-green-400'
    case 'info':
      return 'bg-blue-400'
    case 'pending':
      return 'bg-yellow-400'
    case 'error':
      return 'bg-red-400'
    default:
      return 'bg-gray-400'
  }
}

const RecentActivity = React.memo(function RecentActivity() {
  return (
    <div className="bg-white shadow rounded-lg" role="region" aria-labelledby="recent-activity-heading">
      <div className="px-4 py-5 sm:p-6">
        <h3 id="recent-activity-heading" className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Recent Activity
        </h3>
        <div className="flow-root">
          <ul className="-mb-8" role="list" aria-label="Recent activity items">
            {activities.map((activity, activityIdx) => (
              <li key={activity.id} role="listitem">
                <div className="relative pb-8">
                  {activityIdx !== activities.length - 1 ? (
                    <span
                      className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  ) : null}
                  <div className="relative flex items-start space-x-3">
                    <div className="relative">
                      <div 
                        className={`h-3 w-3 rounded-full ${getStatusDot(activity.status)} ring-8 ring-white`}
                        role="img"
                        aria-label={`Status: ${activity.status}`}
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm text-gray-900">
                        <span className="font-medium">{activity.message}</span>
                      </div>
                      <div className="mt-1 flex items-center space-x-2">
                        <span 
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}
                          role="status"
                          aria-label={`Activity status: ${activity.status}`}
                        >
                          {activity.status}
                        </span>
                        <div className="flex items-center text-sm text-gray-500">
                          <ClockIcon className="mr-1.5 h-4 w-4 text-gray-400" aria-hidden="true" />
                          <time dateTime={activity.time} aria-label={`Time: ${activity.time}`}>
                            {activity.time}
                          </time>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
})

export default RecentActivity