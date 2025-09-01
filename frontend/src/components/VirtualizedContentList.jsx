import React, { memo, useCallback } from 'react'
import { FixedSizeList as List } from 'react-window'
import {
  EyeIcon,
  PencilIcon,
  TrashIcon,
  ShareIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  PhotoIcon,
  PlayIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

// Individual content item component
const ContentItem = memo(function ContentItem({ 
  index, 
  style, 
  data: { 
    items, 
    onView, 
    onEdit, 
    onPublish, 
    onDelete,
    onRegenerateImage,
    formatDate,
    getStatusIcon,
    getStatusColor,
    getContentTypeIcon 
  } 
}) {
  const item = items[index]

  if (!item) {
    return (
      <div style={style} className="p-3">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-20 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  return (
    <div style={style} className="p-3">
      <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
        <div className="p-6">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-2">
              {getContentTypeIcon(item.content_type)}
              <span className="text-sm font-medium text-gray-600 capitalize">
                {item.content_type || 'text'}
              </span>
            </div>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
              {item.status}
            </span>
          </div>
          
          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
            {item.title || 'Untitled'}
          </h3>
          
          <p className="text-sm text-gray-600 mb-4 line-clamp-3">
            {item.content || 'No content preview available'}
          </p>
          
          <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
            <span className="capitalize">{item.platform || 'All platforms'}</span>
            <span>{formatDate(item.scheduled_at || item.created_at)}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              {getStatusIcon(item.status)}
              <span>{item.performance?.views || 0} views</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <button
                onClick={() => onView(item)}
                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                title="View"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => onEdit(item)}
                className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                title="Edit"
              >
                <PencilIcon className="h-4 w-4" />
              </button>
              {(item.content_type === 'image' || item.image_url) && onRegenerateImage && (
                <button
                  onClick={() => onRegenerateImage(item)}
                  className="p-1 text-gray-400 hover:text-purple-600 transition-colors"
                  title="Regenerate Image"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>
              )}
              {item.status === 'draft' && (
                <button
                  onClick={() => onPublish(item.id)}
                  className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                  title="Publish"
                >
                  <ShareIcon className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => onDelete(item.id)}
                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                title="Delete"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
})

// Grid-based virtualized content list
const VirtualizedContentGrid = memo(function VirtualizedContentGrid({
  items,
  onView,
  onEdit,
  onPublish,
  onDelete,
  onRegenerateImage,
  formatDate,
  getStatusIcon,
  getStatusColor,
  getContentTypeIcon,
  height = 600,
  itemHeight = 280,
  itemsPerRow = 3
}) {
  // Calculate grid dimensions
  const rowCount = Math.ceil(items.length / itemsPerRow)
  
  const Row = useCallback(({ index, style }) => {
    const startIndex = index * itemsPerRow
    const endIndex = Math.min(startIndex + itemsPerRow, items.length)
    const rowItems = items.slice(startIndex, endIndex)
    
    return (
      <div style={style} className="flex">
        {rowItems.map((item, itemIndex) => (
          <div key={item.id} className="flex-1 px-3">
            <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getContentTypeIcon(item.content_type)}
                    <span className="text-sm font-medium text-gray-600 capitalize">
                      {item.content_type || 'text'}
                    </span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                    {item.status}
                  </span>
                </div>
                
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                  {item.title || 'Untitled'}
                </h3>
                
                <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                  {item.content || 'No content preview available'}
                </p>
                
                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <span className="capitalize">{item.platform || 'All platforms'}</span>
                  <span>{formatDate(item.scheduled_at || item.created_at)}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    {getStatusIcon(item.status)}
                    <span>{item.performance?.views || 0} views</span>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => onView(item)}
                      className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      title="View"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onEdit(item)}
                      className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                      title="Edit"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    {item.status === 'draft' && (
                      <button
                        onClick={() => onPublish(item.id)}
                        className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Publish"
                      >
                        <ShareIcon className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => onDelete(item.id)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
        {/* Fill empty slots */}
        {Array.from({ length: itemsPerRow - rowItems.length }).map((_, emptyIndex) => (
          <div key={`empty-${emptyIndex}`} className="flex-1 px-3" />
        ))}
      </div>
    )
  }, [items, itemsPerRow, onView, onEdit, onPublish, onDelete, onRegenerateImage, formatDate, getStatusIcon, getStatusColor, getContentTypeIcon])

  if (rowCount === 0) {
    return null
  }

  return (
    <List
      height={height}
      itemCount={rowCount}
      itemSize={itemHeight}
      itemData={{
        items,
        onView,
        onEdit,
        onPublish,
        onDelete,
        formatDate,
        getStatusIcon,
        getStatusColor,
        getContentTypeIcon
      }}
    >
      {Row}
    </List>
  )
})

// List-based virtualized content list for simpler layouts
const VirtualizedContentList = memo(function VirtualizedContentList({
  items,
  onView,
  onEdit,
  onPublish,
  onDelete,
  onRegenerateImage,
  formatDate,
  getStatusIcon,
  getStatusColor,
  getContentTypeIcon,
  height = 600,
  itemHeight = 120
}) {
  const itemData = {
    items,
    onView,
    onEdit,
    onPublish,
    onDelete,
    onRegenerateImage,
    formatDate,
    getStatusIcon,
    getStatusColor,
    getContentTypeIcon
  }

  const ListItem = useCallback(({ index, style }) => {
    const item = items[index]

    if (!item) {
      return (
        <div style={style} className="p-2">
          <div className="bg-white rounded-lg shadow p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      )
    }

    return (
      <div style={style} className="p-2">
        <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                {getContentTypeIcon(item.content_type)}
                <h3 className="font-medium text-gray-900 truncate">
                  {item.title || 'Untitled'}
                </h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                  {item.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 truncate mb-2">
                {item.content || 'No content preview available'}
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span className="capitalize">{item.platform || 'All platforms'}</span>
                <span>{formatDate(item.scheduled_at || item.created_at)}</span>
                <div className="flex items-center space-x-1">
                  {getStatusIcon(item.status)}
                  <span>{item.performance?.views || 0} views</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-1 ml-4">
              <button
                onClick={() => onView(item)}
                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                title="View"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => onEdit(item)}
                className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                title="Edit"
              >
                <PencilIcon className="h-4 w-4" />
              </button>
              {(item.content_type === 'image' || item.image_url) && onRegenerateImage && (
                <button
                  onClick={() => onRegenerateImage(item)}
                  className="p-1 text-gray-400 hover:text-purple-600 transition-colors"
                  title="Regenerate Image"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>
              )}
              {item.status === 'draft' && (
                <button
                  onClick={() => onPublish(item.id)}
                  className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                  title="Publish"
                >
                  <ShareIcon className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => onDelete(item.id)}
                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                title="Delete"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }, [items, onView, onEdit, onPublish, onDelete, onRegenerateImage, formatDate, getStatusIcon, getStatusColor, getContentTypeIcon])

  if (items.length === 0) {
    return null
  }

  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemHeight}
      itemData={itemData}
    >
      {ListItem}
    </List>
  )
})

export default VirtualizedContentList
export { VirtualizedContentGrid }