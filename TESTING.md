# Testing Guide

## Overview

This document outlines the comprehensive testing strategy for the Student-Employer Matching Platform. 

## Testing Philosophy

We follow a three-tier testing strategy:

1. **Unit Tests** (Primary Focus) - Fast, isolated tests for individual components
2. **Integration Tests** (Secondary Focus) - Tests for component interaction and API endpoints  
3. **UI Tests** - End-to-end browser testing for user flows

## Test Architecture

### Test Structure

```
├── core/
│   ├── tests.py           # Model and business logic tests
│   └── factories.py       # Test data factories
├── api/
│   └── tests.py           # API integration tests
├── utils/
│   └── tests.py           # Monitoring and utility tests
└── web/
    └── tests.py           # Web view tests 
```

### Test Database Configuration

Tests use an optimized configuration for speed:
- **In-memory SQLite** for fast test execution
- **Simplified password hashing** (MD5) for test users
- **Disabled migrations** for faster database setup
- **Local cache backend** instead of Redis/Memcached

## Running Tests

### Basic Test Commands

```bash
# Run all tests
uv run python manage.py test

# Run tests with verbose output
uv run python manage.py test --verbosity=2

# Run specific app tests
uv run python manage.py test core
uv run python manage.py test api
uv run python manage.py test utils

# Run specific test class
uv run python manage.py test core.tests.ProjectMatcherTest

# Run specific test method
uv run python manage.py test core.tests.ProjectMatcherTest.test_find_matches_basic
```

### Using Pytest (Alternative)

```bash
# Install pytest dependencies first
uv sync

# Run all tests with pytest
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest core/tests.py

# Run tests matching pattern
uv run pytest -k "test_matching"

# Skip slow tests
uv run pytest -m "not slow"
```

### Coverage Reporting

```bash
# Generate HTML coverage report
uv run coverage run --source='.' manage.py test
uv run coverage html

# View coverage report
open htmlcov/index.html

# Generate terminal coverage report
uv run coverage report --show-missing

# Target coverage: 85%+ for core business logic
```

## Test Categories

### 1. Unit Tests

**Location**: `core/tests.py`

**Focus Areas**:
- Model validation and business logic
- Custom model methods and properties
- Matching algorithm components
- Data transformation utilities
- Error handling and edge cases

**Key Test Classes**:
```python
# Model Tests
- UserModelTest              # User authentication and validation
- StudentProfileModelTest    # Student profile functionality
- EmployerProfileModelTest   # Employer profile functionality
- ProjectModelTest          # Project model behavior
- SkillModelTest            # Skill model and relationships

# Business Logic Tests  
- ProjectMatcherTest        # Core matching algorithm
- ProjectMatchingIntegrationTest  # End-to-end matching
```

**Example Test Pattern**:
```python
class StudentProfileModelTest(TestCase):
    """Test StudentProfile model behavior"""

    def setUp(self) -> None:
        """Create test data with factories"""
        self.user = StudentUserFactory()
        self.profile = StudentProfileFactory(user=self.user)

    def test_profile_completeness(self) -> None:
        """Test profile completion calculation"""
        # Test logic here
        self.assertTrue(self.profile.profile_complete)
```

### 2. Integration Tests

**Location**: `api/tests.py`

**Status**: ⚠️ Currently skipped - API endpoints not implemented yet

**Planned Focus Areas**:
- API endpoint functionality
- Authentication and authorization
- Request/response validation
- Database integration
- Caching behavior
- Error handling

**Key Test Classes** (Currently Skipped):
```python
- APITestCase              # Base test class with common setup
- StudentAPITest           # Student-related endpoints (SKIPPED)
- EmployerAPITest          # Employer-related endpoints (SKIPPED)
- MatchingAPITest          # Matching system endpoints (SKIPPED)
- SkillsAPITest           # Skills management endpoints (SKIPPED)
- APISecurityTest         # Security and auth testing (SKIPPED)
```

**Note**: These tests serve as specifications for the future API implementation. Remove the `@unittest.skip()` decorators when ready to implement the API endpoints.

**Example Integration Test**:
```python
class EmployerAPITest(APITestCase):
    """Test employer-related API endpoints"""

    def test_project_creation(self) -> None:
        """Test creating project via API"""
        self.login_employer()
        
        data = {'title': 'New Project', 'description': 'Test project'}
        response = self.client.post('/api/projects/', data)
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Project.objects.filter(title='New Project').exists())
```

### 3. Future Utility Tests

**Note**: Utility monitoring components have been removed for now but may be added back later if needed.

## Test Data Management

### Factory Boy Usage

We use Factory Boy for creating consistent, realistic test data:

```python
# Create a basic student
student = StudentProfileFactory()

# Create a complete student with relationships
student = CompleteStudentProfileFactory()

# Create with specific attributes
student = StudentProfileFactory(
    academic_year="senior",
    currently_available="yes"
)

# Create perfect matching scenario
student, project = MatchingScenarioFactory.create_perfect_match()
```

### Factory Features
- **Realistic data** using Faker library
- **Relationship handling** for foreign keys and many-to-many fields
- **Scenario factories** for common test patterns
- **Trait system** for variations (e.g., CompleteStudentProfileFactory)

### Test Data Best Practices

1. **Use factories instead of fixtures** for flexibility
2. **Create data in setUp()** for test isolation
3. **Use specific factories** for targeted testing
4. **Clean up relationships** to avoid cascade issues

## Test Quality Guidelines

