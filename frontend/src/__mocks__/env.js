// Mock environment variables for Jest tests
global.import = global.import || {}
global.import.meta = global.import.meta || {}
global.import.meta.env = {
  VITE_AUTH0_DOMAIN: 'test-domain.auth0.com',
  VITE_AUTH0_CLIENT_ID: 'test-client-id',
  VITE_AUTH0_AUDIENCE: 'test-audience',
  VITE_API_BASE_URL: 'http://localhost:8000',
  NODE_ENV: 'test',
  MODE: 'test'
}

// Also set on process.env for compatibility
process.env.VITE_AUTH0_DOMAIN = 'test-domain.auth0.com'
process.env.VITE_AUTH0_CLIENT_ID = 'test-client-id'
process.env.VITE_AUTH0_AUDIENCE = 'test-audience'
process.env.VITE_API_BASE_URL = 'http://localhost:8000'
process.env.NODE_ENV = 'test'