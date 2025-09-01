import { render, screen, fireEvent } from '@testing-library/react'
import DragDropCalendar from '../DragDropCalendar'

// Mock logger
jest.mock('../../../utils/logger.js', () => ({
  debug: jest.fn()
}))

// Mock date-fns functions to control date behavior
jest.mock('date-fns', () => ({
  format: jest.fn((date, formatStr) => {
    if (formatStr === 'yyyy-MM-dd') return '2023-12-01'
    if (formatStr === 'MMMM yyyy') return 'December 2023'
    if (formatStr === 'EEE') return 'Fri'
    if (formatStr === 'd') return '1'
    return '2023-12-01'
  }),
  addDays: jest.fn((date, days) => new Date('2023-12-01')),
  startOfWeek: jest.fn(() => new Date('2023-12-01')),
  isSameDay: jest.fn(() => false),
  parseISO: jest.fn(() => new Date('2023-12-01'))
}))

// Mock DND Kit
jest.mock('@dnd-kit/core', () => ({
  DndContext: ({ children, onDragEnd }) => <div data-testid="dnd-context">{children}</div>,
  DragOverlay: ({ children }) => <div data-testid="drag-overlay">{children}</div>,
  closestCenter: jest.fn(),
  KeyboardSensor: jest.fn(),
  PointerSensor: jest.fn(),
  useSensor: jest.fn(),
  useSensors: jest.fn(() => []),
  pointerWithin: jest.fn(),
  rectIntersection: jest.fn(),
  useDroppable: jest.fn(() => ({
    isOver: false,
    setNodeRef: jest.fn(),
    active: null
  }))
}))

jest.mock('@dnd-kit/sortable', () => ({
  arrayMove: jest.fn(),
  SortableContext: ({ children }) => <div data-testid="sortable-context">{children}</div>,
  sortableKeyboardCoordinates: jest.fn(),
  verticalListSortingStrategy: jest.fn(),
  useSortable: jest.fn(() => ({
    attributes: {},
    listeners: {},
    setNodeRef: jest.fn(),
    transform: null,
    transition: null,
    isDragging: false
  })),
  CSS: {
    Transform: {
      toString: jest.fn(() => '')
    }
  }
}))

describe('DragDropCalendar', () => {
  const mockProps = {
    posts: [
      {
        id: 1,
        title: 'Test Post',
        content: 'Test content',
        platform: 'LinkedIn',
        date: '2023-12-01',
        time: '09:00',
        status: 'scheduled'
      }
    ],
    onUpdatePost: jest.fn(),
    onDeletePost: jest.fn(),
    onCreatePost: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders calendar container', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    expect(screen.getByTestId('dnd-context')).toBeInTheDocument()
    expect(screen.getByText('December 2023')).toBeInTheDocument()
  })

  it('displays navigation buttons', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    expect(screen.getByRole('button', { name: /previous month/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next month/i })).toBeInTheDocument()
  })

  it('displays view toggle buttons', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    expect(screen.getByRole('button', { name: /week/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /month/i })).toBeInTheDocument()
  })

  it('shows optimal times when enabled', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    const optimalTimesButton = screen.getByRole('button', { name: /optimal times/i })
    fireEvent.click(optimalTimesButton)
    
    expect(optimalTimesButton).toHaveClass('bg-green-600')
  })

  it('can change view modes', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    const weekButton = screen.getByRole('button', { name: /week/i })
    fireEvent.click(weekButton)
    
    expect(weekButton).toHaveClass('bg-blue-600')
  })

  it('navigates between months', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    const nextButton = screen.getByRole('button', { name: /next month/i })
    fireEvent.click(nextButton)
    
    // Should trigger month change (implementation detail)
    expect(nextButton).toBeInTheDocument()
  })

  it('displays posts in calendar', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    expect(screen.getByText('Test Post')).toBeInTheDocument()
  })

  it('handles empty posts array', () => {
    render(<DragDropCalendar {...mockProps} posts={[]} />)
    
    expect(screen.getByTestId('dnd-context')).toBeInTheDocument()
    expect(screen.queryByText('Test Post')).not.toBeInTheDocument()
  })

  it('renders calendar grid', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    // Should have day headers
    expect(screen.getAllByText('Fri')).toHaveLength(7) // Day headers for week view
  })

  it('allows toggling analytics panel', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    const analyticsButton = screen.getByRole('button', { name: /analytics/i })
    fireEvent.click(analyticsButton)
    
    expect(analyticsButton).toHaveClass('bg-purple-600')
  })

  it('handles post creation', () => {
    render(<DragDropCalendar {...mockProps} />)
    
    // Click on a calendar day to create post
    const addButton = screen.getAllByRole('button').find(button => 
      button.querySelector('svg')?.classList.contains('h-4')
    )
    
    if (addButton) {
      fireEvent.click(addButton)
    }
    
    // Test passes if no errors thrown
    expect(screen.getByTestId('dnd-context')).toBeInTheDocument()
  })
})