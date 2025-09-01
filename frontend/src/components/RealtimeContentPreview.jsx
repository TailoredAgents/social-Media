import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  HeartIcon, 
  ChatBubbleOvalLeftIcon, 
  ArrowPathIcon,
  ShareIcon,
  EllipsisHorizontalIcon,
  HandThumbUpIcon,
  FaceSmileIcon,
  PhotoIcon
} from '@heroicons/react/24/outline'
import { 
  HeartIcon as HeartSolidIcon,
  ChatBubbleOvalLeftIcon as ChatSolidIcon,
  HandThumbUpIcon as ThumbUpSolidIcon
} from '@heroicons/react/24/solid'

const RealtimeContentPreview = ({ 
  content = '', 
  title = '', 
  selectedPlatforms = ['twitter'], 
  imageUrl = null,
  className = '' 
}) => {
  const [activePreview, setActivePreview] = useState(selectedPlatforms[0] || 'twitter')
  const [liked, setLiked] = useState({})
  const [shared, setShared] = useState({})

  // Platform configurations
  const platformConfig = {
    twitter: {
      name: 'X (Twitter)',
      color: 'bg-black',
      textColor: 'text-white',
      maxLength: 280,
      bgColor: 'bg-black',
      userBg: 'bg-gray-900',
      icon: '𝕏',
      features: {
        replies: true,
        retweets: true,
        likes: true,
        views: true
      }
    },
    instagram: {
      name: 'Instagram',
      color: 'bg-gradient-to-tr from-pink-500 via-red-500 to-yellow-500',
      textColor: 'text-white',
      maxLength: 2200,
      bgColor: 'bg-gray-50',
      userBg: 'bg-white',
      icon: '📷',
      features: {
        likes: true,
        comments: true,
        shares: true,
        saves: true
      }
    },
    facebook: {
      name: 'Facebook',
      color: 'bg-blue-600',
      textColor: 'text-white',
      maxLength: 63206,
      bgColor: 'bg-gray-50',
      userBg: 'bg-white',
      icon: '👥',
      features: {
        likes: true,
        comments: true,
        shares: true,
        reactions: true
      }
    },
    linkedin: {
      name: 'LinkedIn',
      color: 'bg-blue-700',
      textColor: 'text-white',
      maxLength: 3000,
      bgColor: 'bg-gray-50',
      userBg: 'bg-white',
      icon: '💼',
      features: {
        likes: true,
        comments: true,
        reposts: true,
        reactions: true
      }
    }
  }

  // Character count analysis
  const getCharacterAnalysis = (platform) => {
    const config = platformConfig[platform]
    const length = content.length
    const remaining = config.maxLength - length
    const percentage = (length / config.maxLength) * 100
    
    return {
      current: length,
      max: config.maxLength,
      remaining,
      percentage,
      status: percentage > 95 ? 'critical' : percentage > 80 ? 'warning' : 'good'
    }
  }

  // Hashtag and mention detection
  const parseContent = (text) => {
    const hashtagRegex = /#[a-zA-Z0-9_]+/g
    const mentionRegex = /@[a-zA-Z0-9_.]+/g
    
    return text
      .replace(hashtagRegex, '<span class="text-blue-500 font-semibold">$&</span>')
      .replace(mentionRegex, '<span class="text-blue-600 font-semibold">$&</span>')
  }

  // Simulate engagement metrics
  const getEngagementMetrics = (platform) => {
    const baseMetrics = {
      twitter: { likes: 47, retweets: 12, replies: 8, views: 1247 },
      instagram: { likes: 156, comments: 23, shares: 5, saves: 31 },
      facebook: { likes: 89, comments: 15, shares: 7, reactions: 12 },
      linkedin: { likes: 34, comments: 8, reposts: 3, reactions: 6 }
    }
    
    return baseMetrics[platform] || baseMetrics.twitter
  }

  const TwitterPreview = () => {
    const analysis = getCharacterAnalysis('twitter')
    const metrics = getEngagementMetrics('twitter')
    
    return (
      <div className="bg-black text-white rounded-xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
              Y
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h3 className="font-bold text-white">Your Company</h3>
                <span className="text-blue-400">✓</span>
                <span className="text-gray-500">@yourcompany</span>
                <span className="text-gray-500">·</span>
                <span className="text-gray-500">2m</span>
              </div>
            </div>
            <EllipsisHorizontalIcon className="w-5 h-5 text-gray-400" />
          </div>
        </div>
        
        {/* Content */}
        <div className="p-4">
          <div 
            className="text-white text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: parseContent(content || "Your content will appear here as you type...") }}
          />
          
          {imageUrl && (
            <div className="mt-3 rounded-xl overflow-hidden">
              <img src={imageUrl} alt="Post image" className="w-full h-48 object-cover" />
            </div>
          )}
          
          {/* Character Count Indicator */}
          <div className="mt-3 flex justify-between items-center text-xs">
            <span className={`${analysis.status === 'critical' ? 'text-red-400' : analysis.status === 'warning' ? 'text-yellow-400' : 'text-gray-400'}`}>
              {analysis.current}/{analysis.max} characters
            </span>
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded-full bg-gray-800 relative">
                <svg className="w-6 h-6 transform -rotate-90" viewBox="0 0 24 24">
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    fill="none"
                    className="stroke-current text-gray-600"
                    strokeWidth="2"
                  />
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    fill="none"
                    className={`stroke-current ${
                      analysis.status === 'critical' ? 'text-red-400' : 
                      analysis.status === 'warning' ? 'text-yellow-400' : 'text-blue-400'
                    }`}
                    strokeWidth="2"
                    strokeDasharray={`${analysis.percentage * 0.628} 62.8`}
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
        
        {/* Engagement */}
        <div className="px-4 py-3 border-t border-gray-800">
          <div className="flex justify-between text-gray-400">
            <button className="flex items-center space-x-2 hover:text-red-400 transition-colors">
              <HeartIcon className="w-5 h-5" />
              <span className="text-sm">{metrics.likes}</span>
            </button>
            <button className="flex items-center space-x-2 hover:text-green-400 transition-colors">
              <ArrowPathIcon className="w-5 h-5" />
              <span className="text-sm">{metrics.retweets}</span>
            </button>
            <button className="flex items-center space-x-2 hover:text-blue-400 transition-colors">
              <ChatBubbleOvalLeftIcon className="w-5 h-5" />
              <span className="text-sm">{metrics.replies}</span>
            </button>
            <button className="flex items-center space-x-2 hover:text-blue-400 transition-colors">
              <ShareIcon className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {metrics.views.toLocaleString()} views
          </div>
        </div>
      </div>
    )
  }

  const InstagramPreview = () => {
    const analysis = getCharacterAnalysis('instagram')
    const metrics = getEngagementMetrics('instagram')
    
    return (
      <div className="bg-white rounded-xl overflow-hidden border border-gray-200">
        {/* Header */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-tr from-pink-500 via-red-500 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
              Y
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">yourcompany</h3>
            </div>
            <EllipsisHorizontalIcon className="w-5 h-5 text-gray-400" />
          </div>
        </div>
        
        {/* Image */}
        {imageUrl && (
          <div className="relative">
            <img src={imageUrl} alt="Post image" className="w-full h-64 object-cover" />
          </div>
        )}
        
        {/* Engagement Bar */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex justify-between items-center">
            <div className="flex space-x-4">
              <button className="hover:scale-110 transition-transform">
                <HeartIcon className="w-6 h-6 text-gray-700" />
              </button>
              <button className="hover:scale-110 transition-transform">
                <ChatBubbleOvalLeftIcon className="w-6 h-6 text-gray-700" />
              </button>
              <button className="hover:scale-110 transition-transform">
                <ShareIcon className="w-6 h-6 text-gray-700" />
              </button>
            </div>
          </div>
          
          <div className="mt-3">
            <p className="text-sm font-semibold text-gray-900">{metrics.likes.toLocaleString()} likes</p>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-4">
          <div className="flex space-x-3">
            <span className="font-semibold text-gray-900">yourcompany</span>
            <div 
              className="flex-1 text-gray-900 text-sm"
              dangerouslySetInnerHTML={{ __html: parseContent(content || "Your Instagram caption will appear here...") }}
            />
          </div>
          
          <div className="mt-2 text-xs text-gray-500">
            {analysis.current}/{analysis.max} characters
          </div>
          
          <div className="mt-3 text-xs text-gray-500">
            View all {metrics.comments} comments
          </div>
          
          <div className="mt-1 text-xs text-gray-400 uppercase tracking-wide">
            2 minutes ago
          </div>
        </div>
      </div>
    )
  }

  const FacebookPreview = () => {
    const analysis = getCharacterAnalysis('facebook')
    const metrics = getEngagementMetrics('facebook')
    
    return (
      <div className="bg-white rounded-xl overflow-hidden border border-gray-200">
        {/* Header */}
        <div className="p-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
              Y
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Your Company</h3>
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                <span>2 minutes ago</span>
                <span>·</span>
                <span>🌐</span>
              </div>
            </div>
            <EllipsisHorizontalIcon className="w-5 h-5 text-gray-400" />
          </div>
        </div>
        
        {/* Content */}
        <div className="px-4 pb-3">
          <div 
            className="text-gray-900 text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: parseContent(content || "Your Facebook post content will appear here...") }}
          />
          <div className="mt-2 text-xs text-gray-500">
            {analysis.current}/{analysis.max} characters
          </div>
        </div>
        
        {/* Image */}
        {imageUrl && (
          <div className="mb-3">
            <img src={imageUrl} alt="Post image" className="w-full h-48 object-cover" />
          </div>
        )}
        
        {/* Engagement */}
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="flex -space-x-1">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                  <HandThumbUpIcon className="w-3 h-3 text-white" />
                </div>
                <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                  <HeartIcon className="w-3 h-3 text-white" />
                </div>
              </div>
              <span>{metrics.likes}</span>
            </div>
            <div className="text-sm text-gray-500">
              {metrics.comments} comments · {metrics.shares} shares
            </div>
          </div>
          
          <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between">
            <button className="flex items-center space-x-2 text-gray-600 hover:bg-gray-50 px-4 py-2 rounded-md transition-colors">
              <HandThumbUpIcon className="w-5 h-5" />
              <span className="text-sm font-medium">Like</span>
            </button>
            <button className="flex items-center space-x-2 text-gray-600 hover:bg-gray-50 px-4 py-2 rounded-md transition-colors">
              <ChatBubbleOvalLeftIcon className="w-5 h-5" />
              <span className="text-sm font-medium">Comment</span>
            </button>
            <button className="flex items-center space-x-2 text-gray-600 hover:bg-gray-50 px-4 py-2 rounded-md transition-colors">
              <ShareIcon className="w-5 h-5" />
              <span className="text-sm font-medium">Share</span>
            </button>
          </div>
        </div>
      </div>
    )
  }

  const renderPreview = () => {
    switch (activePreview) {
      case 'twitter':
        return <TwitterPreview />
      case 'instagram':
        return <InstagramPreview />
      case 'facebook':
        return <FacebookPreview />
      default:
        return <TwitterPreview />
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Platform Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {selectedPlatforms.map((platform) => {
          const config = platformConfig[platform]
          return (
            <button
              key={platform}
              onClick={() => setActivePreview(platform)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                activePreview === platform 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <span>{config.icon}</span>
              <span>{config.name}</span>
            </button>
          )
        })}
      </div>

      {/* Live Preview */}
      <div className="relative">
        <div className="absolute top-2 right-2 z-10">
          <div className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span>LIVE</span>
          </div>
        </div>
        
        <AnimatePresence mode="wait">
          <motion.div
            key={activePreview}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {renderPreview()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Platform Optimization Tips */}
      {content && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            💡 {platformConfig[activePreview].name} Optimization Tips:
          </h4>
          <div className="text-xs text-blue-800 space-y-1">
            {activePreview === 'twitter' && (
              <>
                <p>• Keep it concise and engaging</p>
                <p>• Use 1-2 hashtags for better reach</p>
                <p>• Ask questions to encourage replies</p>
              </>
            )}
            {activePreview === 'instagram' && (
              <>
                <p>• Use engaging visuals for higher engagement</p>
                <p>• Include 8-12 relevant hashtags</p>
                <p>• Add a clear call-to-action</p>
              </>
            )}
            {activePreview === 'facebook' && (
              <>
                <p>• Longer posts perform well on Facebook</p>
                <p>• Include questions to boost engagement</p>
                <p>• Share behind-the-scenes content</p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default RealtimeContentPreview