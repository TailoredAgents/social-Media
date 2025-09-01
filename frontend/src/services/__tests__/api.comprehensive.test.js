import { jest } from '@jest/globals'

// Mock the logger
jest.mock('../../utils/logger.js', () => ({
  error: jest.fn()
}))

// Mock fetch globally
global.fetch = jest.fn()

// Import the API service after mocks are set up
import apiService from '../api.js'
import { error as logError } from '../../utils/logger.js'

describe('ApiService Comprehensive Tests', () => {
  beforeEach(() => {
    fetch.mockClear()
    logError.mockClear()
    apiService.token = null
  })

  describe('Basic Functionality', () => {
    it('should set and use authentication token', async () => {
      const mockResponse = { data: 'test' }
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
        headers: new Map([['content-type', 'application/json']])
      })

      apiService.setToken('test-token')

      await apiService.request('/test')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )
    })

    it('should handle JSON response correctly', async () => {
      const mockResponse = { message: 'success', data: [1, 2, 3] }
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.request('/test')

      expect(result).toEqual(mockResponse)
    })

    it('should handle text response correctly', async () => {
      const mockResponse = 'plain text response'
      fetch.mockResolvedValue({
        ok: true,
        text: async () => mockResponse,
        headers: new Map([['content-type', 'text/plain']])
      })

      const result = await apiService.request('/test')

      expect(result).toBe(mockResponse)
    })

    it('should stringify request body when it is an object', async () => {
      const mockBody = { name: 'test', value: 123 }
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Map([['content-type', 'application/json']])
      })

      await apiService.request('/test', {
        method: 'POST',
        body: mockBody
      })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(mockBody)
        })
      )
    })

    it('should pass through string body without modification', async () => {
      const mockBody = 'raw string data'
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Map([['content-type', 'application/json']])
      })

      await apiService.request('/test', {
        method: 'POST',
        body: mockBody
      })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: mockBody
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle HTTP error responses with JSON error data', async () => {
      const errorResponse = { detail: 'Validation failed', code: 'VALIDATION_ERROR' }
      fetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => errorResponse
      })

      await expect(apiService.request('/test')).rejects.toThrow('Validation failed')
      expect(logError).toHaveBeenCalledWith(
        'API request failed: /test',
        expect.any(Error)
      )
    })

    it('should handle HTTP error responses without JSON error data', async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        }
      })

      await expect(apiService.request('/test')).rejects.toThrow('HTTP error! status: 500')
      expect(logError).toHaveBeenCalledWith(
        'API request failed: /test',
        expect.any(Error)
      )
    })

    it('should handle network errors', async () => {
      const networkError = new Error('Network connection failed')
      fetch.mockRejectedValue(networkError)

      await expect(apiService.request('/test')).rejects.toThrow('Network connection failed')
      expect(logError).toHaveBeenCalledWith(
        'API request failed: /test',
        networkError
      )
    })

    it('should handle JSON parsing errors in error responses gracefully', async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => {
          throw new SyntaxError('Unexpected token')
        }
      })

      await expect(apiService.request('/test')).rejects.toThrow('HTTP error! status: 422')
    })
  })

  describe('Content Management API', () => {
    it('should fetch content correctly', async () => {
      const mockContent = [
        { id: 1, title: 'Post 1', content: 'Content 1' },
        { id: 2, title: 'Post 2', content: 'Content 2' }
      ]
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockContent,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.getContent()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/content',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockContent)
    })

    it('should create content correctly', async () => {
      const newContent = { title: 'New Post', content: 'New content', platform: 'LinkedIn' }
      const createdContent = { id: 3, ...newContent, createdAt: '2023-12-01T00:00:00Z' }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => createdContent,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.createContent(newContent)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/content',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newContent)
        })
      )
      expect(result).toEqual(createdContent)
    })

    it('should update content correctly', async () => {
      const contentId = 1
      const updateData = { title: 'Updated Post' }
      const updatedContent = { id: contentId, title: 'Updated Post', content: 'Original content' }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => updatedContent,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.updateContent(contentId, updateData)

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/content/${contentId}`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData)
        })
      )
      expect(result).toEqual(updatedContent)
    })

    it('should delete content correctly', async () => {
      const contentId = 1
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: 'Content deleted successfully' }),
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.deleteContent(contentId)

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/content/${contentId}`,
        expect.objectContaining({
          method: 'DELETE'
        })
      )
      expect(result).toEqual({ message: 'Content deleted successfully' })
    })
  })

  describe('Analytics API', () => {
    it('should fetch analytics data correctly', async () => {
      const mockAnalytics = {
        totalViews: 1000,
        totalEngagement: 150,
        topPerformingPosts: []
      }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockAnalytics,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.getAnalytics()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/analytics',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockAnalytics)
    })

    it('should fetch analytics with date range', async () => {
      const startDate = '2023-11-01'
      const endDate = '2023-11-30'
      const mockAnalytics = { period: 'November 2023', metrics: {} }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockAnalytics,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.getAnalytics(startDate, endDate)

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/analytics?start_date=${startDate}&end_date=${endDate}`,
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockAnalytics)
    })
  })

  describe('Goals API', () => {
    it('should fetch goals correctly', async () => {
      const mockGoals = [
        { id: 1, title: 'Increase followers', target: 1000, current: 750 },
        { id: 2, title: 'Improve engagement', target: 100, current: 80 }
      ]
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockGoals,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.getGoals()

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/goals',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockGoals)
    })

    it('should create goal correctly', async () => {
      const newGoal = { title: 'New Goal', target: 500, description: 'Test goal' }
      const createdGoal = { id: 3, ...newGoal, current: 0, status: 'active' }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => createdGoal,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.createGoal(newGoal)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/goals',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newGoal)
        })
      )
      expect(result).toEqual(createdGoal)
    })
  })

  describe('Memory/Search API', () => {
    it('should search content correctly', async () => {
      const query = 'test search'
      const mockResults = [
        { id: 1, title: 'Result 1', similarity: 0.9 },
        { id: 2, title: 'Result 2', similarity: 0.8 }
      ]
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResults,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.searchContent(query)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/search',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ query })
        })
      )
      expect(result).toEqual(mockResults)
    })

    it('should search content with filters', async () => {
      const query = 'filtered search'
      const filters = { platform: 'LinkedIn', type: 'post' }
      const mockResults = [{ id: 1, title: 'Filtered Result' }]
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResults,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.searchContent(query, filters)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/search',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ query, filters })
        })
      )
      expect(result).toEqual(mockResults)
    })
  })

  describe('Workflow API', () => {
    it('should trigger workflow correctly', async () => {
      const workflowType = 'content_generation'
      const parameters = { topic: 'AI trends', platform: 'LinkedIn' }
      const mockResponse = { 
        workflowId: 'wf-123', 
        status: 'started',
        estimatedDuration: '5 minutes'
      }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.triggerWorkflow(workflowType, parameters)

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/workflows/trigger',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ workflow_type: workflowType, parameters })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should get workflow status correctly', async () => {
      const workflowId = 'wf-123'
      const mockStatus = {
        id: workflowId,
        status: 'completed',
        progress: 100,
        result: { contentGenerated: true }
      }
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockStatus,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.getWorkflowStatus(workflowId)

      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/api/workflows/${workflowId}`,
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockStatus)
    })
  })

  describe('Custom Headers and Options', () => {
    it('should merge custom headers with default headers', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Map([['content-type', 'application/json']])
      })

      await apiService.request('/test', {
        headers: {
          'X-Custom-Header': 'custom-value',
          'X-Another-Header': 'another-value'
        }
      })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Custom-Header': 'custom-value',
            'X-Another-Header': 'another-value'
          })
        })
      )
    })

    it('should override default headers with custom headers', async () => {
      fetch.mockResolvedValue({
        ok: true,
        text: async () => 'success',
        headers: new Map([['content-type', 'text/plain']])
      })

      await apiService.request('/test', {
        headers: {
          'Content-Type': 'text/plain'
        }
      })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'text/plain'
          })
        })
      )
    })

    it('should pass through additional fetch options', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Map([['content-type', 'application/json']])
      })

      await apiService.request('/test', {
        method: 'PATCH',
        credentials: 'include',
        cache: 'no-cache',
        redirect: 'follow'
      })

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'PATCH',
          credentials: 'include',
          cache: 'no-cache',
          redirect: 'follow'
        })
      )
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty endpoint gracefully', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        headers: new Map([['content-type', 'application/json']])
      })

      await apiService.request('')

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000',
        expect.any(Object)
      )
    })

    it('should handle missing content-type header', async () => {
      const mockResponse = 'response without content-type'
      fetch.mockResolvedValue({
        ok: true,
        text: async () => mockResponse,
        headers: new Map()
      })

      const result = await apiService.request('/test')

      expect(result).toBe(mockResponse)
    })

    it('should handle null response body', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => null,
        headers: new Map([['content-type', 'application/json']])
      })

      const result = await apiService.request('/test')

      expect(result).toBeNull()
    })
  })
})