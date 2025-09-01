import React from 'react'
import ErrorBoundary from './ErrorBoundary'
import { HomeIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

const PageErrorFallback = (error, retry) => {
  const navigateHome = () => {
    window.location.href = '/'
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center p-8 max-w-md">
        <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-red-100 mb-6">
          <HomeIcon className="h-10 w-10 text-red-600" />
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Page Error
        </h1>
        
        <p className="text-gray-600 mb-8">
          This page encountered an unexpected error. You can try reloading the page 
          or return to the dashboard.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={retry}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <ArrowPathIcon className="h-5 w-5 mr-2" />
            Try Again
          </button>
          
          <button
            onClick={navigateHome}
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <HomeIcon className="h-5 w-5 mr-2" />
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

const PageErrorBoundary = ({ children, pageName, onError, onRetry }) => {
  return (
    <ErrorBoundary
      componentName={`Page: ${pageName}`}
      fallback={PageErrorFallback}
      onError={onError}
      onRetry={onRetry}
      showDetails={true}
      showRefresh={true}
      supportContact={true}
    >
      {children}
    </ErrorBoundary>
  )
}

export default PageErrorBoundary