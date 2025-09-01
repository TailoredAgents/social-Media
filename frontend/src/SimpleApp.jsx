function SimpleApp() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          🚀 AI Social Media Content Agent
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900">Total Posts</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">156</p>
            <p className="text-sm text-gray-600 mt-1">+12% this week</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900">Engagement Rate</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">4.2%</p>
            <p className="text-sm text-gray-600 mt-1">+0.8% this week</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900">Followers</h3>
            <p className="text-3xl font-bold text-purple-600 mt-2">2,750</p>
            <p className="text-sm text-gray-600 mt-1">+342 this month</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900">AI Status</h3>
            <p className="text-3xl font-bold text-orange-600 mt-2">Active</p>
            <p className="text-sm text-gray-600 mt-1">Cycle #142 running</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">🤖 Autonomous Workflow Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-green-900">Daily Research</h3>
                <p className="text-sm text-green-700">Completed at 6:00 AM</p>
              </div>
              <span className="px-3 py-1 bg-green-200 text-green-800 text-sm rounded-full">✓ Done</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-blue-900">Content Generation</h3>
                <p className="text-sm text-blue-700">Currently running...</p>
              </div>
              <span className="px-3 py-1 bg-blue-200 text-blue-800 text-sm rounded-full">🔄 Active</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-gray-900">Automated Posting</h3>
                <p className="text-sm text-gray-700">Scheduled for 3:00 PM</p>
              </div>
              <span className="px-3 py-1 bg-gray-200 text-gray-800 text-sm rounded-full">⏳ Pending</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">🧠 Memory System</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Content Items Stored:</span>
                <span className="font-semibold">245</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Research Articles:</span>
                <span className="font-semibold">45</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Generated Posts:</span>
                <span className="font-semibold">156</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Repurpose Ready:</span>
                <span className="font-semibold text-green-600">23</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">🎯 Active Goals</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>LinkedIn Growth</span>
                  <span>92%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: '92%'}}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Engagement Rate</span>
                  <span>85%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '85%'}}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Monthly Content</span>
                  <span>75%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-yellow-600 h-2 rounded-full" style={{width: '75%'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-gray-600">
            🚀 Enterprise AI Social Media Content Agent - Fully Operational
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Backend API: <span className="text-green-600 font-mono">http://localhost:8000</span> • 
            Frontend: <span className="text-blue-600 font-mono">http://localhost:5173</span>
          </p>
        </div>
      </div>
    </div>
  )
}

export default SimpleApp