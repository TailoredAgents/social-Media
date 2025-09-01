# Backend Testing Infrastructure

## Overview
Comprehensive testing infrastructure for the AI Social Media Content Agent backend, organized into unit tests, integration tests, fixtures, and performance benchmarks.

## Directory Structure
```
backend/tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Shared test fixtures and configuration
├── README.md                       # This documentation
├── unit/                          # Unit tests for individual components
│   ├── __init__.py
│   ├── test_content_api.py        # Content API endpoint tests  
│   ├── test_goals_api.py          # Goals API endpoint tests
│   └── test_auth_middleware.py    # Authentication middleware tests
├── integration/                   # Integration tests for workflows
│   ├── __init__.py
│   └── test_workflow_integration.py # End-to-end workflow tests
├── fixtures/                      # Test data factories and fixtures
│   ├── __init__.py
│   └── factories.py               # Model factories for test data generation
└── performance/                   # Performance and benchmark tests
    ├── __init__.py
    └── test_performance_benchmarks.py # Performance regression tests
```

## Test Categories

### Unit Tests (`unit/`)
- **Content API Tests**: Comprehensive testing of content creation, retrieval, updating, scheduling, and publishing
- **Goals API Tests**: Goal management, progress tracking, analytics, and AI recommendations
- **Authentication Tests**: JWT middleware, Auth0 integration, role-based access control

### Integration Tests (`integration/`)
- **Workflow Integration**: End-to-end testing of complete workflows including research, content generation, and posting
- **Multi-platform Testing**: Cross-platform content distribution and social media integrations
- **Error Handling**: Workflow error recovery and retry mechanisms

### Performance Tests (`performance/`)
- **API Performance**: Response time benchmarks and throughput testing
- **Database Performance**: Query optimization and index performance
- **Vector Search**: FAISS performance and embedding generation
- **Concurrent Load**: Multi-threaded performance and resource usage

## Test Fixtures

### Database Fixtures
- `test_db`: Session-scoped test database with automatic cleanup
- `db_session`: Function-scoped database session with transaction rollback
- `test_user`: Authenticated test user with profile data

### Mock Fixtures  
- `mock_openai`: OpenAI API mocking for embeddings and chat completions
- `mock_faiss`: FAISS vector store operations mocking
- `mock_social_apis`: Social media platform API mocking
- `mock_celery`: Background task execution mocking

### Data Factories
- `UserFactory`: Create test users with realistic data
- `ContentItemFactory`: Generate content with performance data
- `GoalFactory`: Create goals with progress tracking
- `MemoryFactory`: Generate semantic memory entries
- `NotificationFactory`: Create user notifications

## Running Tests

### All Tests
```bash
pytest
```

### By Category
```bash
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only  
pytest -m performance             # Performance tests only
```

### By Component
```bash
pytest backend/tests/unit/test_content_api.py     # Content API tests
pytest backend/tests/unit/test_goals_api.py       # Goals API tests
pytest backend/tests/integration/                 # All integration tests
```

### With Coverage
```bash
pytest --cov=backend --cov-report=html
```

### Performance Benchmarks
```bash
pytest -m performance --durations=0
```

## Test Configuration

### Pytest Settings (`pytest.ini`)
- Coverage reporting with 80% minimum threshold
- HTML and XML coverage reports
- Performance markers and timeout settings
- Test environment variable configuration

### Environment Variables
Tests use isolated test environment with:
- SQLite test database (`test.db`)
- Test API keys and authentication
- Mock external service endpoints

## Test Data Management

### Factory Usage
```python
# Create test user
user = UserFactory()

# Create user with specific content
user, contents = create_user_with_content(content_count=10)

# Create high-performing content
content = HighPerformingContentFactory(platform="twitter")
```

### Database Isolation
- Each test gets fresh database session
- Automatic transaction rollback after each test
- No test data pollution between tests

## Performance Benchmarks

### API Response Times
- Content API: < 200ms
- Goals API: < 150ms  
- Memory Search: < 100ms
- Health Check: < 10ms

### Throughput Targets
- Content Creation: > 10 requests/second
- Bulk Operations: > 20 items/second
- Vector Search: < 50ms per query

### Resource Limits
- Memory Usage: < 500MB
- CPU Usage: < 80%
- File Descriptors: < 1000

## Continuous Integration

Tests are designed to run in CI/CD environments with:
- Automated test execution on push/PR
- Coverage reporting and trend tracking
- Performance regression detection
- Parallel test execution support

## Test Best Practices

### Writing New Tests
1. Use appropriate test category markers
2. Follow naming conventions (`test_*`)
3. Use fixtures for common setup
4. Mock external services appropriately
5. Include both positive and negative test cases

### Performance Tests
1. Use `performance_timer` fixture for timing
2. Set realistic performance expectations
3. Test under various load conditions
4. Monitor resource usage

### Database Tests
1. Use `db_session` fixture for database access
2. Create test data with factories
3. Test both success and error conditions
4. Verify proper cleanup

## Maintenance

### Regular Tasks
- Update performance benchmarks as system grows
- Add tests for new features and APIs
- Review and update mock responses
- Monitor test execution times

### Debugging Failed Tests
- Check test logs for detailed error information
- Use `--pdb` flag for interactive debugging
- Verify test environment configuration
- Check for external service dependencies

## Coverage Reporting

Current coverage targets:
- Overall: > 80%
- API Endpoints: > 90%
- Core Services: > 85%
- Authentication: > 95%

Coverage reports available in:
- Terminal: Real-time coverage summary
- HTML: `htmlcov/index.html`
- XML: `coverage.xml` for CI integration
EOF < /dev/null