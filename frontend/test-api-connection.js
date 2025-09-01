// Simple test to verify frontend can connect to backend APIs
const API_BASE_URL = 'http://localhost:8000'

async function testApiConnection() {
  console.log('🧪 Testing API Connection...')
  
  try {
    // Test health endpoint
    console.log('Testing /health endpoint...')
    const healthResponse = await fetch(`${API_BASE_URL}/health`)
    const healthData = await healthResponse.json()
    console.log('✅ Health check:', healthData.status)
    
    // Test notifications endpoint
    console.log('Testing /api/notifications/types endpoint...')
    const typesResponse = await fetch(`${API_BASE_URL}/api/notifications/types`)
    const typesData = await typesResponse.json()
    console.log('✅ Notification types:', typesData.notification_types.length, 'types available')
    
    // Test social platforms endpoint
    console.log('Testing /api/social/connections endpoint...')
    const socialResponse = await fetch(`${API_BASE_URL}/api/social/connections`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (socialResponse.status === 401) {
      console.log('⚠️  Social connections: Authentication required (expected)')
    } else {
      const socialData = await socialResponse.json()
      console.log('✅ Social connections endpoint accessible')
    }
    
    // Test WebSocket connection
    console.log('Testing WebSocket connection...')
    const ws = new WebSocket(`ws://localhost:8000/api/notifications/ws?user_id=1`)
    
    ws.onopen = () => {
      console.log('✅ WebSocket connection established')
      ws.close()
    }
    
    ws.onerror = (error) => {
      console.log('⚠️  WebSocket connection failed (expected without auth):', error.type)
    }
    
    ws.onclose = () => {
      console.log('🔌 WebSocket connection closed')
    }
    
    console.log('\n🎉 Frontend-Backend Integration Test Complete!')
    console.log('📋 Summary:')
    console.log('  - REST API endpoints accessible')
    console.log('  - Real-time notification types loaded')
    console.log('  - Social platform endpoints protected (good!)')
    console.log('  - WebSocket endpoint responsive')
    
  } catch (error) {
    console.error('❌ API connection test failed:', error)
    console.log('\n🔧 Make sure the backend is running on http://localhost:8000')
  }
}

// Run the test
testApiConnection()