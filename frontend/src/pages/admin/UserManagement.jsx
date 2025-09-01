import { useState, useEffect } from 'react'
import { useAdminAuth } from '../../contexts/AdminAuthContext'

const UserManagement = () => {
  const { adminApi } = useAdminAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selectedUser, setSelectedUser] = useState(null)
  const [showUserModal, setShowUserModal] = useState(false)
  const [actionLoading, setActionLoading] = useState(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const usersData = await adminApi.getUsers()
      setUsers(usersData.users || [])
    } catch (error) {
      console.error('Failed to load users:', error)
      setError('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const handleUserClick = async (user) => {
    try {
      const userDetails = await adminApi.getUserDetails(user.id)
      setSelectedUser(userDetails)
      setShowUserModal(true)
    } catch (error) {
      console.error('Failed to load user details:', error)
    }
  }

  const generateApiKey = async (userId) => {
    try {
      setActionLoading(`api-key-${userId}`)
      const result = await adminApi.generateApiKey(userId)
      
      // Show the API key in a modal or alert
      alert(`API Key generated successfully:\n\nAPI Key: ${result.api_key}\nAPI Secret: ${result.api_secret}\n\nPlease save these securely - they won't be shown again!`)
      
      // Refresh user data
      if (selectedUser && selectedUser.id === userId) {
        const updatedUser = await adminApi.getUserDetails(userId)
        setSelectedUser(updatedUser)
      }
      await loadUsers()
    } catch (error) {
      console.error('Failed to generate API key:', error)
      alert('Failed to generate API key: ' + error.message)
    } finally {
      setActionLoading(null)
    }
  }

  const revokeApiKey = async (userId, reason = 'Admin revocation') => {
    try {
      setActionLoading(`revoke-${userId}`)
      await adminApi.revokeApiKey(userId, reason)
      
      // Refresh user data
      if (selectedUser && selectedUser.id === userId) {
        const updatedUser = await adminApi.getUserDetails(userId)
        setSelectedUser(updatedUser)
      }
      await loadUsers()
    } catch (error) {
      console.error('Failed to revoke API key:', error)
      alert('Failed to revoke API key: ' + error.message)
    } finally {
      setActionLoading(null)
    }
  }

  const updateUserStatus = async (userId, updates) => {
    try {
      setActionLoading(`status-${userId}`)
      await adminApi.updateUserManagement(userId, updates)
      
      // Refresh user data
      if (selectedUser && selectedUser.id === userId) {
        const updatedUser = await adminApi.getUserDetails(userId)
        setSelectedUser(updatedUser)
      }
      await loadUsers()
    } catch (error) {
      console.error('Failed to update user:', error)
      alert('Failed to update user: ' + error.message)
    } finally {
      setActionLoading(null)
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.full_name?.toLowerCase().includes(searchTerm.toLowerCase())
    
    if (!matchesSearch) return false
    
    if (filterStatus === 'all') return true
    if (filterStatus === 'active') return user.is_active
    if (filterStatus === 'inactive') return !user.is_active
    if (filterStatus === 'suspended') return user.user_management?.is_suspended
    if (filterStatus === 'verified') return user.user_management?.is_verified
    
    return true
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <button 
          onClick={loadUsers}
          className="mt-2 text-sm underline hover:no-underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-5">
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          User Management
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage user accounts, API keys, and permissions
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Search */}
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700">
                Search Users
              </label>
              <input
                type="text"
                id="search"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                placeholder="Search by email, username, or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Status Filter */}
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                Status Filter
              </label>
              <select
                id="status"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="all">All Users</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
                <option value="verified">Verified</option>
              </select>
            </div>

            {/* Stats */}
            <div className="flex items-end">
              <div className="text-sm text-gray-500">
                Showing {filteredUsers.length} of {users.length} users
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                API Access
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-red-500 flex items-center justify-center">
                        <span className="text-sm font-medium text-white">
                          {user.email.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {user.full_name || user.username || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">
                        {user.email}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-col space-y-1">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {user.user_management?.is_suspended && (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        Suspended
                      </span>
                    )}
                    {user.user_management?.is_verified && (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        Verified
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {user.user_management?.api_key ? (
                    <div>
                      <div className="text-green-600 font-medium">Has API Key</div>
                      <div className="text-xs">
                        Used: {user.user_management.api_key_usage_count || 0} times
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-400">No API Key</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => handleUserClick(user)}
                    className="text-red-600 hover:text-red-900 mr-4"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredUsers.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No users found matching your criteria.</p>
          </div>
        )}
      </div>

      {/* User Details Modal */}
      {showUserModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              {/* Modal Header */}
              <div className="flex items-center justify-between pb-3 border-b">
                <h3 className="text-lg font-medium text-gray-900">
                  User Details: {selectedUser.email}
                </h3>
                <button
                  onClick={() => setShowUserModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="mt-4 space-y-4">
                {/* User Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <p className="text-sm text-gray-900">{selectedUser.email}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Username</label>
                    <p className="text-sm text-gray-900">{selectedUser.username || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Full Name</label>
                    <p className="text-sm text-gray-900">{selectedUser.full_name || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Created</label>
                    <p className="text-sm text-gray-900">{new Date(selectedUser.created_at).toLocaleString()}</p>
                  </div>
                </div>

                {/* API Key Management */}
                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-2">API Key Management</h4>
                  {selectedUser.user_management?.api_key ? (
                    <div className="space-y-2">
                      <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                        <div>
                          <p className="font-medium text-green-800">API Key Active</p>
                          <p className="text-sm text-green-600">
                            Created: {new Date(selectedUser.user_management.api_key_created_at).toLocaleString()}
                          </p>
                          <p className="text-sm text-green-600">
                            Usage: {selectedUser.user_management.api_key_usage_count || 0} times
                          </p>
                        </div>
                        <button
                          onClick={() => revokeApiKey(selectedUser.id)}
                          disabled={actionLoading === `revoke-${selectedUser.id}`}
                          className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          {actionLoading === `revoke-${selectedUser.id}` ? 'Revoking...' : 'Revoke'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-gray-600 mb-2">No API key generated</p>
                      <button
                        onClick={() => generateApiKey(selectedUser.id)}
                        disabled={actionLoading === `api-key-${selectedUser.id}`}
                        className="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                      >
                        {actionLoading === `api-key-${selectedUser.id}` ? 'Generating...' : 'Generate API Key'}
                      </button>
                    </div>
                  )}
                </div>

                {/* User Status Management */}
                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-2">Status Management</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedUser.is_active}
                          onChange={(e) => updateUserStatus(selectedUser.id, { is_active: e.target.checked })}
                          disabled={actionLoading === `status-${selectedUser.id}`}
                          className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Active</span>
                      </label>
                    </div>
                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedUser.user_management?.is_verified || false}
                          onChange={(e) => updateUserStatus(selectedUser.id, { is_verified: e.target.checked })}
                          disabled={actionLoading === `status-${selectedUser.id}`}
                          className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Verified</span>
                      </label>
                    </div>
                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedUser.user_management?.is_suspended || false}
                          onChange={(e) => updateUserStatus(selectedUser.id, { is_suspended: e.target.checked })}
                          disabled={actionLoading === `status-${selectedUser.id}`}
                          className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Suspended</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowUserModal(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserManagement