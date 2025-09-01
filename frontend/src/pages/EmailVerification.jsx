import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const EmailVerification = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { authError, clearError } = useAuth()
  
  const [status, setStatus] = useState('loading') // loading, success, error, expired
  const [isResending, setIsResending] = useState(false)
  const [resendMessage, setResendMessage] = useState('')
  const [email, setEmail] = useState('')

  const token = searchParams.get('token')

  useEffect(() => {
    if (token) {
      verifyEmail(token)
    } else {
      setStatus('error')
    }
  }, [token])

  useEffect(() => {
    clearError()
  }, [clearError])

  const verifyEmail = async (verificationToken) => {
    try {
      const response = await fetch('/api/auth/verify-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: verificationToken })
      })

      if (response.ok) {
        setStatus('success')
        setTimeout(() => {
          navigate('/login', { replace: true })
        }, 3000)
      } else {
        const data = await response.json()
        if (data.detail?.includes('expired')) {
          setStatus('expired')
        } else {
          setStatus('error')
        }
      }
    } catch (error) {
      console.error('Email verification failed:', error)
      setStatus('error')
    }
  }

  const handleResendVerification = async (e) => {
    e.preventDefault()
    
    if (!email) {
      setResendMessage('Please enter your email address')
      return
    }

    try {
      setIsResending(true)
      const response = await fetch('/api/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      })

      if (response.ok) {
        setResendMessage('Verification email sent! Check your inbox.')
      } else {
        const data = await response.json()
        setResendMessage(data.detail || 'Failed to send verification email')
      }
    } catch (error) {
      setResendMessage('Failed to send verification email')
    } finally {
      setIsResending(false)
    }
  }

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <h2 className="text-2xl font-bold text-gray-900">
            Verifying your email...
          </h2>
        </div>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8 text-center">
          <div className="rounded-full h-16 w-16 bg-green-100 mx-auto flex items-center justify-center">
            <svg className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Email Verified Successfully!
          </h2>
          <p className="text-gray-600">
            Your email has been verified. You'll be redirected to the login page in a few seconds.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Continue to Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="rounded-full h-16 w-16 bg-red-100 mx-auto flex items-center justify-center mb-4">
            <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            {status === 'expired' ? 'Verification Link Expired' : 'Verification Failed'}
          </h2>
          <p className="mt-2 text-gray-600">
            {status === 'expired' 
              ? 'Your verification link has expired. Please request a new one below.'
              : 'There was a problem verifying your email address.'
            }
          </p>
        </div>

        {authError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{authError}</span>
            <button
              type="button"
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={clearError}
            >
              <span className="sr-only">Dismiss</span>
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleResendVerification}>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Request New Verification Email</h3>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isResending}
            />
          </div>

          {resendMessage && (
            <div className={`px-4 py-3 rounded ${
              resendMessage.includes('sent') 
                ? 'bg-green-50 border border-green-200 text-green-700'
                : 'bg-red-50 border border-red-200 text-red-700'
            }`}>
              {resendMessage}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isResending}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isResending ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Sending...
                </div>
              ) : (
                'Send Verification Email'
              )}
            </button>
          </div>

          <div className="text-center">
            <Link to="/login" className="text-blue-600 hover:text-blue-500 text-sm">
              Back to Login
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EmailVerification