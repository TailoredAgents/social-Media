import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, AlertCircle, Info, RefreshCw, Download, Activity, Wifi, WifiOff } from 'lucide-react';
import apiService from '../services/api';
import errorReporter from '../utils/errorReporter.jsx';

const ErrorLogs = () => {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false); // Disabled to prevent CORS cascades
  const [wsConnected, setWsConnected] = useState(false);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [showingLocalLogs, setShowingLocalLogs] = useState(false);
  const wsRef = useRef(null);
  const refreshIntervalRef = useRef(null);

  // Fetch logs
  const fetchLogs = async () => {
    try {
      const response = await apiService.request(`/api/system/logs?log_type=${filter}&limit=100`);
      setLogs(response.logs || []);
      setBackendAvailable(true);
      setShowingLocalLogs(false);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setBackendAvailable(false);
      // Fallback to local logs
      const localLogs = errorReporter.getLocalErrors(100);
      setLogs(localLogs);
      setShowingLocalLogs(true);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await apiService.request('/api/system/logs/stats');
      setStats(response);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Generate local stats
      const localLogs = errorReporter.getLocalErrors();
      const localStats = {
        total_errors: localLogs.filter(log => log.severity === 'error' || log.type === 'network-error').length,
        total_warnings: localLogs.filter(log => log.severity === 'warning').length,
        errors_last_hour: localLogs.filter(log => {
          const hourAgo = new Date(Date.now() - 60 * 60 * 1000);
          return new Date(log.timestamp) > hourAgo;
        }).length,
        errors_last_day: localLogs.filter(log => {
          const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
          return new Date(log.timestamp) > dayAgo;
        }).length
      };
      setStats(localStats);
    }
  };

  // Initialize WebSocket for real-time updates
  const initWebSocket = () => {
    const wsUrl = `${apiService.baseURL.replace('http', 'ws')}/api/system/logs/stream`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setWsConnected(true);
        console.log('Connected to log stream');
      };
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'error' || message.type === 'warning') {
          // Add new log to the beginning of the list
          setLogs(prevLogs => [message.data, ...prevLogs.slice(0, 99)]);
          
          // Update stats if needed
          if (message.type === 'error') {
            setStats(prev => ({
              ...prev,
              total_errors: (prev?.total_errors || 0) + 1,
              errors_last_hour: (prev?.errors_last_hour || 0) + 1
            }));
          }
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
      wsRef.current.onclose = () => {
        setWsConnected(false);
        // Reconnect after 5 seconds
        setTimeout(initWebSocket, 5000);
      };
      
      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send('ping');
        }
      }, 30000);
      
      return () => clearInterval(pingInterval);
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchStats();
    
    // Initialize WebSocket
    const cleanupWs = initWebSocket();
    
    // Auto-refresh setup
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(() => {
        fetchLogs();
        fetchStats();
      }, 10000); // Refresh every 10 seconds
    }
    
    setLoading(false);
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (cleanupWs) {
        cleanupWs();
      }
    };
  }, [filter, autoRefresh]);

  // Log severity icon and color
  const getLogIcon = (log) => {
    const severity = log.severity || log.level || log.log_type;
    
    switch (severity?.toLowerCase()) {
      case 'error':
      case 'critical':
        return <AlertCircle className="text-red-500" size={20} />;
      case 'warning':
        return <AlertTriangle className="text-yellow-500" size={20} />;
      default:
        return <Info className="text-blue-500" size={20} />;
    }
  };

  // Export logs
  const exportLogs = async (format = 'json') => {
    try {
      const response = await apiService.request(
        `/api/system/logs/export?format=${format}&log_type=${filter}`
      );
      
      // Create download link
      const blob = new Blob(
        [format === 'json' ? JSON.stringify(response.logs, null, 2) : response],
        { type: format === 'json' ? 'application/json' : 'text/csv' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `error_logs_${new Date().toISOString()}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">System Logs & Errors</h2>
          <p className="text-gray-600 mt-1">
            Monitor live errors and system logs from your Render deployment
          </p>
          <p className="text-sm text-pink-600 mt-2 italic">
            💗 They make me write down everytime I hiccup 😊
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Backend Status */}
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
            backendAvailable ? 'bg-green-100' : 'bg-red-100'
          }`}>
            {backendAvailable ? (
              <Wifi className="text-green-500" size={16} />
            ) : (
              <WifiOff className="text-red-500" size={16} />
            )}
            <span className="text-sm">
              {backendAvailable ? 'Backend Connected' : 'Backend Down'}
            </span>
          </div>

          {/* WebSocket Status */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100">
            <Activity 
              className={wsConnected ? 'text-green-500' : 'text-gray-400'} 
              size={16} 
            />
            <span className="text-sm">
              {wsConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1 rounded-md text-sm ${
              autoRefresh 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
          </button>
          
          {/* Manual refresh */}
          <button
            onClick={() => {
              fetchLogs();
              fetchStats();
            }}
            className="p-2 hover:bg-gray-100 rounded-md"
          >
            <RefreshCw size={20} />
          </button>
          
          {/* Export */}
          <button
            onClick={() => exportLogs('json')}
            className="p-2 hover:bg-gray-100 rounded-md"
            title="Export as JSON"
          >
            <Download size={20} />
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-red-600">
              {stats.total_errors || 0}
            </div>
            <div className="text-sm text-gray-600">Total Errors</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-yellow-600">
              {stats.total_warnings || 0}
            </div>
            <div className="text-sm text-gray-600">Total Warnings</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-red-500">
              {stats.errors_last_hour || 0}
            </div>
            <div className="text-sm text-gray-600">Errors (Last Hour)</div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-red-400">
              {stats.errors_last_day || 0}
            </div>
            <div className="text-sm text-gray-600">Errors (Last 24h)</div>
          </div>
        </div>
      )}

      {/* Backend Status Banner */}
      {showingLocalLogs && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <div>
              <h3 className="font-medium text-yellow-800">Showing Local Error Logs</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Backend is unavailable. Displaying {logs.length} errors stored locally in your browser.
                These errors are automatically captured from your console.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['all', 'error', 'warning', 'info'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-4 py-2 rounded-md capitalize ${
              filter === type
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Time
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Endpoint
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Message
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                    No logs found
                  </td>
                </tr>
              ) : (
                logs.map((log, index) => (
                  <tr key={log.id || index} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      {getLogIcon(log)}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-600">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-sm font-mono">
                      {log.endpoint || log.module || '-'}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <div className="max-w-md truncate">
                        {log.message || log.error_message || '-'}
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <details className="cursor-pointer">
                        <summary className="text-blue-600 hover:text-blue-800">
                          View
                        </summary>
                        <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                          {JSON.stringify(log, null, 2)}
                        </pre>
                      </details>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Error Endpoints */}
      {stats?.top_error_endpoints && Object.keys(stats.top_error_endpoints).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Top Error Endpoints</h3>
          <div className="space-y-2">
            {Object.entries(stats.top_error_endpoints).slice(0, 5).map(([endpoint, count]) => (
              <div key={endpoint} className="flex justify-between items-center">
                <span className="font-mono text-sm">{endpoint}</span>
                <span className="text-red-600 font-semibold">{count} errors</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ErrorLogs;