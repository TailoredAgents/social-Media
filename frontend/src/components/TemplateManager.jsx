import React, { useState, useEffect } from 'react'
import api from '../services/api'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  DocumentTextIcon,
  TagIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

const TEMPLATE_CATEGORIES = [
  { value: 'question', label: 'Questions', description: 'Responses to customer questions' },
  { value: 'complaint', label: 'Complaints', description: 'Handling customer complaints' },
  { value: 'praise', label: 'Praise', description: 'Thanking customers for praise' },
  { value: 'lead', label: 'Sales Leads', description: 'Following up on sales inquiries' },
  { value: 'support', label: 'Support', description: 'Technical support responses' },
  { value: 'general', label: 'General', description: 'General purpose responses' }
]

const PLATFORMS = [
  { value: 'facebook', label: 'Facebook', emoji: '📘' },
  { value: 'instagram', label: 'Instagram', emoji: '📷' },
  { value: 'twitter', label: 'X/Twitter', emoji: '🐦' }
]

const PERSONALITY_STYLES = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'casual', label: 'Casual' },
  { value: 'technical', label: 'Technical' }
]

function TemplateManager() {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger_type: 'general',
    platforms: ['facebook', 'instagram', 'twitter'],
    response_text: '',
    variables: [],
    personality_style: 'professional',
    keywords: [],
    priority: 50,
    is_active: true
  })

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      setLoading(true)
      const response = await api.getResponseTemplates()
      setTemplates(response.templates || [])
    } catch (error) {
      console.error('Failed to fetch templates:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (editingTemplate) {
        await api.updateResponseTemplate(editingTemplate.id, formData)
      } else {
        await api.createResponseTemplate(formData)
      }
      
      fetchTemplates()
      resetForm()
    } catch (error) {
      console.error('Failed to save template:', error)
    }
  }

  const handleDelete = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return
    }
    
    try {
      await api.deleteResponseTemplate(templateId)
      fetchTemplates()
    } catch (error) {
      console.error('Failed to delete template:', error)
    }
  }

  const handleEdit = (template) => {
    setEditingTemplate(template)
    setFormData({
      name: template.name || '',
      description: template.description || '',
      trigger_type: template.trigger_type || 'general',
      platforms: template.platforms || ['facebook', 'instagram', 'twitter'],
      response_text: template.response_text || '',
      variables: template.variables || [],
      personality_style: template.personality_style || 'professional',
      keywords: template.keywords || [],
      priority: template.priority || 50,
      is_active: template.is_active !== false
    })
    setShowCreateForm(true)
  }

  const resetForm = () => {
    setEditingTemplate(null)
    setShowCreateForm(false)
    setFormData({
      name: '',
      description: '',
      trigger_type: 'general',
      platforms: ['facebook', 'instagram', 'twitter'],
      response_text: '',
      variables: [],
      personality_style: 'professional',
      keywords: [],
      priority: 50,
      is_active: true
    })
  }

  const handleKeywordChange = (value) => {
    const keywords = value.split(',').map(k => k.trim()).filter(Boolean)
    setFormData(prev => ({ ...prev, keywords }))
  }

  const handleVariableChange = (value) => {
    const variables = value.split(',').map(v => v.trim()).filter(Boolean)
    setFormData(prev => ({ ...prev, variables }))
  }

  const insertVariable = (variable) => {
    const textarea = document.getElementById('response_text')
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = formData.response_text
    const newText = text.slice(0, start) + `{{${variable}}}` + text.slice(end)
    
    setFormData(prev => ({ ...prev, response_text: newText }))
    
    // Focus back to textarea
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + variable.length + 4, start + variable.length + 4)
    }, 10)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900 flex items-center">
          <DocumentTextIcon className="h-5 w-5 mr-2" />
          Response Templates
        </h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Template
        </button>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {editingTemplate ? 'Edit Template' : 'Create New Template'}
              </h3>
              <button
                type="button"
                onClick={resetForm}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={formData.trigger_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, trigger_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {TEMPLATE_CATEGORIES.map(category => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Brief description of when to use this template"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Platforms
              </label>
              <div className="flex space-x-4">
                {PLATFORMS.map(platform => (
                  <label key={platform.value} className="inline-flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.platforms.includes(platform.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData(prev => ({
                            ...prev,
                            platforms: [...prev.platforms, platform.value]
                          }))
                        } else {
                          setFormData(prev => ({
                            ...prev,
                            platforms: prev.platforms.filter(p => p !== platform.value)
                          }))
                        }
                      }}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      {platform.emoji} {platform.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Personality Style
                </label>
                <select
                  value={formData.personality_style}
                  onChange={(e) => setFormData(prev => ({ ...prev, personality_style: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {PERSONALITY_STYLES.map(style => (
                    <option key={style.value} value={style.value}>
                      {style.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority (1-100)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Keywords (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.keywords.join(', ')}
                  onChange={(e) => handleKeywordChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="refund, support, help"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Variables (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.variables.join(', ')}
                  onChange={(e) => handleVariableChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="customer_name, product, order_id"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Response Text
                </label>
                {formData.variables.length > 0 && (
                  <div className="flex space-x-1">
                    {formData.variables.map(variable => (
                      <button
                        key={variable}
                        type="button"
                        onClick={() => insertVariable(variable)}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                      >
                        {variable}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <textarea
                id="response_text"
                value={formData.response_text}
                onChange={(e) => setFormData(prev => ({ ...prev, response_text: e.target.value }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Hi {{customer_name}}, thank you for reaching out about {{product}}..."
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Use {{variable}} to insert dynamic content
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                Active (available for use)
              </label>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                {editingTemplate ? 'Update Template' : 'Create Template'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Templates List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {templates.length === 0 ? (
          <div className="text-center py-12">
            <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No response templates created yet</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Your First Template
            </button>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {templates.map((template) => (
              <li key={template.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        TEMPLATE_CATEGORIES.find(cat => cat.value === template.trigger_type)?.value === 'complaint' ? 'bg-red-100 text-red-800' :
                        TEMPLATE_CATEGORIES.find(cat => cat.value === template.trigger_type)?.value === 'praise' ? 'bg-green-100 text-green-800' :
                        TEMPLATE_CATEGORIES.find(cat => cat.value === template.trigger_type)?.value === 'lead' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {TEMPLATE_CATEGORIES.find(cat => cat.value === template.trigger_type)?.label || template.trigger_type}
                      </span>
                      {!template.is_active && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Inactive
                        </span>
                      )}
                    </div>
                    {template.description && (
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                    )}
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span className="flex items-center">
                        <SparklesIcon className="h-3 w-3 mr-1" />
                        {template.personality_style}
                      </span>
                      <span className="flex items-center">
                        <TagIcon className="h-3 w-3 mr-1" />
                        {template.keywords?.length || 0} keywords
                      </span>
                      <span>Priority: {template.priority || 50}</span>
                      <span>Used: {template.usage_count || 0} times</span>
                    </div>
                    <div className="flex space-x-2 mt-2">
                      {template.platforms?.map(platform => {
                        const platformInfo = PLATFORMS.find(p => p.value === platform)
                        return (
                          <span key={platform} className="text-xs text-gray-500">
                            {platformInfo?.emoji} {platformInfo?.label}
                          </span>
                        )
                      })}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEdit(template)}
                      className="p-2 text-gray-400 hover:text-gray-600"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="p-2 text-gray-400 hover:text-red-600"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default TemplateManager