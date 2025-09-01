import React, { useEffect, useRef } from 'react'

const SimilarityChart = React.memo(function SimilarityChart({ content, onNodeClick }) {
  const canvasRef = useRef()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !content?.length) return

    const ctx = canvas.getContext('2d')
    const rect = canvas.getBoundingClientRect()
    
    // Set canvas size
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    const width = rect.width
    const height = rect.height
    const centerX = width / 2
    const centerY = height / 2

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Create nodes based on similarity scores
    const nodes = content.map((item, index) => ({
      id: item.id,
      title: item.title,
      similarity: item.similarity_score || 0,
      type: item.type,
      x: centerX + Math.cos((index / content.length) * 2 * Math.PI) * (100 + item.similarity_score * 50),
      y: centerY + Math.sin((index / content.length) * 2 * Math.PI) * (100 + item.similarity_score * 50),
      radius: 8 + item.similarity_score * 15
    }))

    // Draw connections for highly similar content
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.2)'
    ctx.lineWidth = 1
    nodes.forEach((node, i) => {
      nodes.slice(i + 1).forEach(otherNode => {
        const distance = Math.sqrt(
          Math.pow(node.x - otherNode.x, 2) + Math.pow(node.y - otherNode.y, 2)
        )
        const similarity = Math.abs(node.similarity - otherNode.similarity)
        
        if (similarity < 0.1 && distance < 200) {
          ctx.beginPath()
          ctx.moveTo(node.x, node.y)
          ctx.lineTo(otherNode.x, otherNode.y)
          ctx.stroke()
        }
      })
    })

    // Draw nodes
    nodes.forEach(node => {
      // Node circle
      ctx.fillStyle = getTypeColor(node.type)
      ctx.beginPath()
      ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI)
      ctx.fill()

      // Node border
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()

      // Similarity score
      ctx.fillStyle = '#fff'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(
        Math.round(node.similarity * 100) + '%',
        node.x,
        node.y + 3
      )
    })

    // Add event listener for clicks
    const handleClick = (event) => {
      const rect = canvas.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top

      const clickedNode = nodes.find(node => {
        const distance = Math.sqrt(
          Math.pow(x - node.x, 2) + Math.pow(y - node.y, 2)
        )
        return distance <= node.radius
      })

      if (clickedNode && onNodeClick) {
        onNodeClick(clickedNode.id)
      }
    }

    canvas.addEventListener('click', handleClick)
    return () => canvas.removeEventListener('click', handleClick)
  }, [content, onNodeClick])

  const getTypeColor = (type) => {
    const colors = {
      research: '#10b981',
      content: '#3b82f6',
      image: '#f59e0b',
      competitor_analysis: '#8b5cf6',
      default: '#6b7280'
    }
    return colors[type] || colors.default
  }

  return (
    <div className="relative w-full h-64">
      <canvas
        ref={canvasRef}
        className="w-full h-full border rounded-lg"
        style={{ cursor: 'pointer' }}
      />
      <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm rounded p-2 text-xs">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Research</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Content</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span>Images</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span>Analysis</span>
          </div>
        </div>
      </div>
    </div>
  )
})

export default SimilarityChart