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
│   ├── views.py         # API views
│   ├── urls.py          # API URL patterns
│   └── apps.py          # API app configuration
├── web/                 # Web interface
│   ├── views.py         # Web views
│   ├── urls.py          # Web URL patterns
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JavaScript, images
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

This project uses **Ruff** for code linting and formatting. All code should pass ruff checks before committing.

#### Running Ruff
```bash
# Check for linting issues
uv run ruff check

# Auto-fix issues (when safe)
uv run ruff check --fix

# Format code
uv run ruff format
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

*   **Unit Tests:**  Use Django's testing framework to write unit tests for individual components.
*   **Integration Tests:**  Write integration tests to verify the interaction between different parts of the application.
*   **Test Coverage:**  Aim for at least 80% test coverage.
*   **Running Tests:** `python manage.py test`

### 8. Deployment

*(This section will be populated as the deployment process is finalized)*

### 9. Useful Resources

*   **Django Documentation:** [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
*   **Bootstrap Documentation:** [https://getbootstrap.com/](https://getbootstrap.com/)
*   **htmx Documentation:** [https://htmx.org/](https://htmx.org/)
*   **PostgreSQL Documentation:** [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

### 10. Contact

For questions or assistance, please contact open an issue on GitHub.