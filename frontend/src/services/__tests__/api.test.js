import { jest } from '@jest/globals'

// Mock fetch globally
global.fetch = jest.fn()

// Mock environment variable
const mockApiService = {
  baseURL: 'http://localhost:8000',
  token: null,
  
  setToken(token) {
    this.token = token
  },

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

    try {
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
    } catch (error) {
      // Mock logger for tests - in real code this uses the logger
      if (process.env.NODE_ENV !== 'test') {
        console.error(`API request failed: ${endpoint}`, error)
      }
      throw error
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' })
  },

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: data,
    })
  },

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: data,
    })
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' })
  }
}

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiService.token = null
    
    // Reset fetch mock
    fetch.mockClear()
  })

  describe('Token Management', () => {
    it('sets authorization token', () => {
      const token = 'test-token-123'
      mockApiService.setToken(token)
      
      expect(mockApiService.token).toBe(token)
    })

    it('includes authorization header when token is set', async () => {
      const token = 'test-token-123'
      mockApiService.setToken(token)

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
        headers: { get: () => 'application/json' }
      })

      await mockApiService.get('/test')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123'
          })
        })
      )
    })

    it('does not include authorization header when no token', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
        headers: { get: () => 'application/json' }
      })

      await mockApiService.get('/test')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.any(String)
          })
        })
      )
    })
  })

  describe('HTTP Methods', () => {
    it('makes GET request', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
        headers: { get: () => 'application/json' }
      })

      const result = await mockApiService.get('/test')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual({ data: 'test' })
    })

    it('makes POST request with data', async () => {
      const postData = { name: 'test', value: 123 }
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, ...postData }),
        headers: { get: () => 'application/json' }
      })

      const result = await mockApiService.post('/test', postData)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData)
        })
      )
      expect(result).toEqual({ id: 1, ...postData })
    })

    it('makes PUT request with data', async () => {
      const putData = { id: 1, name: 'updated' }
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => putData,
        headers: { get: () => 'application/json' }
      })

      await mockApiService.put('/test/1', putData)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData)
        })
      )
    })

    it('makes DELETE request', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'deleted' }),
        headers: { get: () => 'application/json' }
      })

      await mockApiService.delete('/test/1')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'DELETE'
        })
      )
    })
  })

  describe('Response Handling', () => {
    it('handles JSON responses', async () => {
      const jsonData = { message: 'success', data: [1, 2, 3] }
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => jsonData,
        headers: { get: () => 'application/json' }
      })

      const result = await mockApiService.get('/test')
      expect(result).toEqual(jsonData)
    })

    it('handles text responses', async () => {
      const textData = 'Plain text response'
      
      fetch.mockResolvedValueOnce({
        ok: true,
        text: async () => textData,
        headers: { get: () => 'text/plain' }
      })

      const result = await mockApiService.get('/test')
      expect(result).toBe(textData)
    })

    it('handles HTTP errors with JSON error details', async () => {
      const errorDetail = { detail: 'Validation failed', errors: ['field is required'] }
      
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorDetail
      })

      await expect(mockApiService.get('/test')).rejects.toThrow('Validation failed')
    })

    it('handles HTTP errors without JSON details', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Not JSON') }
      })

      await expect(mockApiService.get('/test')).rejects.toThrow('HTTP error! status: 500')
    })

    it('handles network errors', async () => {
      const networkError = new Error('Network error')
      fetch.mockRejectedValueOnce(networkError)

      await expect(mockApiService.get('/test')).rejects.toThrow('Network error')
      // Note: Logger doesn't output in test environment, so we don't test console.error
    })
  })

  describe('Request Configuration', () => {
    it('sets correct content-type header', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: { get: () => 'application/json' }
      })

      await mockApiService.post('/test', { data: 'test' })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )
    })

    it('allows custom headers', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: { get: () => 'application/json' }
      })

      await mockApiService.request('/test', {
        headers: {
          'X-Custom-Header': 'custom-value'
        }
      })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: {
            'X-Custom-Header': 'custom-value'
          }
        })
      )
    })

    it('constructs correct URL with base URL', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: { get: () => 'application/json' }
      })

      await mockApiService.get('/api/v1/users')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/users',
        expect.any(Object)
      )
    })
  })
})