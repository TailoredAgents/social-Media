import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ProtectedRoute from '../ProtectedRoute'

// Mock the auth context
const mockAuthContext = {
  isAuthenticated: true,
  isLoading: false,
  hasPermission: jest.fn(),
  hasRole: jest.fn()
}

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

// Mock Navigate component
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Navigate: ({ to, state, replace }) => {
    mockNavigate(to, state, replace)
    return <div data-testid="navigate">Redirecting to {to}</div>
  }
}))

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockAuthContext.isAuthenticated = true
    mockAuthContext.isLoading = false
    mockAuthContext.hasPermission.mockReturnValue(true)
    mockAuthContext.hasRole.mockReturnValue(true)
  })

  it('renders children when authenticated', () => {
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('shows loading spinner when authentication is loading', () => {
    mockAuthContext.isLoading = true
    
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockAuthContext.isAuthenticated = false
    
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(screen.getByTestId('navigate')).toBeInTheDocument()
    expect(screen.getByText('Redirecting to /login')).toBeInTheDocument()
    expect(mockNavigate).toHaveBeenCalledWith('/login', expect.any(Object), true)
  })

  it('shows access denied when permission is required but not granted', () => {
    mockAuthContext.hasPermission.mockReturnValue(false)
    
    renderWithRouter(
      <ProtectedRoute requiredPermission="admin">
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText("You don't have permission to access this page.")).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('shows access denied when role is required but not granted', () => {
    mockAuthContext.hasRole.mockReturnValue(false)
    
    renderWithRouter(
      <ProtectedRoute requiredRole="admin">
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText("You don't have the required role to access this page.")).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('calls hasPermission with correct parameter', () => {
    renderWithRouter(
      <ProtectedRoute requiredPermission="write">
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(mockAuthContext.hasPermission).toHaveBeenCalledWith('write')
  })

  it('calls hasRole with correct parameter', () => {
    renderWithRouter(
      <ProtectedRoute requiredRole="moderator">
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(mockAuthContext.hasRole).toHaveBeenCalledWith('moderator')
  })

  it('renders children when both permission and role requirements are met', () => {
    mockAuthContext.hasPermission.mockReturnValue(true)
    mockAuthContext.hasRole.mockReturnValue(true)
    
    renderWithRouter(
      <ProtectedRoute requiredPermission="write" requiredRole="editor">
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(mockAuthContext.hasPermission).toHaveBeenCalledWith('write')
    expect(mockAuthContext.hasRole).toHaveBeenCalledWith('editor')
  })

  it('shows permission denied when permission check fails even with valid role', () => {
    mockAuthContext.hasPermission.mockReturnValue(false)
    mockAuthContext.hasRole.mockReturnValue(true)
    
    renderWithRouter(
      <ProtectedRoute requiredPermission="admin" requiredRole="user">
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    
    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText("You don't have permission to access this page.")).toBeInTheDocument()
  })
})