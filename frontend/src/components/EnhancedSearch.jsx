import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon,
  TagIcon,
  CalendarDaysIcon,
  SparklesIcon,
  HashtagIcon
} from '@heroicons/react/24/outline'
import { useNotifications } from '../hooks/useNotifications'

const EnhancedSearch = ({
  searchQuery,
  onSearchChange,
  filters,
  onFiltersChange,
  suggestions = [],
  recentSearches = [],
  onSearch,
  placeholder = "Search with AI-powered semantic search...",
  showAdvanced = false,
  className = ""
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [localQuery, setLocalQuery] = useState(searchQuery || '')
  const [activeFilters, setActiveFilters] = useState(filters || {})
  const { showSuccess } = useNotifications()

  // Smart suggestions based on content type
  const smartSuggestions = useMemo(() => [
    { text: "AI-generated content", icon: SparklesIcon, type: "filter" },
    { text: "high engagement posts", icon: HashtagIcon, type: "search" },
    { text: "recent viral trends", icon: CalendarDaysIcon, type: "search" },
    { text: "competitor analysis", icon: FunnelIcon, type: "search" },
    { text: "visual content ideas", icon: TagIcon, type: "search" },
    ...suggestions
  ], [suggestions])

  useEffect(() => {
    setLocalQuery(searchQuery || '')
  }, [searchQuery])

  useEffect(() => {
    setActiveFilters(filters || {})
  }, [filters])

  const handleSearch = (query = localQuery) => {
    if (query.trim()) {
      onSearch?.(query, activeFilters)
      onSearchChange?.(query)
      setShowSuggestions(false)
      
      // Store in recent searches (would be persisted to localStorage in real app)
      const newRecentSearches = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5)
      // In real app: localStorage.setItem('recentSearches', JSON.stringify(newRecentSearches))
    }
  }

  const handleSuggestionClick = (suggestion) => {
    if (suggestion.type === 'filter') {
      // Apply filter
      const newFilters = { ...activeFilters, generated_by_ai: true }
      setActiveFilters(newFilters)
      onFiltersChange?.(newFilters)
      showSuccess(`Filter applied: ${suggestion.text}`)
    } else {
      // Apply search
      setLocalQuery(suggestion.text)
      handleSearch(suggestion.text)
    }
    setShowSuggestions(false)
  }

  const clearFilter = (filterKey) => {
    const newFilters = { ...activeFilters }
    delete newFilters[filterKey]
    setActiveFilters(newFilters)
    onFiltersChange?.(newFilters)
  }

  const clearAllFilters = () => {
    setActiveFilters({})
    onFiltersChange?.({})
  }

  const activeFilterCount = Object.keys(activeFilters).filter(key => 
    activeFilters[key] && activeFilters[key] !== 'all'
  ).length

  return (
    <div className={`relative ${className}`}>
      {/* Main Search Bar */}
      <div className="relative">
        <div className={`relative transition-all duration-200 ${isExpanded ? 'ring-2 ring-blue-500' : ''}`}>
          <MagnifyingGlassIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={localQuery}
            onChange={(e) => {
              setLocalQuery(e.target.value)
              onSearchChange?.(e.target.value)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch()
              } else if (e.key === 'Escape') {
                setShowSuggestions(false)
                setIsExpanded(false)
              }
            }}
            onFocus={() => {
              setIsExpanded(true)
              setShowSuggestions(true)
            }}
            onBlur={() => {
              // Delay to allow clicks on suggestions
              setTimeout(() => {
                setIsExpanded(false)
                setShowSuggestions(false)
              }, 200)
            }}
            placeholder={placeholder}
            className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
          />
          
          {/* Clear search */}
          {localQuery && (
            <button
              onClick={() => {
                setLocalQuery('')
                onSearchChange?.('')
              }}
              className="absolute right-3 top-3 p-1 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Active Filters Row */}
        {activeFilterCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-wrap items-center gap-2 mt-3"
          >
            <span className="text-sm text-gray-500">Filters:</span>
            {Object.entries(activeFilters).map(([key, value]) => {
              if (!value || value === 'all') return null
              return (
                <motion.span
                  key={key}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                >
                  <TagIcon className="h-3 w-3" />
                  {key}: {value}
                  <button
                    onClick={() => clearFilter(key)}
                    className="ml-1 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                  >
                    <XMarkIcon className="h-2.5 w-2.5" />
                  </button>
                </motion.span>
              )
            })}
            <button
              onClick={clearAllFilters}
              className="text-xs text-gray-500 hover:text-red-600 underline ml-2"
            >
              Clear all
            </button>
          </motion.div>
        )}
      </div>

      {/* Search Suggestions Dropdown */}
      <AnimatePresence>
        {showSuggestions && isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl border z-50 max-h-96 overflow-y-auto"
          >
            {/* Smart Suggestions */}
            {smartSuggestions.length > 0 && (
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <SparklesIcon className="h-4 w-4 text-purple-600" />
                  <h4 className="text-sm font-medium text-gray-900">Smart Suggestions</h4>
                </div>
                <div className="space-y-2">
                  {smartSuggestions.slice(0, 5).map((suggestion, index) => {
                    const Icon = suggestion.icon
                    return (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="w-full flex items-center gap-3 p-2 text-left hover:bg-gray-50 rounded-md transition-colors group"
                      >
                        <Icon className="h-4 w-4 text-gray-400 group-hover:text-blue-600" />
                        <span className="text-sm text-gray-700 group-hover:text-gray-900">
                          {suggestion.text}
                        </span>
                        <span className={`ml-auto px-2 py-0.5 text-xs rounded-full ${
                          suggestion.type === 'filter' 
                            ? 'bg-purple-100 text-purple-700' 
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          {suggestion.type}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Recent Searches */}
            {recentSearches.length > 0 && (
              <div className="p-4 border-t">
                <div className="flex items-center gap-2 mb-3">
                  <CalendarDaysIcon className="h-4 w-4 text-gray-500" />
                  <h4 className="text-sm font-medium text-gray-900">Recent Searches</h4>
                </div>
                <div className="space-y-1">
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setLocalQuery(search)
                        handleSearch(search)
                      }}
                      className="w-full text-left p-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-md transition-colors"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Search Tips */}
            <div className="p-4 border-t bg-gray-50">
              <div className="flex items-center gap-2 mb-2">
                <SparklesIcon className="h-4 w-4 text-blue-600" />
                <h4 className="text-sm font-medium text-gray-900">Search Tips</h4>
              </div>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• Use semantic search: "posts about growth" finds growth-related content</li>
                <li>• Try specific terms: "viral marketing strategies" or "engagement tips"</li>
                <li>• Search by emotion: "motivational content" or "inspiring posts"</li>
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Advanced Filters Toggle */}
      {showAdvanced && (
        <div className="mt-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <AdjustmentsHorizontalIcon className="h-4 w-4" />
            Advanced Filters
            {activeFilterCount > 0 && (
              <span className="bg-blue-600 text-white text-xs rounded-full px-2 py-0.5">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

export default EnhancedSearch