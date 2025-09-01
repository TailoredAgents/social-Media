import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAdminAuth } from '../../contexts/AdminAuthContext'

const AdminLogin = () => {
  const { adminLogin, isAuthenticated, isLoading, authError, clearError } = useAdminAuth()
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    totpCode: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [show2FA, setShow2FA] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/admin/dashboard', { replace: true })
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    clearError()
  }, [clearError])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.email || !formData.password) {
      return
    }

    try {
      setIsSubmitting(true)
      await adminLogin({
        email: formData.email,
        password: formData.password,
        totp_code: formData.totpCode || null
      })
    } catch (error) {
      // Check if 2FA is required
      if (error.message === '2FA token required') {
        setShow2FA(true)
      }
      console.error('Admin login failed:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading && !isSubmitting) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-red-600">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            Admin Access
          </h2>
          <p className="mt-2 text-center text-sm text-gray-400">
            Lily AI Social Media Administration Panel
          </p>
          <div className="mt-4 text-center">
            <Link 
              to="/login" 
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              ← Back to User Login
            </Link>
          </div>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {authError && (
            <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded relative">
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

          <div className="space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm"
                placeholder="Enter admin email"
                value={formData.email}
                onChange={handleInputChange}
                disabled={isSubmitting}
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  className="appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm"
                  placeholder="Enter password"
                  value={formData.password}
                  onChange={handleInputChange}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isSubmitting}
                >
                  {showPassword ? (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* 2FA Token (show only if required) */}
            {show2FA && (
              <div>
                <label htmlFor="totpCode" className="block text-sm font-medium text-gray-300">
                  2FA Authentication Code
                </label>
                <input
                  id="totpCode"
                  name="totpCode"
                  type="text"
                  maxLength="6"
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm"
                  placeholder="Enter 6-digit code"
                  value={formData.totpCode}
                  onChange={handleInputChange}
                  disabled={isSubmitting}
                />
                <p className="mt-1 text-xs text-gray-400">
                  Enter the 6-digit code from your authenticator app
                </p>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={isSubmitting || !formData.email || !formData.password}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Authenticating...
                </div>
              ) : (
                <>
                  <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                    <svg className="h-5 w-5 text-red-500 group-hover:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                  Sign in to Admin Panel
                </>
              )}
            </button>
          </div>
        </form>

        {/* Security Notice */}
        <div className="mt-6 text-center">
          <div className="bg-gray-800 border border-gray-700 rounded-md p-4">
            <div className="flex items-center justify-center mb-2">
              <svg className="h-5 w-5 text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm font-medium text-yellow-400">Security Notice</span>
            </div>
            <p className="text-xs text-gray-300">
              This is a restricted admin area. All access attempts are logged and monitored.
              Unauthorized access is prohibited.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminLogin