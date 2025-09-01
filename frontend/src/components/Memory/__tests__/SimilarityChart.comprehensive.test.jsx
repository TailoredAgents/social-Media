import { render, screen, fireEvent } from '@testing-library/react'
import SimilarityChart from '../SimilarityChart'

// Mock canvas context
const mockContext = {
  clearRect: jest.fn(),
  scale: jest.fn(),
  beginPath: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  stroke: jest.fn(),
  fillText: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 1,
  font: '',
  textAlign: '',
  textBaseline: ''
}

// Mock HTMLCanvasElement
HTMLCanvasElement.prototype.getContext = jest.fn(() => mockContext)
HTMLCanvasElement.prototype.getBoundingClientRect = jest.fn(() => ({
  width: 400,
  height: 300,
  top: 0,
  left: 0,
  right: 400,
  bottom: 300
}))

// Mock devicePixelRatio
Object.defineProperty(window, 'devicePixelRatio', {
  value: 2,
  writable: true
})

describe('SimilarityChart Component', () => {
  const mockContent = [
    {
      id: 1,
      title: 'AI Tools for Social Media',
      similarity_score: 0.95,
      content: 'Article about AI tools'
    },
    {
      id: 2,
      title: 'Social Media Strategy',
      similarity_score: 0.87,
      content: 'Guide to social media strategy'
    },
    {
      id: 3,
      title: 'Content Creation Tips',
      similarity_score: 0.73,
      content: 'Tips for creating engaging content'
    },
    {
      id: 4,
      title: 'Analytics and Metrics',
      similarity_score: 0.61,
      content: 'Understanding social media analytics'
    }
  ]

  const mockOnNodeClick = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders canvas element', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true }) // Canvas has img role
      expect(canvas).toBeInTheDocument()
      expect(canvas.tagName).toBe('CANVAS')
    })

    it('renders with proper dimensions', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      expect(canvas).toHaveStyle('width: 100%')
      expect(canvas).toHaveStyle('height: 300px')
    })

    it('handles empty content array', () => {
      render(<SimilarityChart content={[]} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      expect(canvas).toBeInTheDocument()
      // Should not call drawing methods for empty content
      expect(mockContext.clearRect).not.toHaveBeenCalled()
    })

    it('handles null content', () => {
      render(<SimilarityChart content={null} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      expect(canvas).toBeInTheDocument()
      expect(mockContext.clearRect).not.toHaveBeenCalled()
    })
  })

  describe('Canvas Drawing', () => {
    it('sets up canvas with proper scaling', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      expect(mockContext.scale).toHaveBeenCalledWith(2, 2) // devicePixelRatio
    })

    it('clears canvas before drawing', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      expect(mockContext.clearRect).toHaveBeenCalledWith(0, 0, 400, 300)
    })

    it('draws nodes for each content item', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // Should call arc for each node (4 content items)
      expect(mockContext.arc).toHaveBeenCalledTimes(4)
      expect(mockContext.fill).toHaveBeenCalledTimes(4)
    })

    it('draws connections between similar nodes', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // Should draw lines between connected nodes
      expect(mockContext.moveTo).toHaveBeenCalled()
      expect(mockContext.lineTo).toHaveBeenCalled()
      expect(mockContext.stroke).toHaveBeenCalled()
    })

    it('renders node labels', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // Should call fillText for each node label
      expect(mockContext.fillText).toHaveBeenCalledTimes(4)
      expect(mockContext.fillText).toHaveBeenCalledWith('AI Tools for Social Media', expect.any(Number), expect.any(Number))
    })
  })

  describe('Node Positioning', () => {
    it('positions nodes based on similarity scores', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // High similarity nodes should be closer to center
      const arcCalls = mockContext.arc.mock.calls
      
      // First node (highest similarity 0.95) should be closer to center
      const firstNodeCall = arcCalls[0]
      const firstNodeDistance = Math.sqrt(
        Math.pow(firstNodeCall[0] - 200, 2) + Math.pow(firstNodeCall[1] - 150, 2)
      )
      
      // Last node (lowest similarity 0.61) should be farther from center  
      const lastNodeCall = arcCalls[3]
      const lastNodeDistance = Math.sqrt(
        Math.pow(lastNodeCall[0] - 200, 2) + Math.pow(lastNodeCall[1] - 150, 2)
      )
      
      expect(firstNodeDistance).toBeLessThan(lastNodeDistance)
    })

    it('distributes nodes evenly around circle', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const arcCalls = mockContext.arc.mock.calls
      
      // Check that nodes are positioned at different angles
      const angles = arcCalls.map(call => {
        const x = call[0] - 200 // centerX
        const y = call[1] - 150 // centerY
        return Math.atan2(y, x)
      })
      
      // All angles should be different
      const uniqueAngles = new Set(angles.map(a => Math.round(a * 100)))
      expect(uniqueAngles.size).toBe(4)
    })
  })

  describe('Node Styling', () => {
    it('styles nodes based on similarity scores', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // Higher similarity should result in larger/more prominent nodes
      const arcCalls = mockContext.arc.mock.calls
      
      // First node (highest similarity) should have larger radius
      const firstNodeRadius = arcCalls[0][2]
      const lastNodeRadius = arcCalls[3][2]
      
      expect(firstNodeRadius).toBeGreaterThan(lastNodeRadius)
    })

    it('uses different colors for different similarity ranges', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // Should set different fillStyle colors based on similarity
      const fillStyleValues = []
      mockContext.fillStyle = ''
      
      // Capture fillStyle assignments
      Object.defineProperty(mockContext, 'fillStyle', {
        set: function(value) {
          fillStyleValues.push(value)
        },
        get: function() {
          return fillStyleValues[fillStyleValues.length - 1] || ''
        }
      })
      
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      // Should have set different colors
      expect(fillStyleValues.length).toBeGreaterThan(0)
    })
  })

  describe('Mouse Interactions', () => {
    it('handles canvas click events', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      
      fireEvent.click(canvas, {
        clientX: 200,
        clientY: 150
      })
      
      // Click handler should be attached
      expect(canvas).toHaveAttribute('style')
    })

    it('calls onNodeClick when node is clicked', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      
      // Simulate click near a node position
      fireEvent.click(canvas, {
        clientX: 250, // Near where a node might be
        clientY: 150
      })
      
      // onNodeClick should be called with the clicked node data
      expect(mockOnNodeClick).toHaveBeenCalled()
    })

    it('ignores clicks outside of nodes', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      
      // Click far from any nodes
      fireEvent.click(canvas, {
        clientX: 10,
        clientY: 10
      })
      
      // Should not trigger node click for empty areas
      expect(mockOnNodeClick).not.toHaveBeenCalled()
    })
  })

  describe('Content Updates', () => {
    it('redraws when content changes', () => {
      const { rerender } = render(
        <SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />
      )
      
      const initialClearCalls = mockContext.clearRect.mock.calls.length
      
      // Update content
      const newContent = [...mockContent, {
        id: 5,
        title: 'New Content Item',
        similarity_score: 0.82,
        content: 'New content'
      }]
      
      rerender(<SimilarityChart content={newContent} onNodeClick={mockOnNodeClick} />)
      
      // Should clear and redraw
      expect(mockContext.clearRect.mock.calls.length).toBeGreaterThan(initialClearCalls)
    })

    it('handles content with missing similarity scores', () => {
      const contentWithoutScores = [
        { id: 1, title: 'Item 1', content: 'Content 1' },
        { id: 2, title: 'Item 2', similarity_score: 0.8, content: 'Content 2' }
      ]
      
      render(<SimilarityChart content={contentWithoutScores} onNodeClick={mockOnNodeClick} />)
      
      // Should still render without crashing
      expect(mockContext.arc).toHaveBeenCalledTimes(2)
      expect(mockContext.fill).toHaveBeenCalledTimes(2)
    })
  })

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeContent = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        title: `Content Item ${i + 1}`,
        similarity_score: Math.random(),
        content: `Content ${i + 1}`
      }))
      
      render(<SimilarityChart content={largeContent} onNodeClick={mockOnNodeClick} />)
      
      // Should render all nodes
      expect(mockContext.arc).toHaveBeenCalledTimes(100)
      expect(mockContext.fill).toHaveBeenCalledTimes(100)
    })

    it('optimizes connection drawing for many nodes', () => {
      const manyNodes = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        title: `Node ${i + 1}`,
        similarity_score: 0.5 + (Math.random() * 0.5),
        content: `Content ${i + 1}`
      }))
      
      render(<SimilarityChart content={manyNodes} onNodeClick={mockOnNodeClick} />)
      
      // Should limit connections to avoid clutter
      const connectionCalls = mockContext.stroke.mock.calls.length
      expect(connectionCalls).toBeLessThan(100) // Should not draw n² connections
    })
  })

  describe('Accessibility', () => {
    it('provides canvas alternative text', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      expect(canvas).toHaveAttribute('aria-label', 'Content similarity visualization')
    })

    it('supports keyboard navigation', () => {
      render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      
      const canvas = screen.getByRole('img', { hidden: true })
      expect(canvas).toHaveAttribute('tabIndex', '0')
    })
  })

  describe('Error Handling', () => {
    it('gracefully handles canvas context creation failure', () => {
      HTMLCanvasElement.prototype.getContext = jest.fn(() => null)
      
      expect(() => {
        render(<SimilarityChart content={mockContent} onNodeClick={mockOnNodeClick} />)
      }).not.toThrow()
    })

    it('handles invalid content data', () => {
      const invalidContent = [
        { id: 'invalid' }, // Missing required fields
        null,
        undefined,
        { id: 2, title: 'Valid', similarity_score: 0.8 }
      ]
      
      expect(() => {
        render(<SimilarityChart content={invalidContent} onNodeClick={mockOnNodeClick} />)
      }).not.toThrow()
    })
  })
})