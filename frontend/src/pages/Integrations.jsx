import React, { useState, useEffect } from 'react';
import ConnectionHealth from '../components/ConnectionHealth';
import MetaAssetPicker from '../components/MetaAssetPicker';
import partnerOAuthService from '../services/partnerOAuth';

const Integrations = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [disconnectingIds, setDisconnectingIds] = useState(new Set());
  
  // Modal states
  const [showMetaAssetPicker, setShowMetaAssetPicker] = useState(false);
  const [metaOAuthState, setMetaOAuthState] = useState(null);
  
  // Connection flow states
  const [connectingPlatform, setConnectingPlatform] = useState(null);

  useEffect(() => {
    // Check if feature is enabled
    if (!partnerOAuthService.isFeatureEnabled()) {
      setError('Partner OAuth feature is not enabled');
      setLoading(false);
      return;
    }
    
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await partnerOAuthService.listConnections();
      setConnections(result.connections || []);
    } catch (err) {
      console.error('Failed to load connections:', err);
      setError(err.message || 'Failed to load connections');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectFacebook = async () => {
    try {
      setConnectingPlatform('meta');
      
      const oauthResult = await partnerOAuthService.startOAuthFlow('meta');
      
      // Open OAuth popup
      const callback = await partnerOAuthService.openOAuthPopup(oauthResult.auth_url);
      
      if (callback.error) {
        throw new Error(callback.error_description || callback.error);
      }
      
      // Show asset picker with state from callback
      setMetaOAuthState(callback.state);
      setShowMetaAssetPicker(true);
      
    } catch (err) {
      console.error('Facebook connection failed:', err);
      setError(err.message || 'Failed to connect Facebook account');
    } finally {
      setConnectingPlatform(null);
    }
  };

  const handleConnectX = async () => {
    try {
      setConnectingPlatform('x');
      
      const oauthResult = await partnerOAuthService.startOAuthFlow('x');
      
      // Open OAuth popup
      const callback = await partnerOAuthService.openOAuthPopup(oauthResult.auth_url);
      
      if (callback.error) {
        throw new Error(callback.error_description || callback.error);
      }
      
      // Directly connect X account (no asset picker needed)
      const connectResult = await partnerOAuthService.connectX(callback.state);
      
      // Reload connections
      await loadConnections();
      
      // Show success notification
      setError(null);
      
    } catch (err) {
      console.error('X connection failed:', err);
      setError(err.message || 'Failed to connect X account');
    } finally {
      setConnectingPlatform(null);
    }
  };

  const handleMetaConnect = async (connectResult) => {
    try {
      setShowMetaAssetPicker(false);
      setMetaOAuthState(null);
      
      // Reload connections to show new connection
      await loadConnections();
      
      // Clear any previous errors
      setError(null);
      
    } catch (err) {
      console.error('Failed to complete Meta connection:', err);
      setError(err.message || 'Failed to complete Meta connection');
    }
  };

  const handleDisconnect = async (connectionId) => {
    try {
      setDisconnectingIds(prev => new Set([...prev, connectionId]));
      
      await partnerOAuthService.disconnectConnection(connectionId);
      
      // Reload connections
      await loadConnections();
      
      // Clear any previous errors
      setError(null);
      
    } catch (err) {
      console.error('Failed to disconnect:', err);
      setError(err.message || 'Failed to disconnect connection');
    } finally {
      setDisconnectingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(connectionId);
        return newSet;
      });
    }
  };

  const handleReconnect = async (platform) => {
    // Reconnect by starting the OAuth flow again
    if (platform === 'meta') {
      await handleConnectFacebook();
    } else if (platform === 'x') {
      await handleConnectX();
    }
  };

  // Don't render if feature is disabled
  if (!partnerOAuthService.isFeatureEnabled()) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
          <p className="mt-2 text-gray-600">
            Connect your social media accounts to automate content publishing and engagement.
          </p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm">{error}</p>
              </div>
              <div className="ml-auto pl-3">
                <button
                  onClick={() => setError(null)}
                  className="text-red-400 hover:text-red-600"
                >
                  <span className="sr-only">Dismiss</span>
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Connect New Platform Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Connect New Platform</h2>
            <p className="mt-1 text-sm text-gray-600">
              Add new social media accounts to expand your reach.
            </p>
          </div>
          
          <div className="px-6 py-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Facebook & Instagram Button */}
              <button
                onClick={handleConnectFacebook}
                disabled={connectingPlatform === 'meta'}
                className="flex items-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white text-lg font-semibold">
                    📘
                  </div>
                  <div className="ml-4 text-left">
                    <h3 className="text-sm font-medium text-gray-900">
                      {connectingPlatform === 'meta' ? 'Connecting...' : 'Connect Facebook & Instagram'}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Connect your Facebook Pages and Instagram Business accounts
                    </p>
                  </div>
                  {connectingPlatform === 'meta' && (
                    <div className="ml-4">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
              </button>

              {/* X (Twitter) Button */}
              <button
                onClick={handleConnectX}
                disabled={connectingPlatform === 'x'}
                className="flex items-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center text-white text-lg font-semibold">
                    🐦
                  </div>
                  <div className="ml-4 text-left">
                    <h3 className="text-sm font-medium text-gray-900">
                      {connectingPlatform === 'x' ? 'Connecting...' : 'Connect X'}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Connect your X (Twitter) account for posting and engagement
                    </p>
                  </div>
                  {connectingPlatform === 'x' && (
                    <div className="ml-4">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></div>
                    </div>
                  )}
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Connected Accounts Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Connected Accounts</h2>
            <p className="mt-1 text-sm text-gray-600">
              Manage your connected social media accounts and their permissions.
            </p>
          </div>
          
          <div className="px-6 py-6">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Loading connections...</span>
              </div>
            ) : connections.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No connected accounts</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Get started by connecting your first social media account.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {connections.map((connection) => (
                  <ConnectionHealth
                    key={connection.id}
                    connection={connection}
                    onDisconnect={handleDisconnect}
                    onReconnect={handleReconnect}
                    isDisconnecting={disconnectingIds.has(connection.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Meta Asset Picker Modal */}
      {showMetaAssetPicker && metaOAuthState && (
        <MetaAssetPicker
          state={metaOAuthState}
          onConnect={handleMetaConnect}
          onCancel={() => {
            setShowMetaAssetPicker(false);
            setMetaOAuthState(null);
          }}
        />
      )}
    </div>
  );
};

export default Integrations;