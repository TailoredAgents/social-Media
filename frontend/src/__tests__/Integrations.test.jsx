import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Integrations from '../pages/Integrations';
import partnerOAuthService from '../services/partnerOAuth';

// Mock the service
jest.mock('../services/partnerOAuth');

// Mock environment variable
const originalEnv = process.env;

describe('Integrations Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  const renderWithRouter = (component) => {
    return render(
      <BrowserRouter>
        {component}
      </BrowserRouter>
    );
  };

  it('should not render when feature flag is disabled', () => {
    // Mock feature flag as disabled
    partnerOAuthService.isFeatureEnabled.mockReturnValue(false);
    
    const { container } = renderWithRouter(<Integrations />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should render integration page when feature flag is enabled', async () => {
    // Mock feature flag as enabled
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    
    renderWithRouter(<Integrations />);
    
    expect(screen.getByText('Integrations')).toBeInTheDocument();
    expect(screen.getByText('Connect your social media accounts to automate content publishing and engagement.')).toBeInTheDocument();
  });

  it('should show connect buttons when feature is enabled', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      expect(screen.getByText('Connect Facebook & Instagram')).toBeInTheDocument();
      expect(screen.getByText('Connect X')).toBeInTheDocument();
    });
  });

  it('should display existing connections', async () => {
    const mockConnections = [
      {
        id: 'conn-1',
        platform: 'meta',
        platform_username: 'TestPage',
        connection_name: 'Test Facebook Page',
        webhook_subscribed: true,
        needs_reconnect: false,
        expires_in_hours: 720,
        scopes: ['pages_show_list', 'pages_manage_posts'],
        created_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 'conn-2',
        platform: 'x',
        platform_username: 'testuser',
        connection_name: '@testuser',
        webhook_subscribed: false,
        needs_reconnect: true,
        expires_in_hours: 48,
        scopes: ['tweet.read', 'tweet.write'],
        created_at: '2024-01-02T00:00:00Z'
      }
    ];

    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: mockConnections });
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Facebook Page')).toBeInTheDocument();
      expect(screen.getByText('@testuser')).toBeInTheDocument();
    });
  });

  it('should show loading state initially', () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    // Mock a delayed response
    partnerOAuthService.listConnections.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ connections: [] }), 100))
    );
    
    renderWithRouter(<Integrations />);
    
    expect(screen.getByText('Loading connections...')).toBeInTheDocument();
  });

  it('should show empty state when no connections exist', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      expect(screen.getByText('No connected accounts')).toBeInTheDocument();
      expect(screen.getByText('Get started by connecting your first social media account.')).toBeInTheDocument();
    });
  });

  it('should handle connection loading error', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockRejectedValue(new Error('API Error'));
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should initiate Facebook OAuth flow when connect button is clicked', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    partnerOAuthService.startOAuthFlow.mockResolvedValue({ 
      auth_url: 'https://facebook.com/oauth',
      state: 'test-state'
    });
    partnerOAuthService.openOAuthPopup.mockResolvedValue({
      state: 'test-state',
      code: 'auth-code'
    });
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      const fbButton = screen.getByText('Connect Facebook & Instagram');
      fireEvent.click(fbButton);
    });

    await waitFor(() => {
      expect(partnerOAuthService.startOAuthFlow).toHaveBeenCalledWith('meta');
      expect(partnerOAuthService.openOAuthPopup).toHaveBeenCalledWith('https://facebook.com/oauth');
    });
  });

  it('should initiate X OAuth flow when connect button is clicked', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    partnerOAuthService.startOAuthFlow.mockResolvedValue({ 
      auth_url: 'https://twitter.com/oauth',
      state: 'test-state'
    });
    partnerOAuthService.openOAuthPopup.mockResolvedValue({
      state: 'test-state',
      code: 'auth-code'
    });
    partnerOAuthService.connectX.mockResolvedValue({
      connection_id: 'new-conn',
      username: 'testuser',
      user_id: 'user123'
    });
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      const xButton = screen.getByText('Connect X');
      fireEvent.click(xButton);
    });

    await waitFor(() => {
      expect(partnerOAuthService.startOAuthFlow).toHaveBeenCalledWith('x');
      expect(partnerOAuthService.connectX).toHaveBeenCalledWith('test-state');
    });
  });

  it('should show error message when OAuth fails', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    partnerOAuthService.startOAuthFlow.mockRejectedValue(new Error('OAuth failed'));
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      const xButton = screen.getByText('Connect X');
      fireEvent.click(xButton);
    });

    await waitFor(() => {
      expect(screen.getByText('OAuth failed')).toBeInTheDocument();
    });
  });

  it('should disable connect buttons during connection process', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    partnerOAuthService.listConnections.mockResolvedValue({ connections: [] });
    
    // Mock a slow OAuth flow
    partnerOAuthService.startOAuthFlow.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        auth_url: 'https://twitter.com/oauth',
        state: 'test-state'
      }), 100))
    );
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      const xButton = screen.getByText('Connect X');
      fireEvent.click(xButton);
    });

    // Button should show connecting state
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('should refresh connections after successful connection', async () => {
    partnerOAuthService.isFeatureEnabled.mockReturnValue(true);
    
    // First call returns empty, second call returns connection
    partnerOAuthService.listConnections
      .mockResolvedValueOnce({ connections: [] })
      .mockResolvedValueOnce({ 
        connections: [{
          id: 'new-conn',
          platform: 'x',
          platform_username: 'newuser',
          connection_name: '@newuser',
          webhook_subscribed: false,
          needs_reconnect: false,
          scopes: ['tweet.read'],
          created_at: '2024-01-01T00:00:00Z'
        }]
      });
    
    partnerOAuthService.startOAuthFlow.mockResolvedValue({ 
      auth_url: 'https://twitter.com/oauth',
      state: 'test-state'
    });
    partnerOAuthService.openOAuthPopup.mockResolvedValue({
      state: 'test-state',
      code: 'auth-code'
    });
    partnerOAuthService.connectX.mockResolvedValue({
      connection_id: 'new-conn',
      username: 'newuser'
    });
    
    renderWithRouter(<Integrations />);
    
    await waitFor(() => {
      const xButton = screen.getByText('Connect X');
      fireEvent.click(xButton);
    });

    // Should refresh connections and show new connection
    await waitFor(() => {
      expect(screen.getByText('@newuser')).toBeInTheDocument();
    });
    
    // Should have called listConnections twice (initial load + refresh)
    expect(partnerOAuthService.listConnections).toHaveBeenCalledTimes(2);
  });
});