# QA Test Suite - Internship Hub API

This folder contains all Quality Assurance tests for the Internship Hub API.

## Test Structure

### Authentication Tests (`test_auth.py`)
- User registration tests
- Login/logout functionality tests  
- Token refresh tests
- Password reset flow tests
- Authorization tests

### API Tests (`test_api.py`) 
- Endpoint response tests
- Data validation tests
- Error handling tests
- Performance tests

### Database Tests (`test_database.py`)
- Model creation/validation tests
- Database connection tests
- Data integrity tests
- Migration tests

### Integration Tests (`test_integration.py`)
- End-to-end user flows
- Cross-module integration
- External service integration

## Running Tests

```bash
# Run all tests
python -m pytest QA/

# Run specific test file
python -m pytest QA/test_auth.py

# Run with coverage
python -m pytest QA/ --cov=.

# Run with verbose output
python -m pytest QA/ -v
```

## Test Configuration

Tests use:
- **pytest** for test framework
- **httpx** for async HTTP client testing
- **pytest-asyncio** for async test support
- **factory_boy** for test data generation

## Environment

Tests should use a separate test database and test environment configurations.