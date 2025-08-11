# Talent Opportunity Hub - Developer Guide

Welcome to the Talent Opportunity Hub development team! This document provides instructions and guidelines for contributing to the project.  Please read this guide carefully before submitting any code.

## Table of Contents

1.  [Introduction](#introduction)
2.  [Project Overview](#project-overview)
3.  [Development Environment Setup](#development-environment-setup)
4.  [Coding Style Guide](#coding-style-guide)
5.  [Code Quality & Linting](#code-quality--linting)
6.  [Workflow](#workflow)
7.  [Testing](#testing)
8.  [Deployment](#deployment)
9.  [Useful Resources](#useful-resources)
10. [Contact](#contact)

---

### 1. Introduction

This guide aims to help developers quickly set up their environment, understand the project structure, and contribute effectively. We value clear, maintainable code and a collaborative development process.

### 2. Project Overview

The Talent Opportunity Hub is a Django application designed to connect students with academic/industry projects, internships, and career opportunities.  

*   **Tech Stack:**
    *   Python 3.12+ 
    *   Django 5.2+ 
    *   Bootstrap 5
    *   htmx.org 2.0+
    *   PostgreSQL 
    *   Git
*   **Key Features (planned/in progress):** 
    *   User Authentication (Students, Employers, Admins)
    *   Opportunity Posting & Management
    *   Search and Filtering of Opportunities
    *   Application Tracking
    *   User Profiles
*   **Structure:**

The project follows a separation of concerns with the following organization:

```
├── config/              # Django configuration
│   ├── settings.py      # Django settings
│   ├── urls.py          # Root URL configuration
│   ├── wsgi.py          # WSGI application
│   └── asgi.py          # ASGI application
├── core/                # Business logic & models
│   ├── models.py        # Database models
│   ├── matching.py      # AI matching algorithms
│   ├── admin.py         # Django admin configuration
│   └── management/      # Custom Django commands
├── api/                 # REST API endpoints
│   ├── views.py         # API views with defensive programming
│   ├── urls.py          # API URL patterns
│   └── apps.py          # API app configuration
├── web/                 # Web interface
│   ├── views.py         # Web views
│   ├── urls.py          # Web URL patterns
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JavaScript, images
├── utils/               # Django app for future utilities (currently empty)
│   ├── apps.py          # Utils app configuration
│   └── __init__.py      # App initialization
├── media/               # User uploaded files
└── doc/                 # Documentation
```


### 3. Development Environment Setup

**Prerequisites:**

*   Python 3.12 or later
*   Git
*   PostgreSQL (or sqlite for development)

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/talent-opportunity-hub.git
    cd talent-opportunity-hub
    ```

2.  **Install uv:**

    **Linux/macOS:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    **Windows (PowerShell):**
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    **Alternative methods:**
    ```bash
    # Via pip
    pip install uv

    # Via Homebrew (macOS)
    brew install uv

    # Via Cargo
    cargo install uv
    ```

    **Verify installation:**
    ```bash
    uv --version
    ```

3.  **Install Dependencies and Activate Environment:**
    ```bash
    # uv will automatically create and use a virtual environment
    uv sync

    # Activate the virtual environment 
    source .venv/bin/activate  # On Linux/macOS
    .venv\Scripts\activate     # On Windows
    ```

4.  **Configure Database:**
    *   Run migrations: `python manage.py migrate`

5.  **Run the Development Server:**
    ```bash
    python manage.py runserver
    ```
    Visit `http://127.0.0.1:8000/` in your browser.

### 4. Coding Style Guide

We follow the [PEP 8](https://peps.python.org/pep-08/) style guide for Python code.  In addition:

*   **Django Style Guide:**  Adhere to the official Django style guide: [https://docs.djangoproject.com/en/dev/contributing/code-style/](https://docs.djangoproject.com/en/dev/contributing/code-style/)
*   **HTML/CSS/JavaScript:**  Follow Bootstrap 5 conventions.  Keep HTML clean and well-formatted.  Use descriptive class names.
*   **htmx:** Leverage htmx for dynamic content updates.  Keep htmx attributes concise and readable.  Focus on enhancing user experience without overcomplicating the frontend.
*   **Commit Messages:** Use clear and concise commit messages.  Follow the format: `feat: Add new feature` or `fix: Resolve bug`.  See [https://www.conventionalcommits.org/en/v1.0.0/](https://www.conventionalcommits.org/en/v1.0.0/) for more details.

### 5. Code Quality & Linting

This project uses **Ruff** for code linting and formatting, plus **mypy** for static type checking. All code should pass both ruff and mypy checks before committing.

#### Project Type Safety Status

This project uses comprehensive type hints with modern Python 3.12+ syntax across all major modules:
- Core business logic (`core/`) - Modern generic syntax and type annotations
- Web views and API endpoints (`web/`, `api/`) - Defensive programming patterns
- Database models and admin (`core/models.py`, `core/admin.py`) - Django model typing
- Matching algorithms (`core/matching.py`) - Advanced generic functions and caching

The codebase leverages Python 3.12's advanced type system including:
- Generic function syntax `def func[T](...)`
- Modern `collections.abc.Callable` usage with proper parameter lists
- `ParamSpec` for decorator type safety
- Type parameter syntax for classes and functions

This provides superior IDE support, runtime error prevention, and clear code documentation through types.

#### Running Ruff
```bash
# Check for linting issues
uv run ruff check

# Auto-fix issues (when safe)
uv run ruff check --fix

# Format code
uv run ruff format

# Check type annotations specifically
uv run ruff check --select ANN

# Check specific file for type annotations
uv run ruff check web/views.py --select ANN
```

#### Running MyPy
```bash
# Run type checking on entire project
uv run mypy .

# Check specific module
uv run mypy core/
uv run mypy web/views.py

# Run with verbose output for debugging
uv run mypy --verbose .

# Check with error codes for specific fixes
uv run mypy --show-error-codes .

# Run strict checking (recommended for new code)
uv run mypy --strict core/matching.py
```

#### Pre-commit Quality Checks

Before committing code, always run the complete quality check suite:

```bash
# Complete quality check workflow
uv run ruff check --fix        # Auto-fix linting issues
uv run ruff format            # Format code
uv run mypy .                 # Validate types
uv run python manage.py test  # Run tests

# One-line quality gate
uv run ruff check --fix && uv run ruff format && uv run mypy . && uv run python manage.py test
```

#### CI/CD Integration

The project is configured to run these checks automatically:
- Ruff linting and formatting validation
- MyPy type checking with strict settings
- Test suite execution
- Django system checks

#### Type Hints Guidelines

This project has **comprehensive type hint coverage** and requires type hints for all new code. Type hints improve code documentation, IDE support, and catch potential runtime errors during development.

##### Type Hint Requirements

**Standards for New Code:**
- **All functions must have type hints** - Parameters and return types (enforced by ruff ANN rules)
- **Django views must be properly typed** - HttpRequest → HttpResponse/JsonResponse patterns
- **Complex data structures must specify types** - Use modern syntax (dict, list, tuple)  
- **API endpoints must have clear types** - Request/response typing for API documentation
- **Database operations must be typed** - QuerySet and model instance types

**Quality Gate**: All code must pass mypy validation before merging.

##### Modern Python Type Syntax (Python 3.12+)
Use modern built-in types and Python 3.12's advanced generic syntax:

```python
from typing import Any, ParamSpec  # Still needed for certain types
from collections.abc import Callable  # Use collections.abc for Callable
from datetime import date, datetime

# ✅ MODERN PYTHON 3.12 (Use this)
def process_items(data: dict[str, Any]) -> list[tuple[str, int]]:
    pass

def get_users() -> list[User]:
    pass

# ✅ MODERN GENERIC FUNCTIONS (Python 3.12+)
def create_decorator[T](func: Callable[..., T]) -> Callable[..., T]:
    pass

# ✅ PROPER CALLABLE SYNTAX (Python 3.12+)
P = ParamSpec('P')

def monitor_function[T](
    log_threshold: float = 1.0
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ❌ LEGACY (Don't use for new code)
from typing import Dict, List, Tuple, Callable as TypingCallable
def process_items(data: Dict[str, Any]) -> List[Tuple[str, int]]:
    pass
```

##### Django-Specific Type Patterns
```python
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import QuerySet
from django.contrib.auth.models import User
from typing import Any, cast

# View functions
def student_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, 'template.html')

def api_endpoint(request: HttpRequest) -> JsonResponse:
    data: dict[str, Any] = {"status": "success"}
    return JsonResponse(data)

# Handling Django User authentication typing
def my_view(request: HttpRequest) -> HttpResponse:
    # Use cast to handle User vs AnonymousUser typing
    auth_user = cast(User, request.user)
    if request.user.is_authenticated:
        # Now can safely access user attributes
        profile = auth_user.student_profile

# QuerySet typing
def get_active_students() -> QuerySet[StudentProfile]:
    return StudentProfile.objects.filter(profile_complete=True)

# Model methods
class StudentProfile(models.Model):
    def __str__(self) -> str:
        return f"{self.user.get_full_name()}"
        
    def clean(self) -> None:
        # Model validation method
        super().clean()
```

##### Date Field Handling
Django DateField requires proper date objects, not strings:

```python
from datetime import date, datetime

def parse_date_string(date_str: str | None) -> date | None:
    """Parse date string and return date object, None if invalid"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

def parse_required_date_string(date_str: str | None) -> date:
    """Parse date string, return today as fallback for required fields"""
    parsed_date = parse_date_string(date_str)
    return parsed_date if parsed_date else date.today()
```

##### Common Type Patterns in This Project (Python 3.12+)
```python
# Matching algorithm types with modern syntax
def find_matches(self, project: Project, limit: int = 20) -> list[tuple[StudentProfile, dict[str, Any]]]:
    pass

# Modern decorator patterns with ParamSpec (example)
from typing import ParamSpec
from collections.abc import Callable

P = ParamSpec('P')

def log_calls[T](
    level: str = 'INFO'
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # logging logic here
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage - note the parentheses for parameterized decorators
@log_calls()
def some_function(data: str) -> int:
    return len(data)

# Complex data processing with proper Callable syntax
def create_processor() -> Callable[[dict[str, Any]], list[dict[str, Any]]]:
    pass

# Union types for flexible returns
def format_trend_data(queryset: QuerySet) -> list[dict[str, str | int]]:
    pass
```

##### Type Ignore Comments
When mypy produces false positives, use specific type ignore comments:

```python
# Django model relationships that mypy can't validate
profile = request.user.student_profile  # type: ignore[union-attr]

# Complex Django QuerySet operations
profile.education.all().delete()  # type: ignore[misc]

# Third-party library compatibility
font = ImageFont.load_default()  # type: ignore[assignment]
```

##### Best Practices
- ✅ **Use modern type syntax** (dict, list, tuple instead of Dict, List, Tuple)
- ✅ **Be specific with types** (`dict[str, int]` instead of `dict`)
- ✅ **Use union syntax** (`str | None` instead of `Optional[str]`)
- ✅ **Type all function parameters and returns**
- ✅ **Use `cast()` for Django User authentication patterns**
- ✅ **Add type ignore comments with specific error codes**
- ❌ **Don't use `Any` unless truly necessary**
- ❌ **Don't suppress all mypy errors with broad ignores**

##### Troubleshooting Common Type Issues

**Django User Authentication Typing:**
```python
# Problem: request.user can be User or AnonymousUser
def my_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        name = request.user.first_name  # mypy error!

# Solution: Use cast() after authentication check
from typing import cast
def my_view(request: HttpRequest) -> HttpResponse:
    auth_user = cast(User, request.user)
    if request.user.is_authenticated:
        name = auth_user.first_name  # Works!
```

**Date Field Parsing:**
```python
# Problem: Django DateField expects date object, not string
start_date = request.POST.get('start_date') or None  # mypy error!

# Solution: Parse date strings properly
start_date = parse_required_date_string(request.POST.get('start_date'))
```

**QuerySet Operations:**
```python
# Problem: Django QuerySet delete() method typing
profile.education.all().delete()  # mypy error!

# Solution: Add type ignore for legitimate Django patterns
profile.education.all().delete()  # type: ignore[misc]
```

**Complex Return Types:**
```python
# Problem: Complex nested data structures
def get_matches() -> ???  # What type?

# Solution: Be specific about the structure
def get_matches() -> list[tuple[StudentProfile, dict[str, Any]]]:
    return [(student, {"score": 85, "skills": ["Python"]}) for student in students]
```

#### Suppressing Ruff Warnings with `# noqa`

Sometimes legitimate code patterns trigger ruff warnings that should be ignored. Use `# noqa` comments to suppress specific warnings:

##### When to Use `# noqa`
- **Intentional code patterns** that ruff flags as problematic
- **Django-specific patterns** that don't follow general Python conventions
- **Utility scripts** with different coding standards
- **Third-party compatibility** requirements

##### Syntax
```python
# Suppress specific error codes
problematic_line()  # noqa: E722

# Suppress multiple error codes
another_line()  # noqa: F401, E722

# Suppress all warnings on a line (use sparingly)
complex_line()  # noqa
```

##### Best Practices for `# noqa`
- ✅ **Always include the specific error code** (e.g., `# noqa: F401`)
- ✅ **Add a comment explaining why** the suppression is needed
- ✅ **Use sparingly** - fix the underlying issue when possible
- ✅ **Review regularly** - remove suppressions when no longer needed
- ❌ **Don't use `# noqa` without error codes** (suppresses all warnings)
- ❌ **Don't suppress warnings** just to avoid fixing code

### 6. Workflow

1.  **Create a Branch:**  For each new feature or bug fix, create a new branch from `main`.  Use a descriptive branch name (e.g., `feat/add-search-functionality`, `fix/broken-login`).
2.  **Write Code and Tests:** Implement the changes and write corresponding unit/integration tests.
3.  **Commit Changes:**  Commit your changes with clear and concise messages.
4.  **Push to Repository:** Push your branch to the remote repository.
5.  **Create a Pull Request:**  Open a pull request targeting the `main` branch.
6.  **Code Review:**  Your pull request will be reviewed by other developers.  Address any feedback.
7.  **Merge:**  Once approved, your pull request will be merged into `main`.

### 7. Testing

This project follows a three-tier testing strategy with strong emphasis on unit and integration testing. See [TESTING.md](TESTING.md) for complete testing guidelines.

**Quick Start:**
```bash
# Run all tests
uv run python manage.py test

# Run with coverage
uv run coverage run --source='.' manage.py test
uv run coverage html
open htmlcov/index.html

# Run specific test categories
uv run python manage.py test core     # Unit tests
uv run python manage.py test api      # Integration tests (currently skipped)
uv run python manage.py test web      # Web interface tests
```

**Test Structure:**
- **Unit Tests** (`core/tests.py`): Models, business logic, matching algorithms
- **Integration Tests** (`api/tests.py`): API endpoints, authentication, caching (currently skipped)
- **Test Factories** (`core/factories.py`): Realistic test data creation

**Coverage Targets:**
- Core business logic: 90%+
- API endpoints: 85%+  
- Overall project: 85%+

**Key Features:**
- Factory Boy for test data generation
- In-memory database for fast test execution
- Security and authentication testing (planned)
- Comprehensive error condition coverage
- AI matching algorithm validation

### 8. Deployment

*(This section will be populated as the deployment process is finalized)*

### 9. Common Commands

```bash
# Development
uv run python manage.py runserver
uv run python manage.py shell
uv run python manage.py dbshell

# Database
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py populate_demo_data

# Testing & Quality
uv run python manage.py test
uv run ruff check
uv run ruff format
uv run mypy .

# Type Checking Workflow
uv run ruff check --select ANN  # Check missing type hints
uv run mypy core/               # Check core module types
uv run mypy web/views.py        # Check specific view file
uv run mypy --strict core/      # Strict type checking
uv run mypy --show-error-codes  # Show specific error codes for fixes

# Comprehensive Quality Check (run before commits)
uv run ruff check --fix && uv run ruff format && uv run mypy . && uv run python manage.py test

# Production
uv run python manage.py collectstatic
uv run python manage.py check --deploy
```

### 10. Useful Resources

*   **Django Documentation:** [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
*   **Bootstrap Documentation:** [https://getbootstrap.com/](https://getbootstrap.com/)
*   **htmx Documentation:** [https://htmx.org/](https://htmx.org/)
*   **PostgreSQL Documentation:** [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
*   **Python Type Hints:** [https://docs.python.org/3/library/typing.html](https://docs.python.org/3/library/typing.html)
*   **MyPy Documentation:** [https://mypy.readthedocs.io/](https://mypy.readthedocs.io/)
*   **Ruff Rules:** [https://docs.astral.sh/ruff/rules/](https://docs.astral.sh/ruff/rules/)

### 11. Contact

For questions or assistance, please contact open an issue on GitHub.