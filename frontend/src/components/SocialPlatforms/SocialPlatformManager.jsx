import React, { useState, useEffect } from 'react'
import apiService from '../../services/api'
import { info, error as logError } from '../../utils/logger'

const SocialPlatformManager = () => {
  const [connections, setConnections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [connecting, setConnecting] = useState(null)

  // Fetch social connections on mount
  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    try {
      setLoading(true)
      const data = await apiService.getSocialConnections()
      setConnections(data)
      info('Fetched social connections', data)
    } catch (err) {
      logError('Failed to fetch social connections', err)
      setError('Failed to load social connections')
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = async (platform) => {
    try {
      setConnecting(platform)
      const response = await apiService.connectSocialPlatform(platform)
      
      // Redirect to OAuth authorization URL
      if (response.authorization_url) {
        window.location.href = response.authorization_url
      }
    } catch (err) {
      logError(`Failed to connect ${platform}`, err)
      setError(`Failed to connect ${platform}`)
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async (connectionId, platform) => {
    if (!window.confirm(`Are you sure you want to disconnect ${platform}?`)) {
      return
    }

    try {
      await apiService.disconnectSocialPlatform(connectionId)
      info(`Disconnected ${platform}`)
      
      // Update local state
      setConnections(prev => prev.filter(c => c.id !== connectionId))
    } catch (err) {
      logError(`Failed to disconnect ${platform}`, err)
      setError(`Failed to disconnect ${platform}`)
    }
  }

  const handleValidate = async (platform) => {
    try {
      const result = await apiService.validateSocialConnection(platform)
      info(`Validation result for ${platform}:`, result)
      
      if (result.is_valid) {
        alert(`${platform} connection is valid!`)
      } else {
        alert(`${platform} connection has issues: ${result.error || 'Unknown error'}`)
      }
      
      // Refresh connections to get updated status
      fetchConnections()
    } catch (err) {
      logError(`Failed to validate ${platform}`, err)
      alert(`Failed to validate ${platform} connection`)
    }
  }

  const getPlatformIcon = (platform) => {
    switch (platform?.toLowerCase()) {
      case 'twitter':
      case 'x':
        return '𝕏'
      case 'instagram':
        return '📷'
      default:
        return '🔗'
    }
  }

  const getPlatformColor = (platform) => {
    switch (platform?.toLowerCase()) {
      case 'twitter':
      case 'x':
        return '#000000'
      case 'instagram':
        return '#E4405F'
      default:
        return '#6B7280'
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'connected':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Connected
          </span>
        )
      case 'error':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Error
          </span>
        )
      case 'disconnected':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            Disconnected
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            {status}
          </span>
        )
    }
  }

  const availablePlatforms = ['twitter', 'instagram']
  const connectedPlatforms = connections.map(c => c.platform.toLowerCase())
  const unconnectedPlatforms = availablePlatforms.filter(p => !connectedPlatforms.includes(p))

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
          <span className="block sm:inline">{error}</span>
          <button
            onClick={() => setError(null)}
            className="absolute top-0 bottom-0 right-0 px-4 py-3"
          >
            <span className="text-red-500">×</span>
          </button>
        </div>
      )}

      {/* Connected Platforms */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Connected Platforms</h3>
        
        {connections.length === 0 ? (
          <p className="text-gray-500">No platforms connected yet.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {connections.map(connection => (
              <div
                key={connection.id}
                className="bg-white overflow-hidden shadow rounded-lg border border-gray-200"
              >
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <div
                        className="flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center text-white font-bold text-lg"
                        style={{ backgroundColor: getPlatformColor(connection.platform) }}
                      >
                        {getPlatformIcon(connection.platform)}
                      </div>
                      <div className="ml-3">
                        <h4 className="text-sm font-medium text-gray-900 capitalize">
                          {connection.platform}
                        </h4>
                        <p className="text-sm text-gray-500">
                          @{connection.platform_username}
                        </p>
                      </div>
                    </div>
                    {getStatusBadge(connection.connection_status)}
                  </div>

                  <div className="text-xs text-gray-500 mb-4">
                    Connected: {new Date(connection.connected_at).toLocaleDateString()}
                    {connection.last_used_at && (
                      <div>
                        Last used: {new Date(connection.last_used_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleValidate(connection.platform)}
                      className="flex-1 inline-flex justify-center items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Validate
                    </button>
                    <button
                      onClick={() => handleDisconnect(connection.id, connection.platform)}
                      className="flex-1 inline-flex justify-center items-center px-3 py-1.5 border border-red-300 shadow-sm text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Platforms to Connect */}
      {unconnectedPlatforms.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Available Platforms</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {unconnectedPlatforms.map(platform => (
              <div
                key={platform}
                className="bg-white overflow-hidden shadow rounded-lg border border-gray-200"
              >
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <div
                        className="flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center text-white font-bold text-lg"
                        style={{ backgroundColor: getPlatformColor(platform) }}
                      >
                        {getPlatformIcon(platform)}
                      </div>
                      <div className="ml-3">
                        <h4 className="text-sm font-medium text-gray-900 capitalize">
                          {platform}
                        </h4>
                        <p className="text-sm text-gray-500">
                          Not connected
                        </p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleConnect(platform)}
                    disabled={connecting === platform}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {connecting === platform ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Connecting...
                      </>
                    ) : (
                      `Connect ${platform}`
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SocialPlatformManager