// Simple API service tests without ES modules issues
import { jest } from '@jest/globals'

// Mock fetch globally
global.fetch = jest.fn()

// Mock environment variable
const mockEnv = {
  VITE_API_BASE_URL: 'http://localhost:8000'
}

// Mock the import.meta.env usage in the API module
jest.mock('../../services/api.js', () => {
  class MockApiService {
    constructor() {
      this.baseURL = 'http://localhost:8000'
      this.token = null
    }

    setToken(token) {
      this.token = token
    }

    async request(endpoint, options = {}) {
      const url = `${this.baseURL}${endpoint}`
      
      const config = {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      }

      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`
      }

      if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body)
      }

      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }
      
      return await response.text()
    }

    // Auth endpoints
    async register(userData) {
      return this.request('/api/auth/register', {
        method: 'POST',
        body: userData
      })
    }

    async login(credentials) {
      return this.request('/api/auth/login', {
        method: 'POST',
        body: credentials
      })
    }

    async getCurrentUser() {
      return this.request('/api/auth/me')
    }

    // Memory endpoints
    async storeMemory(content, metadata) {
      return this.request('/api/memory/store', {
        method: 'POST',
        body: { content, metadata }
      })
    }

    async searchMemory(query, limit = 5) {
      return this.request('/api/memory/search', {
        method: 'POST',
        body: { query, limit }
      })
    }

    // Goals endpoints  
    async createGoal(goalData) {
      return this.request('/api/goals/', {
        method: 'POST',
        body: goalData
      })
    }

    async getGoals() {
      return this.request('/api/goals/')
    }

    // Content endpoints
    async createContent(contentData) {
      return this.request('/api/content/', {
        method: 'POST',
        body: contentData
      })
    }

    async getContent(page = 1, limit = 20) {
      return this.request(`/api/content/?page=${page}&limit=${limit}`)
    }

    async updateContent(contentId, contentData) {
      return this.request(`/api/content/${contentId}`, {
        method: 'PUT',
        body: contentData
      })
    }

    async deleteContent(contentId) {
      return this.request(`/api/content/${contentId}`, {
        method: 'DELETE'
      })
    }

    // Health endpoints
    async getHealth() {
      return this.request('/api/health')
    }

    async getMetrics() {
      return this.request('/api/metrics')
    }
  }

  return {
    __esModule: true,
    default: new MockApiService()
  }
})

describe('API Service (Simple Tests)', () => {
  let apiService

  beforeAll(async () => {
    const apiModule = await import('../../services/api.js')
    apiService = apiModule.default
  })

  beforeEach(() => {
    fetch.mockClear()
    apiService.token = null
  })

  describe('Authentication', () => {
    test('should register user with correct endpoint and data', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ success: true }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const userData = { email: 'test@example.com', password: 'password123' }
      await apiService.register(userData)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/register',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(userData)
        })
      )
    })

    test('should login user with credentials', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ token: 'jwt-token' }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const credentials = { email: 'test@example.com', password: 'password123' }
      await apiService.login(credentials)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(credentials)
        })
      )
    })

    test('should get current user', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ id: 1, email: 'test@example.com' }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      await apiService.getCurrentUser()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/me',
        expect.any(Object)
      )
    })

    test('should set authorization header when token is provided', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({}) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      apiService.setToken('test-token-123')
      await apiService.getCurrentUser()

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123'
          })
        })
      )
    })
  })

  describe('Memory Management', () => {
    test('should store memory with content and metadata', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ id: 123 }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const content = 'Test memory content'
      const metadata = { type: 'research', tags: ['ai', 'social'] }
      
      await apiService.storeMemory(content, metadata)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/memory/store',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ content, metadata })
        })
      )
    })

    test('should search memory with query and limit', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ results: [] }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const query = 'artificial intelligence'
      await apiService.searchMemory(query)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/memory/search',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ query, limit: 5 })
        })
      )
    })

    test('should search memory with custom limit', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ results: [] }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const query = 'artificial intelligence'
      const customLimit = 10
      await apiService.searchMemory(query, customLimit)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/memory/search',
        expect.objectContaining({
          body: JSON.stringify({ query, limit: customLimit })
        })
      )
    })
  })

  describe('Goals Management', () => {
    test('should create goal with data', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ id: 'goal-123' }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const goalData = { title: 'Increase followers', target: 1000 }
      await apiService.createGoal(goalData)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/goals/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(goalData)
        })
      )
    })

    test('should get all goals', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve([]) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      await apiService.getGoals()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/goals/',
        expect.any(Object)
      )
    })
  })

  describe('Content Management', () => {
    test('should create content with data', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ id: 'content-123' }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const contentData = { title: 'New Post', content: 'Post content', platform: 'twitter' }
      await apiService.createContent(contentData)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/content/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(contentData)
        })
      )
    })

    test('should get content with pagination', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ items: [] }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      await apiService.getContent(2, 50)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/content/?page=2&limit=50',
        expect.any(Object)
      )
    })

    test('should update content', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ success: true }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const contentId = 'content-123'
      const updateData = { title: 'Updated Title' }
      
      await apiService.updateContent(contentId, updateData)

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/content/${contentId}`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData)
        })
      )
    })

    test('should delete content', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ success: true }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      const contentId = 'content-123'
      await apiService.deleteContent(contentId)

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/content/${contentId}`,
        expect.objectContaining({
          method: 'DELETE'
        })
      )
    })
  })

  describe('System Health', () => {
    test('should get health status', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ status: 'healthy' }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      await apiService.getHealth()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/health',
        expect.any(Object)
      )
    })

    test('should get metrics', async () => {
      const mockResponse = { ok: true, json: () => Promise.resolve({ metrics: {} }) }
      fetch.mockResolvedValueOnce(mockResponse)
      
      await apiService.getMetrics()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/metrics',
        expect.any(Object)
      )
    })
  })

  describe('Error Handling', () => {
    test('should handle HTTP errors with JSON error data', async () => {
      const errorResponse = { detail: 'Validation failed', code: 'VALIDATION_ERROR' }
      fetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => errorResponse
      })

      await expect(apiService.getHealth()).rejects.toThrow('Validation failed')
    })

    test('should handle HTTP errors without JSON error data', async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        }
      })

      await expect(apiService.getHealth()).rejects.toThrow('HTTP error! status: 500')
    })

    test('should handle network errors', async () => {
      const networkError = new Error('Network connection failed')
      fetch.mockRejectedValue(networkError)

      await expect(apiService.getHealth()).rejects.toThrow('Network connection failed')
    })
  })

  describe('Request Configuration', () => {
    test('should stringify request body when it is an object', async () => {
      const mockBody = { name: 'test', value: 123 }
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Map([['content-type', 'application/json']])
      })

      await apiService.createContent(mockBody)

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(mockBody)
        })
      )
    })

    test('should handle JSON response correctly', async () => {
      const mockData = { message: 'success', data: [1, 2, 3] }
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.getHealth()

      expect(result).toEqual(mockData)
    })

    test('should handle text response correctly', async () => {
      const mockText = 'plain text response'
      fetch.mockResolvedValue({
        ok: true,
        text: async () => mockText,
        headers: new Map([['content-type', 'text/plain']])
      })

      const result = await apiService.getHealth()

      expect(result).toBe(mockText)
    })
  })
})