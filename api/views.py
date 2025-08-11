import json
import logging
from collections.abc import Callable
from typing import Any

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


class APIValidationError(Exception):
    """Custom exception for API input validation errors"""

    pass


def validate_required_fields(data: dict, required_fields: list[str]) -> None:
    """Validate that all required fields are present and not empty"""
    missing_fields = []
    empty_fields = []

    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field] or (
            isinstance(data[field], str) and not data[field].strip()
        ):
            empty_fields.append(field)

    if missing_fields:
        raise APIValidationError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )
    if empty_fields:
        raise APIValidationError(f"Empty required fields: {', '.join(empty_fields)}")


def sanitize_string_field(value: object, max_length: int = 255) -> str:
    """Sanitize and validate string input"""
    if not isinstance(value, str):
        value = str(value)

    # Strip whitespace and limit length
    sanitized = value.strip()[:max_length]

    # Basic XSS prevention - remove common dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&"]
    for char in dangerous_chars:
        if char in sanitized:
            logger.warning(
                f"Potentially dangerous character '{char}' found in input, sanitizing"
            )
            sanitized = sanitized.replace(char, "")

    return sanitized


def validate_email(email: str) -> str:
    """Validate and sanitize email address"""
    if not email or not isinstance(email, str):
        raise APIValidationError("Invalid email format")

    email = email.strip().lower()

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[1]:
        raise APIValidationError("Invalid email format")

    if len(email) > 254:  # RFC 5321 limit
        raise APIValidationError("Email address too long")

    return email


def validate_url(url: str) -> str:
    """Validate and sanitize URL"""
    if not url or not isinstance(url, str):
        raise APIValidationError("Invalid URL format")

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        raise APIValidationError("URL must start with http:// or https://")

    if len(url) > 2000:  # Reasonable URL length limit
        raise APIValidationError("URL too long")

    return url


