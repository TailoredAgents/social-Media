import { useState, useEffect, useRef } from 'react'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

const NotificationToast = ({ notification, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(false)
  const [isExiting, setIsExiting] = useState(false)
  const timeoutRef = useRef(null)

  useEffect(() => {
    // Animate in
    setIsVisible(true)

    // Auto-dismiss after duration
    if (notification.duration && !notification.persistent) {
      timeoutRef.current = setTimeout(() => {
        handleDismiss()
      }, notification.duration)
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [notification.duration, notification.persistent])

  const handleDismiss = () => {
    setIsExiting(true)
    setTimeout(() => {
      onDismiss(notification.id)
    }, 300) // Match animation duration
  }

  const getIcon = () => {
    const iconClasses = "h-6 w-6"
    
    switch (notification.type) {
      case 'success':
        return <CheckCircleIcon className={`${iconClasses} text-green-400`} />
      case 'error':
        return <XCircleIcon className={`${iconClasses} text-red-400`} />
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClasses} text-yellow-400`} />
      case 'info':
      default:
        return <InformationCircleIcon className={`${iconClasses} text-blue-400`} />
    }
  }

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  return (
    <div
      className={`
        max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden
        transform transition-all duration-300 ease-in-out
        ${isVisible && !isExiting ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        ${getBackgroundColor()}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            <p className="text-sm font-medium text-gray-900">
              {notification.title}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {notification.message}
            </p>
            {notification.action && (
              <div className="mt-3">
                <button
                  onClick={notification.action.onClick}
                  className="text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  {notification.action.label}
                </button>
              </div>
            )}
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={handleDismiss}
            >
              <span className="sr-only">Close</span>
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Progress bar for timed notifications */}
      {notification.duration && !notification.persistent && (
        <div className="h-1 bg-gray-200">
          <div
            className={`h-full transition-all ease-linear ${
              notification.type === 'success' ? 'bg-green-400' :
              notification.type === 'error' ? 'bg-red-400' :
              notification.type === 'warning' ? 'bg-yellow-400' :
              'bg-blue-400'
            }`}
            style={{
              animation: `shrink ${notification.duration}ms linear`,
              animationFillMode: 'forwards'
            }}
          />
        </div>
      )}
      
      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  )
}

export default NotificationToast