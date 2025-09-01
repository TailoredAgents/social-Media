import React from 'react'
import ErrorBoundary from './ErrorBoundary'
import { WifiIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

const ApiErrorFallback = (error, retry) => {
  const isNetworkError = error?.message?.includes('Network') || 
                        error?.message?.includes('fetch') ||
                        error?.message?.includes('ERR_NETWORK')
  
  const isAuthError = error?.message?.includes('401') || 
                     error?.message?.includes('Unauthorized') ||
                     error?.message?.includes('Authentication')

  const is429Error = error?.message?.includes('429') || 
                    error?.message?.includes('rate limit')

  const is503Error = error?.message?.includes('503') || 
                    error?.message?.includes('Service Unavailable')

  let title, message, actionText

  if (isNetworkError) {
    title = 'Connection Problem'
    message = 'Unable to connect to our servers. Please check your internet connection and try again.'
    actionText = 'Retry Connection'
  } else if (isAuthError) {
    title = 'Authentication Required'
    message = 'Your session has expired. Please refresh the page to log in again.'
    actionText = 'Refresh Page'
  } else if (is429Error) {
    title = 'Too Many Requests'
    message = 'You\'re making requests too quickly. Please wait a moment before trying again.'
    actionText = 'Try Again'
  } else if (is503Error) {
    title = 'Service Temporarily Unavailable'
    message = 'Our servers are currently experiencing high traffic. Please try again in a few minutes.'
    actionText = 'Retry'
  } else {
    title = 'API Error'
    message = 'We encountered an error while loading data. This might be a temporary issue.'
    actionText = 'Retry'
  }

  return (
    <div className="min-h-64 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
      <div className="text-center p-6">
        {isNetworkError ? (
          <WifiIcon className="mx-auto h-12 w-12 text-orange-500 mb-3" />
        ) : (
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500 mb-3" />
        )}
        
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-600 mb-4 max-w-sm">{message}</p>
        
        <button
          onClick={retry}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {actionText}
        </button>
      </div>
    </div>
  )
}

const ApiErrorBoundary = ({ children, componentName, onError, onRetry }) => {
  return (
    <ErrorBoundary
      componentName={componentName}
      fallback={ApiErrorFallback}
      onError={onError}
      onRetry={onRetry}
      title="API Error"
      message="Failed to load data from the server."
      showRefresh={true}
      supportContact={true}
    >
      {children}
    </ErrorBoundary>
  )
}

export default ApiErrorBoundary