def handle_api_error(func: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    """Decorator to handle common API errors consistently"""

    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        try:
            return func(request, *args, **kwargs)
        except APIValidationError as e:
            logger.warning(f"API validation error in {func.__name__}: {e}")
            return JsonResponse({"error": str(e), "success": False}, status=400)
        except ValidationError as e:
            logger.warning(f"Django validation error in {func.__name__}: {e}")
            return JsonResponse(
                {"error": "Invalid data provided", "success": False}, status=400
            )
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {e}")
            return JsonResponse(
                {
                    "error": "Data conflict - resource may already exist",
                    "success": False,
                },
                status=409,
            )
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error in {func.__name__}: {e}")
            return JsonResponse(
                {"error": "Invalid JSON format", "success": False}, status=400
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return JsonResponse(
                {"error": "Internal server error", "success": False}, status=500
            )

    return wrapper


@csrf_exempt
@require_http_methods(["POST"])
@handle_api_error
def create_user(request: HttpRequest) -> JsonResponse:
    """Create a new user with comprehensive validation"""
    # Parse and validate JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        raise APIValidationError("Invalid JSON format") from e

    # Validate required fields
    required_fields = ["username", "email", "password"]
    validate_required_fields(data, required_fields)

    # Sanitize and validate inputs
    username = sanitize_string_field(data["username"], max_length=150)
    validate_email(data["email"])  # Validate but don't store
    password = data["password"]  # Don't sanitize passwords
    user_type = data.get("user_type", "student")

    # Validate username length and format
    if len(username) < 3:
        raise APIValidationError("Username must be at least 3 characters long")

    # Validate password strength
    if len(password) < 8:
        raise APIValidationError("Password must be at least 8 characters long")

    # Validate user type
    valid_user_types = ["student", "employer", "admin"]
    if user_type not in valid_user_types:
        raise APIValidationError(
            f"Invalid user type. Must be one of: {', '.join(valid_user_types)}"
        )

    logger.info(f"Creating new user: {username} ({user_type})")

    return JsonResponse(
        {
            "status": "success",
            "message": "User created successfully",
            "username": username,
            "user_type": user_type,
            "success": True,
        }
    )


@csrf_exempt
@require_http_methods(["POST", "PUT"])
@handle_api_error
def update_profile(request: HttpRequest, user_id: int) -> JsonResponse:
    """Update user profile with validation and sanitization"""
    # Validate user_id parameter
    if not isinstance(user_id, int) or user_id <= 0:
        raise APIValidationError("Invalid user ID")

    # Parse and validate JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        raise APIValidationError("Invalid JSON format") from e

    if not isinstance(data, dict):
        raise APIValidationError("Request data must be a JSON object")

    # Define allowed fields to prevent unauthorized updates
    allowed_fields = {
        "program",
        "academic_year",
        "graduation_date",
        "university",
        "location",
        "bio",
        "linkedin_url",
        "portfolio_url",
        "website",
        "company_name",
        "contact_name",
        "industry",
        "company_size",
    }

    sanitized_data = {}

    for field, value in data.items():
        if field not in allowed_fields:
            logger.warning(
                f"Attempt to update unauthorized field '{field}' for user {user_id}"
            )
            continue

        # Sanitize string fields
        if isinstance(value, str):
            if field in ["linkedin_url", "portfolio_url", "website"] and value:
                # URL validation
                try:
                    sanitized_data[field] = validate_url(value)
                except APIValidationError as e:
                    logger.warning(f"Invalid URL for field {field}: {e}")
                    continue
            else:
                sanitized_data[field] = sanitize_string_field(value, max_length=500)
        else:
            sanitized_data[field] = value

    logger.info(
        f"Profile update for user {user_id} with fields: {list(sanitized_data.keys())}"
    )

    return JsonResponse(
        {
            "status": "success",
            "message": f"Profile updated for user {user_id}",
            "updated_fields": list(sanitized_data.keys()),
            "success": True,
        }
    )


@csrf_exempt
def verify_auth(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "success", "verified": True})


@csrf_exempt
@require_http_methods(["POST", "PUT"])
@handle_api_error
def update_skills(request: HttpRequest, user_id: int) -> JsonResponse:
    """Update user skills with validation"""
    # Validate user_id parameter
    if not isinstance(user_id, int) or user_id <= 0:
        raise APIValidationError("Invalid user ID")

    # Parse and validate JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        raise APIValidationError("Invalid JSON format") from e

    skills_data = data.get("skills", [])
    if not isinstance(skills_data, list):
        raise APIValidationError("Skills must be provided as a list")

    if len(skills_data) > 50:  # Reasonable limit
        raise APIValidationError("Too many skills provided (max 50)")

    # Validate and sanitize each skill
    validated_skills = []
    valid_levels = ["beginner", "intermediate", "advanced", "expert"]

    for skill in skills_data:
        if not isinstance(skill, dict):
            logger.warning(f"Invalid skill format for user {user_id}, skipping")
            continue

        skill_name = sanitize_string_field(skill.get("name", ""), max_length=100)
        skill_level = skill.get("level", "beginner")
        skill_description = sanitize_string_field(
            skill.get("description", ""), max_length=500
        )

        if not skill_name:
            logger.warning(f"Empty skill name for user {user_id}, skipping")
            continue

        if skill_level not in valid_levels:
            logger.warning(
                f"Invalid skill level '{skill_level}' for user {user_id}, using 'beginner'"
            )
            skill_level = "beginner"

        validated_skills.append(
            {"name": skill_name, "level": skill_level, "description": skill_description}
        )

    logger.info(f"Skills updated for user {user_id}: {len(validated_skills)} skills")

    return JsonResponse(
        {
            "status": "success",
            "message": f"Skills updated for user {user_id}",
            "skills_count": len(validated_skills),
            "success": True,
        }
    )


@csrf_exempt
def get_matches(request: HttpRequest, project_id: int) -> JsonResponse:
    return JsonResponse({"matches": [], "count": 0})


@csrf_exempt
def semantic_match(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"matches": [], "similarity_scores": []})


@csrf_exempt
def match_evidence(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"evidence": "Mock matching evidence"})


@csrf_exempt
def parse_document(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "success", "parsed_data": {}})


@csrf_exempt
def store_document(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "success", "document_id": "mock_doc_123"})


@csrf_exempt
def highlight_document(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"highlights": []})


