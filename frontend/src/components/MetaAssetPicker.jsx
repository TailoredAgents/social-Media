import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const MetaAssetPicker = ({ 
  state, 
  onConnect, 
  onCancel,
  isLoading = false 
}) => {
  const [pages, setPages] = useState([]);
  const [selectedPage, setSelectedPage] = useState(null);
  const [selectedInstagram, setSelectedInstagram] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    loadMetaAssets();
  }, [state]);

  const loadMetaAssets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const partnerOAuthService = (await import('../services/partnerOAuth.js')).default;
      const result = await partnerOAuthService.getMetaAssets(state);
      
      setPages(result.pages || []);
      
      // Auto-select first page if only one available
      if (result.pages?.length === 1) {
        setSelectedPage(result.pages[0]);
        
        // Auto-select Instagram if only one page and it has Instagram
        if (result.pages[0].has_instagram && result.pages[0].instagram_business_account) {
          setSelectedInstagram(result.pages[0].instagram_business_account);
        }
      }
    } catch (err) {
      console.error('Failed to load Meta assets:', err);
      setError(err.message || 'Failed to load Facebook Pages');
    } finally {
      setLoading(false);
    }
  };

  const handlePageSelect = (page) => {
    setSelectedPage(page);
    
    // Clear Instagram selection if new page doesn't have Instagram
    if (!page.has_instagram) {
      setSelectedInstagram(null);
    }
  };

  const handleConnect = async () => {
    if (!selectedPage) {
      return;
    }

    try {
      setConnecting(true);
      
      const partnerOAuthService = (await import('../services/partnerOAuth.js')).default;
      const result = await partnerOAuthService.connectMeta(
        state,
        selectedPage.id,
        selectedInstagram?.id
      );
      
      onConnect(result);
    } catch (err) {
      console.error('Failed to connect Meta account:', err);
      setError(err.message || 'Failed to connect Meta account');
    } finally {
      setConnecting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl mx-auto p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading Facebook Pages...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-auto">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                Select Facebook Page
              </h2>
              <button
                onClick={onCancel}
                className="text-gray-400 hover:text-gray-600"
                disabled={connecting}
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="mt-1 text-sm text-gray-600">
              Choose which Facebook Page to connect. Instagram Business accounts linked to your pages will also be available.
            </p>
          </div>

          <div className="px-6 py-4 max-h-96 overflow-y-auto">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {pages.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No Facebook Pages Found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    You don't have admin access to any Facebook Pages, or no pages are available.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {pages.map((page) => (
                  <div
                    key={page.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedPage?.id === page.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handlePageSelect(page)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                            📘
                          </div>
                        </div>
                        <div className="ml-3">
                          <h3 className="font-medium text-gray-900">{page.name}</h3>
                          <p className="text-sm text-gray-500">Facebook Page</p>
                          
                          {page.has_instagram && page.instagram_business_account && (
                            <div className="flex items-center mt-2">
                              <span className="text-sm text-green-600 font-medium">
                                📸 Instagram: @{page.instagram_business_account.username}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end space-y-1">
                        {page.token_available ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Admin Access
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Limited Access
                          </span>
                        )}
                        
                        {selectedPage?.id === page.id && (
                          <div className="flex items-center">
                            <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </div>

                    {selectedPage?.id === page.id && page.has_instagram && page.instagram_business_account && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={selectedInstagram?.id === page.instagram_business_account.id}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedInstagram(page.instagram_business_account);
                              } else {
                                setSelectedInstagram(null);
                              }
                            }}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm font-medium text-gray-900">
                            Also connect Instagram Business account
                          </span>
                        </label>
                        <p className="ml-6 text-xs text-gray-600">
                          @{page.instagram_business_account.username}
                        </p>
                      </div>
                    )}

                    {!page.token_available && (
                      <div className="mt-3 p-3 bg-yellow-50 rounded-lg">
                        <p className="text-xs text-yellow-800">
                          <strong>Note:</strong> You need admin access to this Facebook Page to manage posts and access Instagram features.
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                {selectedPage ? (
                  <span>
                    Selected: {selectedPage.name}
                    {selectedInstagram && ` + @${selectedInstagram.username}`}
                  </span>
                ) : (
                  'Please select a Facebook Page'
                )}
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={onCancel}
                  disabled={connecting}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  Cancel
                </button>
                
                <button
                  onClick={handleConnect}
                  disabled={!selectedPage || connecting || !selectedPage.token_available}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {connecting ? (
                    <span className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Connecting...
                    </span>
                  ) : (
                    'Connect'
                  )}
                </button>
              </div>
            </div>
            
            {selectedPage && !selectedPage.token_available && (
              <div className="mt-2 text-xs text-gray-600">
                Admin access required to connect this page
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

MetaAssetPicker.propTypes = {
  state: PropTypes.string.isRequired,
  onConnect: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  isLoading: PropTypes.bool
};

export default MetaAssetPicker;