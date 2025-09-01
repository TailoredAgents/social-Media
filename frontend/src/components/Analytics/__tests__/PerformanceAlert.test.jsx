import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import PerformanceAlert, { 
  PerformanceMetricAlert, 
  SystemHealthAlert, 
  EngagementAlert, 
  ViralAlert, 
  OptimizationAlert 
} from '../PerformanceAlert'

describe('PerformanceAlert Component', () => {
  // Basic rendering tests
  describe('Basic Rendering', () => {
    test('renders alert with title and message', () => {
      render(
        <PerformanceAlert 
          title="Test Alert" 
          message="This is a test message" 
        />
      )
      
      expect(screen.getByText('Test Alert')).toBeInTheDocument()
      expect(screen.getByText('This is a test message')).toBeInTheDocument()
    })

    test('renders with default info type when no type specified', () => {
      render(<PerformanceAlert title="Default Alert" />)
      
      const alertElement = screen.getByText('Default Alert').closest('div')
      expect(alertElement).toHaveClass('bg-blue-50', 'border-blue-200')
    })

    test('renders with correct styling for each alert type', () => {
      const types = ['error', 'warning', 'info', 'success', 'insight']
      const expectedClasses = {
        error: ['bg-red-50', 'border-red-200'],
        warning: ['bg-yellow-50', 'border-yellow-200'],
        info: ['bg-blue-50', 'border-blue-200'],
        success: ['bg-green-50', 'border-green-200'],
        insight: ['bg-purple-50', 'border-purple-200']
      }

      types.forEach(type => {
        const { unmount } = render(
          <PerformanceAlert type={type} title={`${type} Alert`} />
        )
        
        const alertElement = screen.getByText(`${type} Alert`).closest('div')
        expectedClasses[type].forEach(className => {
          expect(alertElement).toHaveClass(className)
        })
        
        unmount()
      })
    })
  })

  // Interaction tests
  describe('User Interactions', () => {
    test('calls onDismiss when dismiss button is clicked', () => {
      const mockOnDismiss = jest.fn()
      
      render(
        <PerformanceAlert 
          title="Dismissible Alert" 
          onDismiss={mockOnDismiss}
          dismissible={true}
        />
      )
      
      const dismissButton = screen.getByLabelText('Dismiss alert')
      fireEvent.click(dismissButton)
      
      expect(mockOnDismiss).toHaveBeenCalledTimes(1)
    })

    test('hides alert after dismiss button is clicked', async () => {
      render(
        <PerformanceAlert 
          title="Dismissible Alert" 
          dismissible={true}
        />
      )
      
      expect(screen.getByText('Dismissible Alert')).toBeInTheDocument()
      
      const dismissButton = screen.getByLabelText('Dismiss alert')
      fireEvent.click(dismissButton)
      
      await waitFor(() => {
        expect(screen.queryByText('Dismissible Alert')).not.toBeInTheDocument()
      })
    })

    test('calls onAction when action button is clicked', () => {
      const mockOnAction = jest.fn()
      
      render(
        <PerformanceAlert 
          title="Action Alert" 
          action="Take Action"
          onAction={mockOnAction}
        />
      )
      
      const actionButton = screen.getByText('Take Action')
      fireEvent.click(actionButton)
      
      expect(mockOnAction).toHaveBeenCalledTimes(1)
    })

    test('does not show dismiss button when dismissible is false', () => {
      render(
        <PerformanceAlert 
          title="Non-dismissible Alert" 
          dismissible={false}
        />
      )
      
      expect(screen.queryByLabelText('Dismiss alert')).not.toBeInTheDocument()
    })

    test('does not show dismiss button when persistent is true', () => {
      render(
        <PerformanceAlert 
          title="Persistent Alert" 
          persistent={true}
        />
      )
      
      expect(screen.queryByLabelText('Dismiss alert')).not.toBeInTheDocument()
    })
  })

  // Metric and data display tests
  describe('Metric Display', () => {
    test('displays metric information when provided', () => {
      render(
        <PerformanceAlert 
          title="Metric Alert"
          metric="Response Time"
          currentValue="250ms"
          threshold="200ms"
        />
      )
      
      expect(screen.getByText('Response Time')).toBeInTheDocument()
      expect(screen.getByText('250ms')).toBeInTheDocument()
      expect(screen.getByText('200ms')).toBeInTheDocument()
    })

    test('displays timestamp with proper formatting', () => {
      const timestamp = new Date('2025-07-28T10:00:00Z').toISOString()
      
      render(
        <PerformanceAlert 
          title="Timestamped Alert"
          timestamp={timestamp}
        />
      )
      
      // Should display some form of time (exact format may vary)
      expect(screen.getByText(/ago|Just now|\/\d+\/\d+/)).toBeInTheDocument()
    })

    test('formats recent timestamps as "Just now"', () => {
      const recentTimestamp = new Date().toISOString()
      
      render(
        <PerformanceAlert 
          title="Recent Alert"
          timestamp={recentTimestamp}
        />
      )
      
      expect(screen.getByText('Just now')).toBeInTheDocument()
    })
  })

  // Edge cases and error handling
  describe('Edge Cases', () => {
    test('handles invalid alert type gracefully', () => {
      render(
        <PerformanceAlert 
          type="invalid-type"
          title="Invalid Type Alert" 
        />
      )
      
      // Should fall back to info styling
      const alertElement = screen.getByText('Invalid Type Alert').closest('div')
      expect(alertElement).toHaveClass('bg-blue-50', 'border-blue-200')
    })

    test('renders without message when not provided', () => {
      render(<PerformanceAlert title="Title Only" />)
      
      expect(screen.getByText('Title Only')).toBeInTheDocument()
      expect(screen.queryByText('This is a test message')).not.toBeInTheDocument()
    })

    test('renders without action button when action is not provided', () => {
      render(<PerformanceAlert title="No Action Alert" />)
      
      expect(screen.queryByRole('button', { name: /take action/i })).not.toBeInTheDocument()
    })
  })
})