@csrf_exempt
def analyze_employer(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"analysis": "Mock employer analysis"})


@csrf_exempt
def analyze_project(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"analysis": "Mock project analysis"})


@csrf_exempt
def generate_questions(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"questions": ["Mock question 1", "Mock question 2"]})


@csrf_exempt
@require_http_methods(["POST"])
@handle_api_error
def validate_responses(request: HttpRequest) -> JsonResponse:
    """Validate user input with AI assistance"""
    # Parse form data or JSON
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            field_name = data.get("field_name", "")
            field_value = data.get("field_value", "")
        except json.JSONDecodeError as e:
            raise APIValidationError("Invalid JSON format") from e
    else:
        field_name = request.POST.get("field_name", "")
        field_value = request.POST.get("field_value", "")

    # Validate required fields
    if not field_name or not field_value:
        raise APIValidationError("Both field_name and field_value are required")

    # Rate limiting could be implemented here
    logger.info(
        f"Validation request for field: {field_name[:50]}..."
    )  # Log truncated field name

    try:
        validation_result = get_ai_validation(field_name, field_value)
        return JsonResponse({"validation": validation_result, "success": True})
    except Exception as e:
        logger.error(f"Error in AI validation: {e}")
        # Return safe fallback instead of error
        return JsonResponse(
            {"validation": {"status": "valid", "suggestions": []}, "success": True}
        )


@csrf_exempt
@require_http_methods(["POST"])
@handle_api_error
def scan_webpage(request: HttpRequest) -> JsonResponse:
    """Simulate webpage scanning and data extraction with validation"""
    # Parse form data or JSON
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            webpage_url = data.get("webpage_url", "")
            scan_type = data.get("scan_type", "employer")
        except json.JSONDecodeError as e:
            raise APIValidationError("Invalid JSON format") from e
    else:
        webpage_url = request.POST.get("webpage_url", "")
        scan_type = request.POST.get("scan_type", "employer")

    # Validate inputs
    if not webpage_url:
        raise APIValidationError("webpage_url is required")

    try:
        webpage_url = validate_url(webpage_url)
    except APIValidationError as e:
        raise APIValidationError(f"Invalid webpage URL: {e}") from e

    # Validate scan type
    valid_scan_types = ["employer", "student"]
    if scan_type not in valid_scan_types:
        raise APIValidationError(
            f"Invalid scan type. Must be one of: {', '.join(valid_scan_types)}"
        )

    logger.info(f"Scanning webpage: {webpage_url} (type: {scan_type})")

    if scan_type == "student":
        return scan_student_webpage(webpage_url)

    # Employer webpage scanning (existing logic)
    if "techcorp" in webpage_url.lower() or "technology" in webpage_url.lower():
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "company_name": "TechCorp Solutions",
                    "industry": "technology",
                    "company_description": "TechCorp Solutions is a leading technology company specializing in innovative software development and digital transformation services. We help businesses modernize their operations through cutting-edge technology solutions.",
                    "company_location": "St. John's, NL",
                    "website": webpage_url,
                },
            }
        )
    elif "creative" in webpage_url.lower() or "design" in webpage_url.lower():
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "company_name": "Atlantic Creative Studio",
                    "industry": "design",
                    "company_description": "Atlantic Creative Studio is a full-service creative agency focused on branding, web design, and digital marketing. We work with startups and established businesses to create compelling visual identities.",
                    "company_location": "Halifax, NS",
                    "website": webpage_url,
                },
            }
        )
    elif "healthcare" in webpage_url.lower() or "medical" in webpage_url.lower():
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "company_name": "Atlantic Health Services",
                    "industry": "healthcare",
                    "company_description": "Atlantic Health Services provides comprehensive healthcare solutions across the Atlantic provinces. We focus on improving patient outcomes through innovative technology and compassionate care.",
                    "company_location": "Moncton, NB",
                    "website": webpage_url,
                },
            }
        )
    else:
        # Generic fallback for demo
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "company_name": "Sample Company",
                    "industry": "other",
                    "company_description": "We are a dynamic organization focused on growth and innovation in our industry.",
                    "company_location": "Atlantic Canada",
                    "website": webpage_url,
                },
            }
        )

    return JsonResponse({"status": "error", "message": "Invalid request"})


