/**
 * Partner OAuth API service
 * Handles social platform authentication flows
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class PartnerOAuthService {
  constructor() {
    this.baseUrl = `${API_BASE}/api/oauth`;
  }

  // Helper method to get auth headers
  getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  // Check if feature is enabled
  isFeatureEnabled() {
    return import.meta.env.VITE_FEATURE_PARTNER_OAUTH === 'true';
  }

  /**
   * Start OAuth flow for a platform
   * @param {string} platform - 'meta' or 'x'
   * @returns {Promise<{auth_url: string, state: string, platform: string}>}
   */
  async startOAuthFlow(platform) {
    if (!this.isFeatureEnabled()) {
      throw new Error('Partner OAuth feature is not enabled');
    }

    const response = await fetch(`${this.baseUrl}/${platform}/start`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || `Failed to start ${platform} OAuth flow`);
    }

    return await response.json();
  }

  /**
   * Get Meta assets after OAuth callback
   * @param {string} state - State parameter from callback
   * @returns {Promise<{pages: Array}>}
   */
  async getMetaAssets(state) {
    if (!this.isFeatureEnabled()) {
      throw new Error('Partner OAuth feature is not enabled');
    }

    const response = await fetch(`${this.baseUrl}/meta/assets?state=${encodeURIComponent(state)}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to get Meta assets');
    }

    return await response.json();
  }

  /**
   * Connect Meta account (Facebook Page + optional Instagram)
   * @param {string} state - State parameter
   * @param {string} pageId - Facebook Page ID
   * @param {string} instagramId - Instagram Business account ID (optional)
   * @returns {Promise<{connection_id: string, facebook_page: object, instagram_account?: object}>}
   */
  async connectMeta(state, pageId, instagramId = null) {
    if (!this.isFeatureEnabled()) {
      throw new Error('Partner OAuth feature is not enabled');
    }

    const requestBody = {
      state,
      page_id: pageId,
      ...(instagramId && { instagram_id: instagramId })
    };

    const response = await fetch(`${this.baseUrl}/meta/connect`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to connect Meta account');
    }

    return await response.json();
  }

  /**
   * Connect X account
   * @param {string} state - State parameter
   * @returns {Promise<{connection_id: string, username: string, user_id: string}>}
   */
  async connectX(state) {
    if (!this.isFeatureEnabled()) {
      throw new Error('Partner OAuth feature is not enabled');
    }

    const response = await fetch(`${this.baseUrl}/x/connect`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ state }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to connect X account');
    }

    return await response.json();
  }

  /**
   * List all connections for the organization
   * @returns {Promise<{connections: Array}>}
   */
  async listConnections() {
    if (!this.isFeatureEnabled()) {
      throw new Error('Partner OAuth feature is not enabled');
    }

    const response = await fetch(`${this.baseUrl}/connections`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to list connections');
    }

    return await response.json();
  }

  /**
   * Disconnect a connection
   * @param {string} connectionId - Connection ID to disconnect
   * @returns {Promise<{status: string, connection_id: string, revoked_at: string}>}
   */
  async disconnectConnection(connectionId) {
    if (!this.isFeatureEnabled()) {
      throw new Error('Partner OAuth feature is not enabled');
    }

    const response = await fetch(`${this.baseUrl}/${connectionId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ confirmation: true }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to disconnect connection');
    }

    return await response.json();
  }

  /**
   * Handle OAuth callback by parsing URL parameters
   * @param {string} url - Current URL with callback parameters
   * @returns {Promise<{platform: string, state: string, code?: string, error?: string}>}
   */
  parseCallback(url) {
    const urlParams = new URLSearchParams(url.split('?')[1] || '');
    
    // Extract platform from the URL path
    const pathMatch = url.match(/\/oauth\/(\w+)\/callback/);
    const platform = pathMatch ? pathMatch[1] : null;
    
    return {
      platform,
      state: urlParams.get('state'),
      code: urlParams.get('code'),
      error: urlParams.get('error'),
      error_description: urlParams.get('error_description')
    };
  }

  /**
   * Open OAuth popup window
   * @param {string} authUrl - OAuth authorization URL
   * @returns {Promise<{state: string, platform: string}>}
   */
  openOAuthPopup(authUrl) {
    return new Promise((resolve, reject) => {
      const popup = window.open(
        authUrl,
        'oauth-popup',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      );

      if (!popup) {
        reject(new Error('Failed to open OAuth popup. Please check popup blocker settings.'));
        return;
      }

      // Poll for popup closure or callback
      const checkPopup = setInterval(() => {
        try {
          if (popup.closed) {
            clearInterval(checkPopup);
            reject(new Error('OAuth flow was cancelled'));
            return;
          }

          // Try to access popup URL to detect callback
          try {
            const popupUrl = popup.location.href;
            if (popupUrl.includes('/callback')) {
              clearInterval(checkPopup);
              popup.close();
              
              const callback = this.parseCallback(popupUrl);
              if (callback.error) {
                reject(new Error(callback.error_description || callback.error));
              } else {
                resolve(callback);
              }
            }
          } catch (e) {
            // Cross-origin error is expected during OAuth flow
          }
        } catch (e) {
          clearInterval(checkPopup);
          popup.close();
          reject(new Error('OAuth flow encountered an error'));
        }
      }, 1000);

      // Timeout after 10 minutes
      setTimeout(() => {
        clearInterval(checkPopup);
        if (!popup.closed) {
          popup.close();
        }
        reject(new Error('OAuth flow timed out'));
      }, 600000);
    });
  }
}

export default new PartnerOAuthService();