// Specialized component tests
describe('PerformanceMetricAlert', () => {
  test('renders warning when current value exceeds threshold', () => {
    render(
      <PerformanceMetricAlert 
        title="High Response Time"
        metric="API Response"
        currentValue={300}
        threshold={200}
        comparison="above"
      />
    )
    
    const alertElement = screen.getByText('High Response Time').closest('div')
    expect(alertElement).toHaveClass('bg-yellow-50', 'border-yellow-200')
  })

  test('renders success when current value is below threshold', () => {
    render(
      <PerformanceMetricAlert 
        title="Good Response Time"
        metric="API Response"
        currentValue={150}
        threshold={200}
        comparison="above"
      />
    )
    
    const alertElement = screen.getByText('Good Response Time').closest('div')
    expect(alertElement).toHaveClass('bg-green-50', 'border-green-200')
  })
})

describe('SystemHealthAlert', () => {
  test('renders success alert for healthy status', () => {
    render(
      <SystemHealthAlert 
        component="Database"
        status="healthy"
        uptime="99.9%"
      />
    )
    
    expect(screen.getByText('Database Status: healthy')).toBeInTheDocument()
    expect(screen.getByText('Uptime: 99.9%')).toBeInTheDocument()
    
    const alertElement = screen.getByText('Database Status: healthy').closest('div')
    expect(alertElement).toHaveClass('bg-green-50')
  })

  test('renders warning alert for degraded status', () => {
    render(
      <SystemHealthAlert 
        component="API"
        status="degraded"
      />
    )
    
    expect(screen.getByText('API Status: degraded')).toBeInTheDocument()
    
    const alertElement = screen.getByText('API Status: degraded').closest('div')
    expect(alertElement).toHaveClass('bg-yellow-50')
  })

  test('renders error alert for down status', () => {
    render(
      <SystemHealthAlert 
        component="Redis"
        status="down"
      />
    )
    
    const alertElement = screen.getByText('Redis Status: down').closest('div')
    expect(alertElement).toHaveClass('bg-red-50')
  })
})

describe('EngagementAlert', () => {
  test('renders success alert for engagement increase', () => {
    render(
      <EngagementAlert 
        platform="Twitter"
        engagementRate={5.5}
        previousRate={4.2}
      />
    )
    
    expect(screen.getByText('Twitter Engagement Increase')).toBeInTheDocument()
    expect(screen.getByText(/improved by.*%/)).toBeInTheDocument()
    expect(screen.getByText('Analyze Success Factors')).toBeInTheDocument()
  })

  test('renders warning alert for engagement decrease', () => {
    render(
      <EngagementAlert 
        platform="LinkedIn"
        engagementRate={3.8}
        previousRate={4.5}
      />
    )
    
    expect(screen.getByText('LinkedIn Engagement Decrease')).toBeInTheDocument()
    expect(screen.getByText(/dropped by.*%/)).toBeInTheDocument()
    expect(screen.getByText('Review Content Strategy')).toBeInTheDocument()
  })
})

describe('ViralAlert', () => {
  test('renders viral content alert', () => {
    render(
      <ViralAlert 
        contentTitle="AI Revolution Post"
        platform="Twitter"
        viralScore={8.5}
        growth={245}
      />
    )
    
    expect(screen.getByText('Content Going Viral!')).toBeInTheDocument()
    expect(screen.getByText(/AI Revolution Post.*Twitter.*8.5.*245%/)).toBeInTheDocument()
    expect(screen.getByText('Boost Similar Content')).toBeInTheDocument()
  })
})

describe('OptimizationAlert', () => {
  test('renders AI optimization suggestion', () => {
    render(
      <OptimizationAlert 
        recommendation="Post during peak hours for 23% better engagement"
        confidence={87}
        platform="Instagram"
      />
    )
    
    expect(screen.getByText('AI Optimization Suggestion')).toBeInTheDocument()
    expect(screen.getByText('Post during peak hours for 23% better engagement')).toBeInTheDocument()
    expect(screen.getByText('Apply Suggestion')).toBeInTheDocument()
    expect(screen.getByText(/Instagram - Confidence: 87%/)).toBeInTheDocument()
  })
})