def scan_student_webpage(webpage_url: str) -> JsonResponse:
    """Simulate student webpage/profile scanning"""
    url_lower = webpage_url.lower()

    # LinkedIn profile simulation
    if "linkedin.com" in url_lower:
        if "sarah" in url_lower or "chen" in url_lower:
            return JsonResponse(
                {
                    "status": "success",
                    "extracted_data": {
                        "first_name": "Sarah",
                        "last_name": "Chen",
                        "email": "sarah.chen@mun.ca",
                        "phone": "(709) 123-4567",
                        "academic_year": "junior",
                        "program": "Computer Science",
                        "education_data": [
                            {
                                "institution": "Memorial University of Newfoundland",
                                "degree": "Bachelor of Science",
                                "field": "Computer Science",
                                "start_date": "2022-09-01",
                                "current": True,
                            }
                        ],
                        "employment_data": [
                            {
                                "company": "Tech Innovations Inc",
                                "position": "Software Development Intern",
                                "start_date": "2024-05-01",
                                "end_date": "2024-08-31",
                                "description": "Developed web applications using React and Node.js. Collaborated with senior developers on client projects.",
                            }
                        ],
                        "skills_data": [
                            {
                                "name": "Python",
                                "level": "intermediate",
                                "description": "Experience with Django web framework and data analysis",
                            },
                            {
                                "name": "JavaScript",
                                "level": "advanced",
                                "description": "React, Node.js, and full-stack web development",
                            },
                            {
                                "name": "SQL",
                                "level": "intermediate",
                                "description": "Database design and query optimization",
                            },
                        ],
                    },
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "success",
                    "extracted_data": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@mun.ca",
                        "academic_year": "senior",
                        "program": "Engineering",
                        "skills_data": [
                            {
                                "name": "Python",
                                "level": "advanced",
                                "description": "Machine learning and data science projects",
                            },
                            {
                                "name": "MATLAB",
                                "level": "intermediate",
                                "description": "Engineering simulations and analysis",
                            },
                        ],
                    },
                }
            )

    # GitHub profile simulation
    elif "github.com" in url_lower:
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "first_name": "Alex",
                    "last_name": "Developer",
                    "email": "alex.dev@mun.ca",
                    "academic_year": "graduate",
                    "program": "Computer Science",
                    "skills_data": [
                        {
                            "name": "Python",
                            "level": "expert",
                            "description": "Open source contributions, web scraping, and automation",
                        },
                        {
                            "name": "JavaScript",
                            "level": "advanced",
                            "description": "React, Vue.js, and Node.js projects on GitHub",
                        },
                        {
                            "name": "Docker",
                            "level": "intermediate",
                            "description": "Containerization and deployment of applications",
                        },
                    ],
                },
            }
        )

    # Personal portfolio website simulation
    elif "portfolio" in url_lower or "personal" in url_lower:
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "first_name": "Emma",
                    "last_name": "Designer",
                    "email": "emma.design@mun.ca",
                    "phone": "(709) 234-5678",
                    "academic_year": "sophomore",
                    "program": "Fine Arts",
                    "skills_data": [
                        {
                            "name": "Graphic Design",
                            "level": "advanced",
                            "description": "Adobe Creative Suite, branding, and visual identity projects",
                        },
                        {
                            "name": "Web Design",
                            "level": "intermediate",
                            "description": "HTML/CSS, responsive design, and user experience",
                        },
                        {
                            "name": "Photography",
                            "level": "intermediate",
                            "description": "Digital photography and photo editing",
                        },
                    ],
                },
            }
        )

    # Generic fallback for demo
    else:
        return JsonResponse(
            {
                "status": "success",
                "extracted_data": {
                    "first_name": "Student",
                    "last_name": "Profile",
                    "email": "student@mun.ca",
                    "academic_year": "junior",
                    "program": "General Studies",
                    "skills_data": [
                        {
                            "name": "Communication",
                            "level": "intermediate",
                            "description": "Strong written and verbal communication skills",
                        }
                    ],
                },
            }
        )