### Code Coverage Targets

- **Core business logic**: 90%+ coverage
- **API endpoints**: 85%+ coverage  
- **Models**: 80%+ coverage
- **Overall project**: 85%+ coverage

### Test Organization

1. **One test class per model/component**
2. **Descriptive test names** (`test_student_profile_validation_with_invalid_email`)
3. **Arrange-Act-Assert pattern** in test methods
4. **setUp() and tearDown()** for common test data
5. **Mock external dependencies** (APIs, email, file systems)

### Writing Effective Tests

```python
def test_project_matching_with_skills(self) -> None:
    """Test that projects match students based on required skills"""
    # Arrange
    python_skill = SkillFactory(name="Python")
    student = StudentProfileFactory(skills=[python_skill])
    project = ProjectFactory(required_skills_text="Python, Django")
    
    # Act
    matches = ProjectMatcher().find_matches(project, limit=10)
    
    # Assert
    self.assertEqual(len(matches), 1)
    matched_student, match_data = matches[0]
    self.assertEqual(matched_student.id, student.id)
    self.assertGreater(match_data['skills_match'], 50)
```

## Performance Testing

### Test Performance Targets

- **Individual tests**: < 100ms (excluding slow tests)
- **Full test suite**: < 60 seconds
- **Memory usage**: < 500MB during test run

### Optimizations Applied

1. **In-memory database** for speed
2. **Disabled migrations** during testing
3. **Simplified password hashing** for test users
4. **Local cache backend** instead of external cache
5. **Minimal logging** during tests

### Slow Test Management

Mark computationally expensive tests:

```python
import pytest

@pytest.mark.slow
def test_large_dataset_processing(self) -> None:
    """Test processing of large datasets"""
    # Expensive test logic here
    pass
```

Run without slow tests:
```bash
uv run pytest -m "not slow"
```

## Debugging Failed Tests

### Common Issues and Solutions

1. **Test Database Issues**
   ```bash
   # Clear test database
   uv run python manage.py flush --verbosity=0 --noinput
   
   # Reset migrations (if needed)
   uv run python manage.py migrate --run-syncdb
   ```

2. **Factory Relationship Issues**
   - Ensure foreign key relationships are properly defined
   - Use `SubFactory` for related objects
   - Check for circular dependencies

3. **Cache-related Test Failures**
   ```python
   def setUp(self) -> None:
       cache.clear()  # Clear cache between tests
   ```

4. **Authentication Issues in API Tests**
   ```python
   def setUp(self) -> None:
       self.client.force_login(self.test_user)  # Force authentication
   ```

### Debug Techniques

1. **Verbose test output**: `--verbosity=2`
2. **Print debugging**: Use `print()` statements (remove before commit)
3. **PDB debugging**: `import pdb; pdb.set_trace()`
4. **Database inspection**: Check actual vs expected data
5. **Logging**: Enable specific loggers during debugging

## Continuous Integration

### Pre-commit Quality Checks

```bash
# Full quality gate (run before commits)
uv run ruff check --fix && uv run ruff format && uv run mypy . && uv run python manage.py test
```

### GitHub Actions (Future)

Recommended CI pipeline:
1. **Lint check** (ruff)
2. **Type check** (mypy)
3. **Unit tests** with coverage
4. **Integration tests**
5. **Security checks** (bandit, safety)
6. **Performance regression tests**

## Test Maintenance

### Regular Tasks

1. **Update factories** when models change
2. **Review test coverage** monthly
3. **Remove obsolete tests** for deprecated features
4. **Update test data** to reflect realistic scenarios
5. **Performance profiling** of slow tests

### Adding New Tests

When adding features:
1. **Write tests first** (TDD approach when possible)
2. **Test both happy path and edge cases**
3. **Include error condition testing**
4. **Add integration tests for new API endpoints**
5. **Update this documentation** with new test patterns

## Test Anti-patterns to Avoid

1. **Testing implementation details** instead of behavior
2. **Overly complex test setup** (use factories)
3. **Tests that depend on external services** (use mocks)
4. **Tests that modify global state** without cleanup
5. **Flaky tests** that pass/fail randomly
6. **Tests without assertions** (smoke tests should still verify something)
7. **Duplicate test logic** (use helper methods)

## Future Testing Enhancements

### Planned Improvements

1. **UI Testing Framework** (Playwright/Selenium)
   - Critical user flow testing
   - Cross-browser compatibility
   - Accessibility testing

2. **Load Testing** (Locust)
   - API endpoint performance
   - Database query optimization
   - Caching effectiveness

3. **Property-based Testing** (Hypothesis)
   - Edge case discovery
   - Input validation robustness
   - Algorithm correctness verification

4. **Contract Testing** (Pact)
   - API consumer/provider contracts
   - Frontend/backend integration
   - Third-party service integration

5. **Visual Regression Testing**
   - UI component consistency
   - Layout stability across changes
   - Responsive design validation

## Resources and References

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Pytest Django Plugin](https://pytest-django.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Test-Driven Development Best Practices](https://testdriven.io/blog/modern-tdd/)

## Getting Help

For testing questions or issues:
1. Check this documentation first
2. Review existing test patterns in the codebase
3. Consult Django testing documentation
4. Ask team members for guidance on complex scenarios
5. Create GitHub issues for test infrastructure problems

---

**Remember**: Good tests are investments in code quality, developer confidence, and long-term maintainability. Write tests that you and your teammates will thank you for later.