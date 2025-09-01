import React, { useState } from 'react';
import PropTypes from 'prop-types';

const ConnectionHealth = ({ 
  connection, 
  onDisconnect, 
  onReconnect,
  isDisconnecting = false 
}) => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Determine platform icon and color
  const getPlatformInfo = (platform) => {
    switch (platform) {
      case 'meta':
        return {
          icon: '📘', // Facebook icon placeholder
          name: 'Facebook & Instagram',
          color: '#1877f2'
        };
      case 'x':
        return {
          icon: '🐦', // X/Twitter icon placeholder
          name: 'X (Twitter)',
          color: '#1da1f2'
        };
      default:
        return {
          icon: '🔗',
          name: platform.toUpperCase(),
          color: '#6b7280'
        };
    }
  };

  // Determine health status and badge
  const getHealthStatus = () => {
    if (!connection.expires_at) {
      return { status: 'healthy', label: 'Healthy', color: 'bg-green-100 text-green-800' };
    }
    
    if (connection.expires_in_hours <= 0) {
      return { status: 'expired', label: 'Expired', color: 'bg-red-100 text-red-800' };
    }
    
    if (connection.needs_reconnect) {
      return { status: 'expiring', label: 'Expiring Soon', color: 'bg-yellow-100 text-yellow-800' };
    }
    
    return { status: 'healthy', label: 'Healthy', color: 'bg-green-100 text-green-800' };
  };

  // Format expiry time
  const formatExpiry = () => {
    if (!connection.expires_at) {
      return 'Never expires';
    }
    
    if (connection.expires_in_hours <= 0) {
      return 'Expired';
    }
    
    if (connection.expires_in_hours < 24) {
      return `Expires in ${connection.expires_in_hours}h`;
    }
    
    const days = Math.floor(connection.expires_in_hours / 24);
    return `Expires in ${days} day${days === 1 ? '' : 's'}`;
  };

  const platformInfo = getPlatformInfo(connection.platform);
  const healthStatus = getHealthStatus();

  const handleDisconnect = () => {
    setShowConfirmDialog(false);
    onDisconnect(connection.id);
  };

  const handleReconnect = () => {
    onReconnect(connection.platform);
  };

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div 
              className="w-10 h-10 rounded-full flex items-center justify-center text-white text-lg font-semibold"
              style={{ backgroundColor: platformInfo.color }}
            >
              {platformInfo.icon}
            </div>
            <div>
              <h3 className="font-medium text-gray-900">
                {connection.connection_name}
              </h3>
              <p className="text-sm text-gray-500">
                @{connection.platform_username} • {platformInfo.name}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${healthStatus.color}`}>
              {healthStatus.label}
            </span>
            {connection.webhook_subscribed && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Webhook ✓
              </span>
            )}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Status:</span> {formatExpiry()}
          </div>
          <div>
            <span className="font-medium">Scopes:</span> {connection.scopes?.length || 0} permissions
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Connected {new Date(connection.created_at).toLocaleDateString()}
          </div>
          
          <div className="flex items-center space-x-2">
            {connection.needs_reconnect && (
              <button
                onClick={handleReconnect}
                className="inline-flex items-center px-3 py-1.5 border border-yellow-300 text-sm font-medium rounded text-yellow-700 bg-yellow-50 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
              >
                Reconnect
              </button>
            )}
            
            <button
              onClick={() => setShowConfirmDialog(true)}
              disabled={isDisconnecting}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative bg-white rounded-lg shadow-xl max-w-md mx-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Disconnect {connection.connection_name}?
              </h3>
              <button
                onClick={() => setShowConfirmDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                This will revoke access to your {platformInfo.name} account and stop all automated posting. 
                You can reconnect at any time.
              </p>
              {connection.webhook_subscribed && (
                <p className="text-sm text-gray-600 mt-2">
                  <strong>Note:</strong> Webhook subscriptions will also be removed.
                </p>
              )}
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowConfirmDialog(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Disconnect
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

ConnectionHealth.propTypes = {
  connection: PropTypes.shape({
    id: PropTypes.string.isRequired,
    platform: PropTypes.string.isRequired,
    platform_account_id: PropTypes.string.isRequired,
    platform_username: PropTypes.string.isRequired,
    connection_name: PropTypes.string.isRequired,
    scopes: PropTypes.arrayOf(PropTypes.string),
    webhook_subscribed: PropTypes.bool.isRequired,
    expires_at: PropTypes.string,
    expires_in_hours: PropTypes.number,
    needs_reconnect: PropTypes.bool.isRequired,
    created_at: PropTypes.string.isRequired
  }).isRequired,
  onDisconnect: PropTypes.func.isRequired,
  onReconnect: PropTypes.func.isRequired,
  isDisconnecting: PropTypes.bool
};

export default ConnectionHealth;