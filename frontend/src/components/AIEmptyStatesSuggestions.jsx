import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  SparklesIcon, 
  PlusIcon, 
  ArrowRightIcon,
  LightBulbIcon,
  CalendarDaysIcon,
  HashtagIcon,
  PhotoIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { useEnhancedApi } from '../hooks/useEnhancedApi'
import { useNotifications } from '../hooks/useNotifications'

const AIEmptyStateSuggestions = ({ 
  type = 'content', 
  context = {}, 
  onSuggestionClick,
  className = ''
}) => {
  const { api } = useEnhancedApi()
  const { showError } = useNotifications()
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentSuggestionIndex, setCurrentSuggestionIndex] = useState(0)

  // Helper function to get appropriate icon for suggestion
  const getIconForSuggestion = (suggestionId, suggestionType) => {
    const iconMap = {
      // Content-related
      'trending-content': SparklesIcon,
      'content-calendar': CalendarDaysIcon,
      'weekly-content': CalendarDaysIcon,
      'hashtag-research': HashtagIcon,
      'visual-content': PhotoIcon,
      'content-ideas': LightBulbIcon,
      
      // Goals-related  
      'growth-goals': SparklesIcon,
      'engagement-goals': LightBulbIcon,
      'performance-goals': SparklesIcon,
      
      // General fallback by type
      'content': DocumentTextIcon,
      'goals': SparklesIcon,
      'inbox': SparklesIcon,
      'memory': PlusIcon,
      'scheduler': CalendarDaysIcon
    }
    
    return iconMap[suggestionId] || iconMap[suggestionType] || SparklesIcon
  }

  // Define suggestion templates based on type
  const getSuggestionsForType = (type, context) => {
    const baseUrls = {
      content: '/create-post',
      goals: '/goals',
      inbox: '/inbox',
      memory: '/memory',
      scheduler: '/calendar'
    }

    const suggestions = {
      content: [
        {
          id: 'trending-content',
          icon: SparklesIcon,
          title: 'Generate trending content ideas',
          description: 'Let me research current trends and create 5 post ideas for you',
          action: 'Generate Ideas',
          color: 'blue',
          aiPrompt: 'Generate 5 trending social media post ideas based on current industry trends',
          estimatedTime: '30 seconds'
        },
        {
          id: 'weekly-content',
          icon: CalendarDaysIcon,
          title: 'Create a full week of content',
          description: 'I\'ll research, write, and schedule 7 posts across your platforms',
          action: 'Create Week Plan',
          color: 'purple',
          aiPrompt: 'Create a comprehensive 7-day content plan with posts for each day',
          estimatedTime: '2 minutes'
        },
        {
          id: 'hashtag-research',
          icon: HashtagIcon,
          title: 'Research trending hashtags',
          description: 'Find the best hashtags for your industry and content type',
          action: 'Find Hashtags',
          color: 'green',
          aiPrompt: 'Research and suggest trending hashtags for your industry',
          estimatedTime: '15 seconds'
        },
        {
          id: 'visual-content',
          icon: PhotoIcon,
          title: 'Generate image concepts',
          description: 'AI-powered visual content ideas with image prompts',
          action: 'Create Visuals',
          color: 'orange',
          aiPrompt: 'Generate image concepts and visual content ideas',
          estimatedTime: '45 seconds'
        }
      ],
      goals: [
        {
          id: 'growth-goals',
          icon: SparklesIcon,
          title: 'Set smart growth goals',
          description: 'AI-recommended goals based on your current metrics',
          action: 'Create Goals',
          color: 'blue',
          aiPrompt: 'Suggest growth goals based on current social media performance',
          estimatedTime: '20 seconds'
        },
        {
          id: 'engagement-goals',
          icon: LightBulbIcon,
          title: 'Boost engagement targets',
          description: 'Set realistic engagement milestones for the next quarter',
          action: 'Set Targets',
          color: 'green',
          aiPrompt: 'Create engagement goals and milestones',
          estimatedTime: '15 seconds'
        }
      ],
      inbox: [
        {
          id: 'auto-responses',
          icon: SparklesIcon,
          title: 'Set up automated responses',
          description: 'Configure AI to handle common questions automatically',
          action: 'Setup Auto-Reply',
          color: 'blue',
          aiPrompt: 'Configure automated response templates',
          estimatedTime: '1 minute'
        }
      ],
      memory: [
        {
          id: 'import-content',
          icon: PlusIcon,
          title: 'Import existing content',
          description: 'Add your previous posts to build your Brand Brain',
          action: 'Import Content',
          color: 'purple',
          aiPrompt: 'Help import and organize existing content',
          estimatedTime: '30 seconds'
        }
      ]
    }

    return suggestions[type] || suggestions.content
  }

  useEffect(() => {
    const loadSuggestions = async () => {
      setLoading(true)
      try {
        // Fetch real-time AI suggestions from backend
        const aiResponse = await api.ai.getContextualSuggestions({ 
          type, 
          context,
          limit: 4 
        })
        
        if (aiResponse && aiResponse.suggestions && aiResponse.suggestions.length > 0) {
          // Transform API response to component format
          const transformedSuggestions = aiResponse.suggestions.map(suggestion => ({
            id: suggestion.id,
            icon: getIconForSuggestion(suggestion.id, type),
            title: suggestion.title,
            description: suggestion.description,
            action: suggestion.action,
            color: suggestion.color,
            aiPrompt: suggestion.ai_prompt,
            estimatedTime: suggestion.estimated_time,
            priority: suggestion.priority,
            personalizationScore: suggestion.personalization_score
          }))
          
          // Sort by priority (lower number = higher priority)
          transformedSuggestions.sort((a, b) => a.priority - b.priority)
          
          setSuggestions(transformedSuggestions)
          
          // Show personalization level to user
          if (aiResponse.personalization_level === 'high') {
            console.log('🎯 Highly personalized suggestions loaded based on your activity')
          }
        } else {
          // Fallback to static suggestions if API fails
          const baseSuggestions = getSuggestionsForType(type, context)
          setSuggestions(baseSuggestions)
        }
        
        // Rotate suggestions every 10 seconds (slightly slower for AI-generated content)
        const interval = setInterval(() => {
          setSuggestions(current => {
            if (current.length > 0) {
              setCurrentSuggestionIndex(prev => (prev + 1) % current.length)
            }
            return current
          })
        }, 10000)
        
        return () => clearInterval(interval)
      } catch (error) {
        console.error('Failed to load AI suggestions:', error)
        showError && showError('Failed to load personalized suggestions')
        
        // Fallback to static suggestions
        const baseSuggestions = getSuggestionsForType(type, context)
        setSuggestions(baseSuggestions)
      } finally {
        setLoading(false)
      }
    }

    loadSuggestions()
  }, [type, context, api])

  const handleSuggestionClick = async (suggestion) => {
    if (onSuggestionClick) {
      onSuggestionClick(suggestion)
    } else {
      // Default action - navigate to relevant page
      const baseUrls = {
        content: '/create-post',
        goals: '/goals',
        inbox: '/inbox',
        memory: '/memory',
        scheduler: '/calendar'
      }
      
      window.location.href = baseUrls[type] || '/create-post'
    }
  }

  if (loading) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="animate-spin mx-auto h-8 w-8 text-blue-600 mb-4">
          <SparklesIcon />
        </div>
        <p className="text-sm text-gray-500">Lily is thinking of suggestions...</p>
      </div>
    )
  }

  if (suggestions.length === 0) {
    return null
  }

  const currentSuggestion = suggestions[currentSuggestionIndex] || suggestions[0]
  const Icon = currentSuggestion.icon

  const colorClasses = {
    blue: 'from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700',
    purple: 'from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700',
    green: 'from-green-500 to-green-600 hover:from-green-600 hover:to-green-700',
    orange: 'from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700',
  }

  return (
    <div className={`text-center py-12 ${className}`}>
      {/* AI Brain Animation */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="mx-auto w-20 h-20 mb-6 relative"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 rounded-full border-2 border-dashed border-blue-300"
        />
        <div className="absolute inset-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
          <SparklesIcon className="w-8 h-8 text-white" />
        </div>
      </motion.div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        🤖 Lily has {suggestions.length > 0 && suggestions[0].personalizationScore > 0.6 ? 'personalized' : 'some'} ideas for you!
      </h3>
      
      <AnimatePresence mode="wait">
        <motion.div
          key={currentSuggestion.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
          className="max-w-md mx-auto"
        >
          <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-6 border border-blue-100">
            <div className="flex items-center justify-center mb-4">
              <div className={`p-3 rounded-full bg-gradient-to-r ${colorClasses[currentSuggestion.color]} text-white`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
            
            <h4 className="text-base font-semibold text-gray-900 mb-2">
              {currentSuggestion.title}
            </h4>
            
            <p className="text-sm text-gray-600 mb-4">
              {currentSuggestion.description}
            </p>
            
            <div className="flex items-center justify-center space-x-4 text-xs text-gray-500 mb-4">
              <span>⚡ {currentSuggestion.estimatedTime}</span>
              <span>•</span>
              <span>🤖 AI-Powered</span>
            </div>

            <button
              onClick={() => handleSuggestionClick(currentSuggestion)}
              className={`w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r ${colorClasses[currentSuggestion.color]} transition-all duration-200 transform hover:scale-105`}
            >
              <Icon className="-ml-1 mr-2 h-4 w-4" />
              {currentSuggestion.action}
              <ArrowRightIcon className="ml-2 h-4 w-4" />
            </button>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Suggestion Navigation Dots */}
      {suggestions.length > 1 && (
        <div className="flex justify-center space-x-2 mt-6">
          {suggestions.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentSuggestionIndex(index)}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentSuggestionIndex ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      )}

      {/* Alternative Actions */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <p className="text-xs text-gray-500 mb-4">Or choose a different action:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {suggestions.map((suggestion, index) => {
            if (index === currentSuggestionIndex) return null
            const SugIcon = suggestion.icon
            return (
              <button
                key={suggestion.id}
                onClick={() => handleSuggestionClick(suggestion)}
                className="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
              >
                <SugIcon className="w-3 h-3 mr-1" />
                {suggestion.action}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default AIEmptyStateSuggestions