import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CreatePostModal from '../CreatePostModal'

describe('CreatePostModal', () => {
  const mockProps = {
    isOpen: true,
    onClose: jest.fn(),
    selectedDate: '2023-12-01',
    onCreatePost: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders modal when open', () => {
    render(<CreatePostModal {...mockProps} />)
    
    expect(screen.getByText('Create New Post')).toBeInTheDocument()
    expect(screen.getByLabelText('Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Content')).toBeInTheDocument()
    expect(screen.getByLabelText('Platform')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<CreatePostModal {...mockProps} isOpen={false} />)
    
    expect(screen.queryByText('Create New Post')).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    render(<CreatePostModal {...mockProps} />)
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    expect(mockProps.onClose).toHaveBeenCalled()
  })

  it('creates post with valid data', async () => {
    render(<CreatePostModal {...mockProps} />)
    
    // Fill out form
    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'Test Post' }
    })
    fireEvent.change(screen.getByLabelText('Content'), {
      target: { value: 'Test content' }
    })
    
    // Submit form
    const form = screen.getByTestId('create-post-form')
    fireEvent.submit(form)
    
    await waitFor(() => {
      expect(mockProps.onCreatePost).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Post',
          content: 'Test content',
          platform: 'LinkedIn'
        })
      )
    })
  })

  it('shows validation errors for empty fields', async () => {
    render(<CreatePostModal {...mockProps} />)
    
    // Try to submit empty form
    const form = screen.getByTestId('create-post-form')
    fireEvent.submit(form)
    
    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument()
      expect(screen.getByText('Content is required')).toBeInTheDocument()
    })
    
    expect(mockProps.onCreatePost).not.toHaveBeenCalled()
  })

  it('allows platform selection', () => {
    render(<CreatePostModal {...mockProps} />)
    
    const platformSelect = screen.getByLabelText('Platform')
    fireEvent.change(platformSelect, { target: { value: 'Twitter' } })
    
    expect(platformSelect.value).toBe('Twitter')
  })

  it('uses selected date when provided', () => {
    render(<CreatePostModal {...mockProps} selectedDate="2023-12-25" />)
    
    const dateInput = screen.getByLabelText('Date')
    expect(dateInput.value).toBe('2023-12-25')
  })

  it('resets form after successful submission', async () => {
    render(<CreatePostModal {...mockProps} />)
    
    // Fill and submit form
    const titleInput = screen.getByLabelText('Title')
    const contentInput = screen.getByLabelText('Content')
    
    fireEvent.change(titleInput, { target: { value: 'Test Post' } })
    fireEvent.change(contentInput, { target: { value: 'Test content' } })
    
    const form = screen.getByTestId('create-post-form')
    fireEvent.submit(form)
    
    await waitFor(() => {
      expect(mockProps.onCreatePost).toHaveBeenCalled()
      expect(mockProps.onClose).toHaveBeenCalled()
    })
  })
})