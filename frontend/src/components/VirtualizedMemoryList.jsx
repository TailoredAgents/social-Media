import React, { memo, useCallback } from 'react'
import { FixedSizeList as List } from 'react-window'
import {
  DocumentTextIcon,
  PhotoIcon,
  ChartBarIcon,
  FunnelIcon,
  EyeIcon,
  ArrowPathIcon,
  PencilIcon,
  TrashIcon,
  HeartIcon,
  ShareIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline'

// Individual memory item component
const MemoryItem = memo(function MemoryItem({ 
  index, 
  style, 
  data: { 
    items, 
    onView, 
    onRepurpose, 
    onEdit, 
    onDelete,
    formatDate,
    getTypeIcon,
    getTypeColor 
  } 
}) {
  const item = items[index]

  if (!item) {
    return (
      <div style={style} className="p-3">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-16 bg-gray-200 rounded mb-4"></div>
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
              {getTypeIcon(item.type)}
              <span className="text-sm font-medium text-gray-600 capitalize">
                {item.type?.replace('_', ' ') || 'content'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              {item.similarity_score && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                  {Math.round(item.similarity_score * 100)}% similar
                </span>
              )}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(item.type)}`}>
                {item.platform}
              </span>
            </div>
          </div>
          
          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
            {item.title || 'Untitled Memory'}
          </h3>
          
          <p className="text-sm text-gray-600 mb-4 line-clamp-3">
            {item.content || 'No content preview available'}
          </p>
          
          <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
            <span>{formatDate(item.created_at)}</span>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <EyeIcon className="h-3 w-3" />
                <span>{item.engagement?.views || 0}</span>
              </div>
              <div className="flex items-center space-x-1">
                <HeartIcon className="h-3 w-3" />
                <span>{item.engagement?.likes || 0}</span>
              </div>
              <div className="flex items-center space-x-1">
                <ShareIcon className="h-3 w-3" />
                <span>{item.engagement?.shares || 0}</span>
              </div>
            </div>
          </div>
          
          {item.tags && item.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-4">
              {item.tags.slice(0, 3).map((tag, tagIndex) => (
                <span
                  key={tagIndex}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
              {item.tags.length > 3 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full">
                  +{item.tags.length - 3} more
                </span>
              )}
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-500">
              {item.repurpose_suggestions > 0 && (
                <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                  {item.repurpose_suggestions} repurpose ideas
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-1">
              <button
                onClick={() => onView(item)}
                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                title="View details"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => onRepurpose(item)}
                className="p-1 text-gray-400 hover:text-purple-600 transition-colors"
                title="Repurpose content"
              >
                <ArrowPathIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => onEdit(item)}
                className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                title="Edit"
              >
                <PencilIcon className="h-4 w-4" />
              </button>
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

// Grid-based virtualized memory list
const VirtualizedMemoryGrid = memo(function VirtualizedMemoryGrid({
  items,
  onView,
  onRepurpose,
  onEdit,
  onDelete,
  formatDate,
  getTypeIcon,
  getTypeColor,
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
                    {getTypeIcon(item.type)}
                    <span className="text-sm font-medium text-gray-600 capitalize">
                      {item.type?.replace('_', ' ') || 'content'}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {item.similarity_score && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                        {Math.round(item.similarity_score * 100)}% similar
                      </span>
                    )}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(item.type)}`}>
                      {item.platform}
                    </span>
                  </div>
                </div>
                
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                  {item.title || 'Untitled Memory'}
                </h3>
                
                <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                  {item.content || 'No content preview available'}
                </p>
                
                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <span>{formatDate(item.created_at)}</span>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1">
                      <EyeIcon className="h-3 w-3" />
                      <span>{item.engagement?.views || 0}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <HeartIcon className="h-3 w-3" />
                      <span>{item.engagement?.likes || 0}</span>
                    </div>
                  </div>
                </div>
                
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {item.tags.slice(0, 2).map((tag, tagIndex) => (
                      <span
                        key={tagIndex}
                        className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {item.tags.length > 2 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full">
                        +{item.tags.length - 2}
                      </span>
                    )}
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-500">
                    {item.repurpose_suggestions > 0 && (
                      <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                        {item.repurpose_suggestions} ideas
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => onView(item)}
                      className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      title="View details"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onRepurpose(item)}
                      className="p-1 text-gray-400 hover:text-purple-600 transition-colors"
                      title="Repurpose content"
                    >
                      <ArrowPathIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onEdit(item)}
                      className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                      title="Edit"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
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
  }, [items, itemsPerRow, onView, onRepurpose, onEdit, onDelete, formatDate, getTypeIcon, getTypeColor])

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
        onRepurpose,
        onEdit,
        onDelete,
        formatDate,
        getTypeIcon,
        getTypeColor
      }}
    >
      {Row}
    </List>
  )
})

// List-based virtualized memory list for compact layouts
const VirtualizedMemoryList = memo(function VirtualizedMemoryList({
  items,
  onView,
  onRepurpose,
  onEdit,
  onDelete,
  formatDate,
  getTypeIcon,
  getTypeColor,
  height = 600,
  itemHeight = 120
}) {
  const itemData = {
    items,
    onView,
    onRepurpose,
    onEdit,
    onDelete,
    formatDate,
    getTypeIcon,
    getTypeColor
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
                {getTypeIcon(item.type)}
                <h3 className="font-medium text-gray-900 truncate">
                  {item.title || 'Untitled Memory'}
                </h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(item.type)}`}>
                  {item.platform}
                </span>
                {item.similarity_score && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                    {Math.round(item.similarity_score * 100)}%
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 truncate mb-2">
                {item.content || 'No content preview available'}
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>{formatDate(item.created_at)}</span>
                <div className="flex items-center space-x-1">
                  <EyeIcon className="h-3 w-3" />
                  <span>{item.engagement?.views || 0}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <HeartIcon className="h-3 w-3" />
                  <span>{item.engagement?.likes || 0}</span>
                </div>
                {item.repurpose_suggestions > 0 && (
                  <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                    {item.repurpose_suggestions} ideas
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-1 ml-4">
              <button
                onClick={() => onView(item)}
                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                title="View details"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => onRepurpose(item)}
                className="p-1 text-gray-400 hover:text-purple-600 transition-colors"
                title="Repurpose content"
              >
                <ArrowPathIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => onEdit(item)}
                className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                title="Edit"
              >
                <PencilIcon className="h-4 w-4" />
              </button>
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
  }, [items, onView, onRepurpose, onEdit, onDelete, formatDate, getTypeIcon, getTypeColor])

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

export default VirtualizedMemoryList
export { VirtualizedMemoryGrid }