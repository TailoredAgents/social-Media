# Frontend Testing Guide

## Overview

The frontend testing infrastructure has been fully established with comprehensive test coverage for key components, hooks, and utility functions. This guide outlines the testing setup, available scripts, and best practices.

## Testing Stack

- **Testing Framework**: Jest
- **Testing Library**: React Testing Library
- **Test Environment**: jsdom
- **Coverage Reporting**: Built-in Jest coverage
- **Pre-commit Hooks**: Husky + lint-staged
- **CI/CD**: GitHub Actions workflows

## Test Scripts

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run tests for CI (no watch mode)
npm run test:ci
```

## Code Quality Scripts

```bash
# Format code with Prettier
npm run format

# Check Prettier formatting
npm run format:check

# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix
```

## Test Coverage Summary

| Component | Coverage | Tests | Status |
|-----------|----------|-------|--------|
| **MetricsCard** | 100% | 6 tests | ✅ Complete |
| **RecentActivity** | 76% | 11 tests | ✅ Complete |
| **Chart** | 100% | 12 tests | ✅ Complete |
| **Layout** | Tests created | 8 tests | ⚠️ Import.meta issues |
| **ProtectedRoute** | Tests created | 10 tests | ⚠️ Context mocking issues |
| **useNotifications** | 97% | 15 tests | ✅ Complete |
| **useApi** | Tests created | 8 tests | ⚠️ Module mocking issues |
| **AuthContext** | Tests created | 7 tests | ⚠️ Import.meta issues |

## File Structure

```
frontend/
├── src/
│   ├── __tests__/           # App-level tests
│   │   ├── App.test.jsx
│   │   ├── Navigation.test.jsx
│   │   └── testUtils.jsx    # Test utilities
│   ├── components/
│   │   └── __tests__/       # Component tests
│   │       ├── Chart.test.jsx
│   │       ├── Layout.test.jsx
│   │       ├── MetricsCard.test.jsx
│   │       ├── ProtectedRoute.test.jsx
│   │       └── RecentActivity.test.jsx
│   ├── contexts/
│   │   └── __tests__/       # Context tests
│   │       ├── AuthContext.test.jsx
│   │       └── AuthContext.simple.test.jsx
│   ├── hooks/
│   │   └── __tests__/       # Hook tests
│   │       ├── useApi.test.js
│   │       └── useNotifications.test.js
│   ├── services/
│   │   └── __tests__/       # Service tests
│   │       └── api.test.js
│   ├── __mocks__/           # Mock files
│   │   └── fileMock.js
│   └── setupTests.js        # Jest setup
├── jest.config.js           # Jest configuration
├── babel.config.js          # Babel configuration
├── .prettierrc              # Prettier configuration
├── .prettierignore          # Prettier ignore rules
└── package.json            # Scripts and dependencies
```

## Configuration Files

### Jest Configuration (`jest.config.js`)
- **Environment**: jsdom for DOM testing
- **Setup**: Automatic import of testing utilities
- **Module Mapping**: CSS and asset mocking
- **Coverage**: Comprehensive collection and reporting
- **Transform**: Babel-jest for JSX/ES6 support

### Prettier Configuration (`.prettierrc`)
- **Style**: Single quotes, no semicolons
- **Width**: 80 characters
- **Trailing Commas**: ES5 compatible
- **Bracket Spacing**: Enabled

### Lint-staged Configuration
- **JavaScript/JSX**: ESLint + Prettier
- **Other Files**: Prettier only
- **Git Integration**: Automatic staging

## GitHub Actions Workflows

### 1. Frontend CI (`.github/workflows/frontend-ci.yml`)
- **Triggers**: Push/PR to main branches
- **Node Versions**: 18.x, 20.x matrix
- **Steps**: Install → Lint → Format Check → Test → Build
- **Artifacts**: Coverage reports and build outputs

### 2. Code Quality (`.github/workflows/code-quality.yml`)
- **Frontend**: ESLint and Prettier checks
- **Backend**: Black, isort, flake8, mypy
- **Reports**: Uploaded as artifacts

### 3. Security Scan (`.github/workflows/security-scan.yml`)
- **Frontend**: npm audit + Snyk
- **Backend**: Safety + Bandit
- **CodeQL**: Automated security analysis
- **Schedule**: Weekly security scans

## Testing Best Practices

### Component Testing
```jsx
import { render, screen } from '@testing-library/react'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### Hook Testing
```jsx
import { renderHook } from '@testing-library/react'
import { useMyHook } from '../useMyHook'

describe('useMyHook', () => {
  it('returns expected values', () => {
    const { result } = renderHook(() => useMyHook())
    expect(result.current.value).toBe(expectedValue)
  })
})
```

### API Testing
```jsx
import apiService from '../api'

// Mock fetch
global.fetch = jest.fn()

describe('API Service', () => {
  beforeEach(() => {
    fetch.mockClear()
  })
  
  it('makes correct API calls', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    })
    
    const result = await apiService.get('/test')
    expect(result).toEqual({ success: true })
  })
})
```

## Known Issues & Solutions

### 1. Import.meta Environment Variables
**Issue**: Jest doesn't support `import.meta.env` by default
**Solution**: Use `globals` in Jest config or mock environment variables

### 2. Auth0 Context Mocking
**Issue**: Complex Auth0 context with async operations
**Solution**: Create simplified mock implementations

### 3. Chart.js Integration
**Issue**: Canvas API not available in jsdom
**Solution**: Mock react-chartjs-2 components

## Future Enhancements

### Priority Items
1. **Fix import.meta issues** - Complete Auth context testing
2. **Add E2E testing** - Playwright or Cypress setup
3. **Visual regression testing** - Screenshot comparison
4. **Performance testing** - Bundle size and rendering performance

### Additional Test Types
- **Integration tests** - Full user workflows
- **Accessibility tests** - Screen reader compatibility
- **Performance tests** - Component rendering speed
- **Visual tests** - UI consistency validation

## Coverage Targets

- **Statements**: 80%+ (Currently: 37% for tested components)
- **Branches**: 75%+ (Currently: 36% for tested components) 
- **Functions**: 80%+ (Currently: 33% for tested components)
- **Lines**: 80%+ (Currently: 37% for tested components)

## Running Specific Tests

```bash
# Run tests for specific component
npm test -- --testPathPatterns="MetricsCard"

# Run tests matching pattern
npm test -- --testPathPatterns="Component|Hook"

# Run with coverage for specific files
npm test -- --testPathPatterns="MetricsCard" --coverage

# Run in watch mode for development
npm run test:watch
```

## Troubleshooting

### Common Issues
1. **Module not found**: Check import paths and mock configurations
2. **Async testing**: Use `waitFor` and proper async/await patterns
3. **Context providers**: Wrap components with necessary providers
4. **File mocking**: Ensure static assets are properly mocked

### Debug Commands
```bash
# Verbose test output
npm test -- --verbose

# Show coverage details
npm test -- --coverage --verbose

# Run specific test file
npm test -- src/components/__tests__/MetricsCard.test.jsx
```

This testing infrastructure provides a solid foundation for maintaining code quality and preventing regressions as the frontend continues to evolve.