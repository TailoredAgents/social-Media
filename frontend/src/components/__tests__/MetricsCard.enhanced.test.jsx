import { render, screen } from '@testing-library/react'
import MetricsCard from '../MetricsCard'

const MockIcon = () => <div data-testid="mock-icon">Icon</div>

describe('MetricsCard Component', () => {
  const defaultStat = {
    name: 'Test Metric',
    value: '123',
    change: '+5.2%',
    changeType: 'increase',
    icon: MockIcon
  }

  it('renders all required elements', () => {
    render(<MetricsCard stat={defaultStat} />)
    
    expect(screen.getByText('Test Metric')).toBeInTheDocument()
    expect(screen.getByText('123')).toBeInTheDocument()
    expect(screen.getByText('+5.2%')).toBeInTheDocument()
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument()
  })

  it('applies correct styling for increase trend', () => {
    render(<MetricsCard stat={{ ...defaultStat, changeType: 'increase', change: '+5.2%' }} />)
    
    const changeElement = screen.getByText('+5.2%').parentElement
    expect(changeElement).toHaveClass('text-green-600')
  })

  it('applies correct styling for decrease trend', () => {
    render(<MetricsCard stat={{ ...defaultStat, changeType: 'decrease', change: '-3.1%' }} />)
    
    const changeElement = screen.getByText('-3.1%').parentElement
    expect(changeElement).toHaveClass('text-red-600')
  })

  it('shows up arrow for increase', () => {
    render(<MetricsCard stat={{ ...defaultStat, changeType: 'increase' }} />)
    
    // Check that the up arrow is present (ArrowUpIcon)
    const changeSection = screen.getByText('+5.2%').closest('div')
    expect(changeSection).toHaveClass('text-green-600')
  })

  it('shows down arrow for decrease', () => {
    render(<MetricsCard stat={{ ...defaultStat, changeType: 'decrease', change: '-3.1%' }} />)
    
    // Check that the down arrow is present (ArrowDownIcon)
    const changeSection = screen.getByText('-3.1%').closest('div')
    expect(changeSection).toHaveClass('text-red-600')
  })

  it('handles large numbers in value', () => {
    render(<MetricsCard stat={{ ...defaultStat, value: '1,234,567' }} />)
    
    expect(screen.getByText('1,234,567')).toBeInTheDocument()
  })

  it('displays metric name correctly', () => {
    render(<MetricsCard stat={{ ...defaultStat, name: 'Custom Metric Name' }} />)
    
    expect(screen.getByText('Custom Metric Name')).toBeInTheDocument()
  })
})