def get_ai_validation(field_name: str, value: str) -> dict[str, Any] | None:
    """Simulate AI validation with contextual responses and input sanitization"""
    # Input validation and sanitization
    if not isinstance(field_name, str) or not isinstance(value, str):
        logger.warning(
            f"Invalid input types for AI validation: field_name={type(field_name)}, value={type(value)}"
        )
        return None

    # Sanitize inputs
    field_name = sanitize_string_field(field_name, max_length=100).lower()
    value = sanitize_string_field(value, max_length=1000).lower()

    if not field_name or not value:
        return None

    logger.debug(f"AI validation request for field: {field_name}")

    # Email validation
    if "email" in field_name:
        if value and "@mun.ca" in value:
            return {"message": "✓ University email detected", "type": "success"}
        elif value and "@" in value:
            return {"message": "Consider using your university email", "type": "info"}

    # Name validation
    if "name" in field_name:
        if value and len(value.split()) >= 2:
            return {"message": "✓ Looks good!", "type": "success"}
        elif value:
            return {"message": "Consider including your full name", "type": "info"}

    # Program validation
    if "program" in field_name:
        if "computer" in value or "engineering" in value:
            return {"message": "Great! I can suggest relevant skills", "type": "info"}
        elif "science" in value:
            return {"message": "STEM programs have high demand", "type": "success"}

    # Academic year validation
    if "academic" in field_name:
        if value in ["junior", "senior", "graduate"]:
            return {
                "message": "✓ Good experience level for projects",
                "type": "success",
            }

    # Phone validation
    if "phone" in field_name:
        if "709" in value:
            return {"message": "✓ Newfoundland number detected", "type": "success"}
        elif value and len(value) >= 10:
            return {"message": "✓ Valid phone format", "type": "success"}

    # Skills validation
    if "skill" in field_name:
        high_demand_skills = [
            "python",
            "javascript",
            "react",
            "sql",
            "java",
            "aws",
            "docker",
        ]
        if any(skill in value for skill in high_demand_skills):
            return {"message": "High demand skill in current market", "type": "success"}
        elif value:
            return {
                "message": "Consider adding specific frameworks or tools",
                "type": "info",
            }

    # Availability validation
    if "availability" in field_name and len(value) > 50:
        return {"message": "✓ Detailed availability info", "type": "success"}
    elif "availability" in field_name and value:
        return {"message": "Consider adding more details", "type": "info"}

    # Career goals validation
    if "career" in field_name and value:
        if len(value) > 100:
            return {"message": "✓ Well-defined career goals", "type": "success"}
        else:
            return {"message": "Consider expanding on your goals", "type": "info"}

    # Password validation
    if "password" in field_name:
        if len(value) >= 12:
            return {"message": "✓ Strong password", "type": "success"}
        elif len(value) >= 8:
            return {"message": "Good password length", "type": "info"}
        elif value:
            return {
                "message": "Password should be at least 8 characters",
                "type": "warning",
            }

    # Confirm password validation
    if "confirm" in field_name and "password" in field_name:
        return {"message": "Make sure passwords match", "type": "info"}

    # Company name validation
    if "company" in field_name and "name" in field_name:
        if len(value) > 3:
            return {"message": "✓ Company name looks good", "type": "success"}
        elif value:
            return {"message": "Company name seems short", "type": "info"}

    # Website validation
    if "website" in field_name:
        if value and ("http" in value or "www" in value):
            return {"message": "✓ Valid website format", "type": "success"}
        elif value:
            return {"message": "Include http:// or https://", "type": "info"}

    # Industry validation
    if "industry" in field_name:
        if value:
            return {"message": "✓ Industry selected", "type": "success"}

    # Company description validation
    if "company_description" in field_name or "description" in field_name:
        if len(value) > 150:
            return {"message": "✓ Detailed company description", "type": "success"}
        elif len(value) > 50:
            return {
                "message": "Good description, consider adding more detail",
                "type": "info",
            }
        elif value:
            return {"message": "Add more details about your company", "type": "info"}

    return None  # No validation message
