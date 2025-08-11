import json
import logging
import random
from collections.abc import Callable
from datetime import date, datetime
from functools import wraps
from typing import Any, cast

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.models import (
    Education,
    EmployerProfile,
    Employment,
    Project,
    Skill,
    StudentProfile,
    User,
)

logger = logging.getLogger(__name__)


class ProfileCreationError(Exception):
    """Custom exception for profile creation failures"""

    pass


def handle_profile_errors(func: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    """Decorator to handle common profile creation/update errors"""

    @wraps(func)
    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> JsonResponse:
        try:
            return func(request, *args, **kwargs)
        except ProfileCreationError as e:
            logger.warning(f"Profile operation failed in {func.__name__}: {e}")
            return JsonResponse({"status": "error", "message": str(e)})
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            error_msg = "Please check your input data for errors."
            if hasattr(e, "message_dict"):
                # Extract first error message for user-friendly display
                first_errors = next(iter(e.message_dict.values()))
                if first_errors:
                    error_msg = first_errors[0]
            return JsonResponse({"status": "error", "message": error_msg})
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {e}")
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Data conflict occurred. Please try again.",
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return JsonResponse(
                {
                    "status": "error",
                    "message": "An unexpected error occurred. Please try again.",
                }
            )

    return wrapper


def validate_required_profile_fields(data: dict, required_fields: list[str]) -> None:
    """Validate that required profile fields are present and not empty"""
    missing_fields = []
    for field in required_fields:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)

    if missing_fields:
        field_names = ", ".join(missing_fields)
        raise ProfileCreationError(
            f"Required fields are missing or empty: {field_names}"
        )


def sanitize_profile_data(post_data: dict) -> dict[str, Any]:
    """Sanitize form data for profile creation/updates"""
    sanitized = {}

    # Define max lengths for various fields
    field_limits = {
        "phone": 20,
        "academic_year": 50,
        "program": 200,
        "availability_notes": 500,
        "location_flexibility": 200,
        "career_goals": 1000,
        "additional_info": 1000,
        "company_name": 200,
        "contact_name": 100,
        "contact_title": 100,
        "industry": 100,
        "company_size": 50,
        "website": 500,
        "description": 2000,
    }

    for key, value in post_data.items():
        if isinstance(value, str):
            # Strip whitespace and apply length limits
            cleaned = value.strip()
            max_length = field_limits.get(key, 255)
            if len(cleaned) > max_length:
                logger.warning(
                    f"Field '{key}' truncated from {len(cleaned)} to {max_length} characters"
                )
                cleaned = cleaned[:max_length]

            # Basic XSS prevention
            if "<" in cleaned or ">" in cleaned:
                logger.warning(f"Potential XSS attempt in field '{key}', sanitizing")
                cleaned = cleaned.replace("<", "").replace(">", "")

            sanitized[key] = cleaned
        else:
            sanitized[key] = value

    return sanitized


def parse_date_string(date_str: str | None) -> date | None:
    """Parse date string and return a date object, None if invalid/empty"""
    if not date_str or not date_str.strip():
        return None
    try:
        # Django usually sends dates in YYYY-MM-DD format from HTML date inputs
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        # If that fails, try other common formats
        try:
            return datetime.strptime(date_str.strip(), "%m/%d/%Y").date()
        except ValueError:
            return None


def parse_required_date_string(date_str: str | None) -> date:
    """Parse date string and return a date object, use today if invalid/empty"""
    parsed_date = parse_date_string(date_str)
    if parsed_date is None:
        # Return today's date as fallback for required fields
        return date.today()
    return parsed_date


def home(request: HttpRequest) -> HttpResponse:
    # If user is already logged in, redirect to appropriate dashboard
    auth_user = cast(User, request.user)
    if request.user.is_authenticated:
        # Handle admin users and users without user_type
        if not hasattr(auth_user, "user_type") or not auth_user.user_type:
            if auth_user.is_staff or auth_user.is_superuser:
                # Admin users can stay on home page or redirect to admin
                return render(
                    request,
                    "auth_choice.html",
                    {"show_admin_link": True, "user": request.user},
                )
            else:
                # Regular users without user_type should choose their role
                return redirect("web:register")

        # Handle regular users with user_type
        if auth_user.user_type == "student":
            try:
                auth_user.student_profile  # type: ignore[misc]  # Check if profile exists  # noqa: B018
                return redirect("web:student_dashboard")
            except StudentProfile.DoesNotExist:
                # User exists but needs to complete profile - redirect to profile setup
                return redirect("web:student_profile_setup")
        elif auth_user.user_type == "employer":
            return redirect("web:employer_dashboard")

    # Show auth choice for anonymous users
    return render(request, "auth_choice.html")


def register(request: HttpRequest) -> HttpResponse:
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect("web:home")

    return render(request, "register_choice.html")


def student_account_creation(request: HttpRequest) -> HttpResponse:
    """Step 1: Account creation with email and password"""
    # If user is already logged in, check if they need to complete their profile
    auth_user = cast(User, request.user)
    if auth_user.is_authenticated:
        if auth_user.user_type == "student":
            # Check if they have a complete profile
            try:
                auth_user.student_profile  ## type: ignore[misc]  # Check if profile exists  # noqa: B018
                return redirect("web:student_dashboard")
            except StudentProfile.DoesNotExist:
                # User exists but needs to complete profile - redirect to profile setup
                return redirect("web:student_profile_setup")
        else:
            # Not a student, redirect to appropriate place
            return redirect("web:home")

    return render(request, "student_account_creation.html")


def student_profile_setup(request: HttpRequest) -> HttpResponse:
    """Step 2: Profile setup wizard (after account creation)"""
    # Check if user is authenticated and is a student
    auth_user = cast(User, request.user)

    if not request.user.is_authenticated:
        return redirect("web:student_register")

    if auth_user.user_type != "student":
        return redirect("web:home")

    # Check if profile already exists
    profile = getattr(request.user, "student_profile", None)
    if profile is not None:
        return redirect("web:student_dashboard")
    else:
        # Show profile setup wizard
        return render(request, "student_registration.html")


@require_http_methods(["POST"])
def process_student_registration(request: HttpRequest) -> JsonResponse:
    """Handle the profile creation steps (after account is created)"""
    current_step = int(request.POST.get("current_step", 1))

    if current_step == 8:  # Final step - create complete profile
        return create_student_profile(request)

    # For other steps, just return success (client-side navigation)
    return JsonResponse({"status": "success", "step": current_step})


@handle_profile_errors
def create_student_profile(request: HttpRequest) -> JsonResponse:
    """Create the complete student profile after account exists with transaction safety"""
    auth_user = cast(User, request.user)

    # User should already be authenticated at this point
    if not auth_user.is_authenticated or auth_user.user_type != "student":
        raise ProfileCreationError("Invalid session. Please start over.")

    # Check if profile already exists
    if hasattr(auth_user, "student_profile"):
        raise ProfileCreationError("Profile already exists.")

    # Sanitize input data
    sanitized_data = sanitize_profile_data(dict(request.POST.items()))

    # Validate required fields
    required_fields = ["academic_year", "program", "currently_available"]
    validate_required_profile_fields(sanitized_data, required_fields)

    # Validate academic year
    valid_academic_years = ["freshman", "sophomore", "junior", "senior", "graduate"]
    if sanitized_data.get("academic_year") not in valid_academic_years:
        raise ProfileCreationError(
            f"Invalid academic year. Must be one of: {', '.join(valid_academic_years)}"
        )

    # Validate availability
    valid_availability = ["yes", "no", "limited"]
    if sanitized_data.get("currently_available") not in valid_availability:
        raise ProfileCreationError(
            f"Invalid availability status. Must be one of: {', '.join(valid_availability)}"
        )

    logger.info(f"Creating student profile for user {auth_user.id}")

    # Use atomic transaction to ensure data consistency
    with transaction.atomic():
        # Collect and validate external links
        external_links = {}
        url_fields = ["linkedin_url", "github_url", "portfolio_url", "other_url"]

        for field in url_fields:
            url = sanitized_data.get(field)
            if url:
                # Basic URL validation
                if not (url.startswith("http://") or url.startswith("https://")):
                    logger.warning(f"Invalid URL format for {field}, skipping: {url}")
                    continue
                if len(url) > 500:
                    logger.warning(f"URL too long for {field}, truncating")
                    url = url[:500]

                field_key = field.replace("_url", "")
                external_links[field_key] = url

        # Create student profile
        profile = StudentProfile.objects.create(
            user=auth_user,
            phone=sanitized_data.get("phone", ""),
            academic_year=sanitized_data.get("academic_year", ""),
            program=sanitized_data.get("program", ""),
            currently_available=sanitized_data.get("currently_available", ""),
            available_date=sanitized_data.get("available_date") or None,
            availability_notes=sanitized_data.get("availability_notes", ""),
            remote_preference=sanitized_data.get("remote_preference", ""),
            location_flexibility=sanitized_data.get("location_flexibility", ""),
            career_goals=sanitized_data.get("career_goals", ""),
            additional_info=sanitized_data.get("additional_info", ""),
            availability=request.POST.getlist("availability"),
            external_links=external_links,
            profile_complete=True,
        )

        # Validate the profile before proceeding
        profile.full_clean()

        # Create education entries with validation
        education_count = 0
        created_education = 0

        while f"education_institution_{education_count}" in request.POST:
            institution = sanitized_data.get(f"education_institution_{education_count}")
            if institution and institution.strip():
                try:
                    # Validate GPA if provided
                    gpa_str = sanitized_data.get(f"education_gpa_{education_count}")
                    gpa = None
                    if gpa_str:
                        try:
                            gpa = float(gpa_str)
                            if gpa < 0 or gpa > 4.0:
                                logger.warning(
                                    f"Invalid GPA value: {gpa}, setting to None"
                                )
                                gpa = None
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Invalid GPA format: {gpa_str}, setting to None"
                            )
                            gpa = None

                    education = Education.objects.create(
                        student=profile,
                        institution=institution.strip(),
                        degree=sanitized_data.get(
                            f"education_degree_{education_count}", ""
                        ),
                        field_of_study=sanitized_data.get(
                            f"education_field_{education_count}", ""
                        ),
                        gpa=gpa,
                        start_date=parse_required_date_string(
                            request.POST.get(f"education_start_{education_count}")
                        ),
                        end_date=parse_date_string(
                            request.POST.get(f"education_end_{education_count}")
                        ),
                        is_current=bool(
                            request.POST.get(f"education_current_{education_count}")
                        ),
                    )
                    education.full_clean()
                    created_education += 1

                except ValidationError as e:
                    logger.warning(
                        f"Skipping invalid education entry {education_count}: {e}"
                    )
                    continue

            education_count += 1

        # Create employment entries
        employment_count = 0
        while f"employment_company_{employment_count}" in request.POST:
            company = request.POST.get(f"employment_company_{employment_count}")
            if company:
                Employment.objects.create(
                    student=profile,
                    company=company,
                    position=request.POST.get(
                        f"employment_position_{employment_count}", ""
                    ),
                    start_date=parse_required_date_string(
                        request.POST.get(f"employment_start_{employment_count}")
                    ),
                    end_date=parse_date_string(
                        request.POST.get(f"employment_end_{employment_count}")
                    ),
                    description=request.POST.get(
                        f"employment_description_{employment_count}", ""
                    ),
                    is_current=bool(
                        request.POST.get(f"employment_current_{employment_count}")
                    ),
                )
            employment_count += 1

        # Create skill entries
        skill_count = 0
        while f"skill_name_{skill_count}" in request.POST:
            skill_name = request.POST.get(f"skill_name_{skill_count}")
            if skill_name:
                Skill.objects.create(
                    student=profile,
                    name=skill_name,
                    level=request.POST.get(f"skill_level_{skill_count}", "beginner"),
                    experience_description=request.POST.get(
                        f"skill_description_{skill_count}", ""
                    ),
                )
            skill_count += 1

        # Create documents entries
        documents = []
        document_count = 0
        while f"document_type_{document_count}" in request.POST:
            doc_type = request.POST.get(f"document_type_{document_count}")
            doc_title = request.POST.get(f"document_title_{document_count}")
            if doc_type or doc_title:
                document_entry = {
                    "type": doc_type,
                    "title": doc_title,
                    "description": request.POST.get(
                        f"document_description_{document_count}", ""
                    ),
                    "file_uploaded": bool(
                        request.FILES.get(f"document_file_{document_count}")
                    ),
                }
                documents.append(document_entry)
            document_count += 1

        # Create profile links entries
        profile_links = []
        link_count = 0
        while f"link_type_{link_count}" in request.POST:
            link_type = request.POST.get(f"link_type_{link_count}")
            link_url = request.POST.get(f"link_url_{link_count}")
            if link_type or link_url:
                link_entry = {
                    "type": link_type,
                    "title": request.POST.get(f"link_title_{link_count}", ""),
                    "url": link_url,
                    "description": request.POST.get(
                        f"link_description_{link_count}", ""
                    ),
                }
                profile_links.append(link_entry)
            link_count += 1

        # Update profile with documents and links
        profile.documents = documents
        profile.profile_links = profile_links
        profile.save()

        return JsonResponse(
            {
                "status": "success",
                "message": "Profile created successfully!",
                "redirect": "/student/dashboard/",
            }
        )


@require_http_methods(["POST"])
@handle_profile_errors
def create_student_account(request: HttpRequest) -> JsonResponse:
    """Create student account with email/password validation and transaction safety"""
    # Get and sanitize form data
    sanitized_data = sanitize_profile_data(dict(request.POST.items()))

    email = sanitized_data.get("email", "").strip().lower()
    password = request.POST.get("password", "")  # Don't sanitize passwords
    confirm_password = request.POST.get("confirm_password", "")
    first_name = sanitized_data.get("first_name", "").strip()
    last_name = sanitized_data.get("last_name", "").strip()

    # Validate required fields
    required_fields = ["email", "password", "first_name", "last_name"]
    form_data = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
    }
    validate_required_profile_fields(form_data, required_fields)

    # Validate email format and domain
    if "@" not in email or not email.endswith("@mun.ca"):
        raise ProfileCreationError(
            "Only @mun.ca email addresses are accepted for student accounts."
        )

    if len(email) > 254:  # RFC limit
        raise ProfileCreationError("Email address is too long.")

    # Validate name fields
    if len(first_name) < 1 or len(last_name) < 1:
        raise ProfileCreationError("First and last names must be provided.")

    if len(first_name) > 100 or len(last_name) > 100:
        raise ProfileCreationError("Names are too long.")

    # Validate password strength
    if len(password) < 8:
        raise ProfileCreationError("Password must be at least 8 characters long.")

    if len(password) > 128:  # Reasonable upper limit
        raise ProfileCreationError("Password is too long.")

    if password != confirm_password:
        raise ProfileCreationError("Passwords do not match.")

    logger.info(f"Creating student account for email: {email}")

    # Use atomic transaction for account creation
    with transaction.atomic():
        # Double-check email uniqueness within transaction
        if User.objects.filter(email=email).exists():
            raise ProfileCreationError(
                "An account with this email already exists. Please sign in instead."
            )

        # Create user account
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type="student",
        )

        # Validate user before proceeding
        user.full_clean()

        # Defensive check: ensure user was created with an ID
        if not user.id:
            raise ProfileCreationError("Failed to create user account - no ID assigned")

        # Log the user in
        login(request, user)

        logger.info(
            f"Student account created successfully for: {email} (ID: {user.id})"
        )

        return JsonResponse(
            {
                "status": "success",
                "message": "Account created successfully!",
                "user_id": user.id,  # Now guaranteed to be not None with type hint
            }
        )


def employer_register(request: HttpRequest) -> HttpResponse:
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect("web:home")

    return render(request, "employer_registration.html")


@require_http_methods(["POST"])
def process_employer_registration(request: HttpRequest) -> JsonResponse:
    current_step = int(request.POST.get("current_step", 1))

    if current_step == 3:  # Final step - create employer account
        return create_employer_account(request)

    # For other steps, just return success (client-side navigation)
    return JsonResponse({"status": "success", "step": current_step})


def create_employer_account(request: HttpRequest) -> JsonResponse:
    try:
        # Check if email already exists
        email = request.POST.get("email") or ""
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {
                    "status": "error",
                    "message": "An account with this email already exists. Please sign in instead.",
                }
            )

        # Get and validate password
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not password or len(password) < 8:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Password must be at least 8 characters long.",
                }
            )

        if password != confirm_password:
            return JsonResponse(
                {"status": "error", "message": "Passwords do not match."}
            )

        # Create user
        first_name = request.POST.get("first_name") or ""
        last_name = request.POST.get("last_name") or ""

        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type="employer",
        )

        # Create employer profile
        EmployerProfile.objects.create(
            user=user,
            company_name=request.POST.get("company_name") or "",
            industry=request.POST.get("industry") or "",
            website=request.POST.get("website", ""),
            company_description=request.POST.get("company_description") or "",
            company_location=request.POST.get("company_location") or "",
            contact_name=request.POST.get("contact_name") or "",
            contact_title=request.POST.get("contact_title") or "",
            contact_phone=request.POST.get("contact_phone", ""),
            approval_status="pending",  # Requires admin approval
        )

        return JsonResponse(
            {
                "status": "success",
                "message": "Your registration has been submitted for review. You will receive an email notification once approved.",
            }
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error creating account: {str(e)}"}
        )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("web:home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email and password:
            # Try to find user by email (which is used as username)
            try:
                user = User.objects.get(email=email)
                # Authenticate using username and password
                auth_user = cast(
                    User,
                    authenticate(request, username=user.username, password=password),
                )

                if auth_user:
                    login(request, auth_user)

                    # Redirect based on user type
                    if auth_user.user_type == "student":
                        return redirect("web:student_dashboard")
                    elif auth_user.user_type == "employer":
                        return redirect("web:employer_dashboard")
                    else:
                        return redirect("web:home")
                else:
                    messages.error(request, "Invalid email or password.")
            except User.DoesNotExist:
                messages.error(request, "No account found with this email address.")
        else:
            messages.error(request, "Please provide both email and password.")

    return render(request, "login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        logout(request)

    return redirect("web:home")


def verify_email(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Email Verification")


@login_required
def student_dashboard(request: HttpRequest) -> HttpResponse:
    auth_user = cast(User, request.user)
    if not hasattr(auth_user, "user_type") or auth_user.user_type != "student":
        messages.error(request, "Access denied. Student account required.")
        logout(request)
        return redirect("web:login")

    try:
        profile = request.user.student_profile  # type: ignore[union-attr]
        return render(request, "student_dashboard.html", {"profile": profile})
    except StudentProfile.DoesNotExist:
        messages.info(request, "Please complete your student profile.")
        return redirect("web:student_register")


@login_required
def student_profile(request: HttpRequest) -> HttpResponse:
    """Edit student profile page"""
    auth_user = cast(User, request.user)
    if not hasattr(request.user, "user_type") or auth_user.user_type != "student":
        messages.error(request, "Access denied. Student account required.")
        return redirect("web:login")

    try:
        profile = request.user.student_profile  # type: ignore[union-attr]

        if request.method == "POST":
            return update_student_profile(request, profile)

        # GET request - show the edit form
        context = {
            "profile": profile,
            "user": request.user,
            "education_entries": profile.education.all(),
            "employment_entries": profile.employment.all(),
            "skill_entries": profile.skills.all(),
        }
        return render(request, "student_profile_edit.html", context)

    except StudentProfile.DoesNotExist:
        messages.info(request, "Please complete your student profile first.")
        return redirect("web:student_profile_setup")


def update_student_profile(
    request: HttpRequest, profile: "StudentProfile"
) -> HttpResponse:
    """Handle student profile updates"""
    try:
        # Update user information
        user = request.user  # type: ignore[assignment]
        user.first_name = request.POST.get("first_name", user.first_name)  # type: ignore[union-attr]
        user.last_name = request.POST.get("last_name", user.last_name)  # type: ignore[union-attr]
        user.email = request.POST.get("email", user.email)  # type: ignore[union-attr]
        user.save()

        # Update external links
        external_links = {}
        if request.POST.get("linkedin_url"):
            external_links["linkedin"] = request.POST.get("linkedin_url")
        if request.POST.get("github_url"):
            external_links["github"] = request.POST.get("github_url")
        if request.POST.get("portfolio_url"):
            external_links["portfolio"] = request.POST.get("portfolio_url")
        if request.POST.get("other_url"):
            external_links["other"] = request.POST.get("other_url")

        # Update profile information
        profile.phone = request.POST.get("phone", "")
        profile.academic_year = request.POST.get("academic_year", "")
        profile.program = request.POST.get("program", "")
        profile.currently_available = request.POST.get("currently_available", "")
        profile.available_date = request.POST.get("available_date") or None
        profile.availability_notes = request.POST.get("availability_notes", "")
        profile.remote_preference = request.POST.get("remote_preference", "")
        profile.location_flexibility = request.POST.get("location_flexibility", "")
        profile.career_goals = request.POST.get("career_goals", "")
        profile.additional_info = request.POST.get("additional_info", "")
        profile.availability = request.POST.getlist("availability")
        profile.external_links = external_links
        profile.save()

        # Update education entries (delete existing and recreate)
        profile.education.all().delete()  # type: ignore[misc]
        education_count = 0
        while f"education_institution_{education_count}" in request.POST:
            institution = request.POST.get(f"education_institution_{education_count}")
            if institution:
                Education.objects.create(
                    student=profile,
                    institution=institution,
                    degree=request.POST.get(f"education_degree_{education_count}", ""),
                    field_of_study=request.POST.get(
                        f"education_field_{education_count}", ""
                    ),
                    gpa=request.POST.get(f"education_gpa_{education_count}") or None,
                    start_date=parse_required_date_string(
                        request.POST.get(f"education_start_{education_count}")
                    ),
                    end_date=parse_date_string(
                        request.POST.get(f"education_end_{education_count}")
                    ),
                    is_current=bool(
                        request.POST.get(f"education_current_{education_count}")
                    ),
                )
            education_count += 1

        # Update employment entries (delete existing and recreate)
        profile.employment.all().delete()  # type: ignore[misc]
        employment_count = 0
        while f"employment_company_{employment_count}" in request.POST:
            company = request.POST.get(f"employment_company_{employment_count}")
            if company:
                Employment.objects.create(
                    student=profile,
                    company=company,
                    position=request.POST.get(
                        f"employment_position_{employment_count}", ""
                    ),
                    start_date=parse_required_date_string(
                        request.POST.get(f"employment_start_{employment_count}")
                    ),
                    end_date=parse_date_string(
                        request.POST.get(f"employment_end_{employment_count}")
                    ),
                    description=request.POST.get(
                        f"employment_description_{employment_count}", ""
                    ),
                    is_current=bool(
                        request.POST.get(f"employment_current_{employment_count}")
                    ),
                )
            employment_count += 1

        # Update skill entries (delete existing and recreate)
        profile.skills.all().delete()  # type: ignore[misc]
        skill_count = 0
        while f"skill_name_{skill_count}" in request.POST:
            skill_name = request.POST.get(f"skill_name_{skill_count}")
            if skill_name:
                Skill.objects.create(
                    student=profile,
                    name=skill_name,
                    level=request.POST.get(f"skill_level_{skill_count}", "beginner"),
                    experience_description=request.POST.get(
                        f"skill_description_{skill_count}", ""
                    ),
                )
            skill_count += 1

        # Update documents entries
        documents = []
        document_count = 0
        while f"document_type_{document_count}" in request.POST:
            doc_type = request.POST.get(f"document_type_{document_count}")
            doc_title = request.POST.get(f"document_title_{document_count}")
            if doc_type or doc_title:
                document_entry = {
                    "type": doc_type,
                    "title": doc_title,
                    "description": request.POST.get(
                        f"document_description_{document_count}", ""
                    ),
                    "file_uploaded": bool(
                        request.FILES.get(f"document_file_{document_count}")
                    ),
                }
                documents.append(document_entry)
            document_count += 1

        # Update profile links entries
        profile_links = []
        link_count = 0
        while f"link_type_{link_count}" in request.POST:
            link_type = request.POST.get(f"link_type_{link_count}")
            link_url = request.POST.get(f"link_url_{link_count}")
            if link_type or link_url:
                link_entry = {
                    "type": link_type,
                    "title": request.POST.get(f"link_title_{link_count}", ""),
                    "url": link_url,
                    "description": request.POST.get(
                        f"link_description_{link_count}", ""
                    ),
                }
                profile_links.append(link_entry)
            link_count += 1

        # Update profile with documents and links
        profile.documents = documents
        profile.profile_links = profile_links
        profile.save()

        return redirect("web:student_dashboard")

    except Exception as e:
        messages.error(request, f"Error updating profile: {str(e)}")
        return redirect("web:student_profile")


@login_required
def employer_dashboard(request: HttpRequest) -> HttpResponse:
    auth_user = cast(User, request.user)
    if not hasattr(request.user, "user_type") or auth_user.user_type != "employer":
        messages.error(request, "Access denied. Employer account required.")
        return redirect("web:login")

    try:
        profile = request.user.employer_profile  # type: ignore[union-attr]

        # Check approval status
        if profile.approval_status != "approved":
            return render(request, "employer_pending.html", {"profile": profile})

        # Get projects for approved employers
        projects = profile.projects.all().order_by("-created_at")

        return render(
            request,
            "employer_dashboard.html",
            {"profile": profile, "projects": projects},
        )

    except EmployerProfile.DoesNotExist:
        messages.info(request, "Please complete your employer registration.")
        return redirect("web:employer_register")


@login_required
def create_project(request: HttpRequest) -> HttpResponse:
    auth_user = cast(User, request.user)
    if not hasattr(request.user, "user_type") or auth_user.user_type != "employer":
        messages.error(request, "Access denied. Employer account required.")
        return redirect("web:login")

    try:
        profile = request.user.employer_profile  # type: ignore[union-attr]

        # Check if employer is approved
        if profile.approval_status != "approved":
            messages.warning(
                request, "Your account must be approved before you can post projects."
            )
            return redirect("web:employer_dashboard")

        if request.method == "POST":
            return process_project_creation(request, profile)

        return render(request, "create_project.html", {"profile": profile})

    except EmployerProfile.DoesNotExist:
        messages.info(request, "Please complete your employer registration.")
        return redirect("web:employer_register")


def process_project_creation(
    request: HttpRequest, profile: "EmployerProfile"
) -> HttpResponse:
    try:
        # Collect required skills
        required_skills = []
        skill_index = 0
        while f"required_skills_{skill_index}" in request.POST:
            skill = request.POST.get(f"required_skills_{skill_index}", "").strip()
            if skill:
                required_skills.append(skill)
            skill_index += 1

        # Collect preferred skills
        preferred_skills = []
        skill_index = 0
        while f"preferred_skills_{skill_index}" in request.POST:
            skill = request.POST.get(f"preferred_skills_{skill_index}", "").strip()
            if skill:
                preferred_skills.append(skill)
            skill_index += 1

        # Handle preferred programs
        preferred_programs_str = request.POST.get("preferred_programs", "")
        preferred_programs = (
            [p.strip() for p in preferred_programs_str.split(",") if p.strip()]
            if preferred_programs_str
            else []
        )

        # Create project
        from core.models import Project

        project = Project.objects.create(
            employer=profile,
            title=request.POST.get("title") or "",
            description=request.POST.get("description") or "",
            project_type=request.POST.get("project_type") or "",
            duration=request.POST.get("duration") or "",
            work_type=request.POST.get("work_type") or "",
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_academic_year=request.POST.get("min_academic_year", ""),
            preferred_programs=preferred_programs,
            is_active=True,
        )

        messages.success(
            request, f'Project "{project.title}" has been posted successfully!'
        )
        return redirect("web:employer_dashboard")

    except Exception as e:
        messages.error(request, f"Error creating project: {str(e)}")
        return render(request, "create_project.html", {"profile": profile})


@login_required
def project_matches(request: HttpRequest, project_id: int) -> HttpResponse:
    """Show student matches for a specific project"""
    auth_user = cast(User, request.user)
    if not hasattr(request.user, "user_type") or auth_user.user_type != "employer":
        messages.error(request, "Access denied. Employer account required.")
        return redirect("web:login")

    try:
        profile = request.user.employer_profile  # type: ignore[union-attr]
        if profile.approval_status != "approved":
            messages.warning(request, "Your account must be approved to view matches.")
            return redirect("web:employer_dashboard")

        # Get project and verify ownership
        from core.models import Project

        project = Project.objects.get(id=project_id, employer=profile)

        # Get matches using our matching algorithm
        from core.matching import get_project_matches

        matches = get_project_matches(project_id)

        return render(
            request,
            "project_matches.html",
            {"project": project, "matches": matches, "profile": profile},
        )

    except Project.DoesNotExist:
        messages.error(
            request, "Project not found or you do not have permission to view it."
        )
        return redirect("web:employer_dashboard")
    except EmployerProfile.DoesNotExist:
        messages.info(request, "Please complete your employer registration.")
        return redirect("web:employer_register")


@login_required
def browse_projects(request: HttpRequest) -> HttpResponse:
    """Show projects that match the current student"""
    auth_user = cast(User, request.user)
    if not hasattr(request.user, "user_type") or auth_user.user_type != "student":
        messages.error(request, "Access denied. Student account required.")
        return redirect("web:login")

    try:
        student_profile = request.user.student_profile  # type: ignore[union-attr]

        # Get project matches using our matching algorithm
        from core.matching import get_student_projects

        project_matches = get_student_projects(student_profile)

        return render(
            request,
            "browse_projects.html",
            {"student_profile": student_profile, "project_matches": project_matches},
        )

    except StudentProfile.DoesNotExist:
        messages.info(request, "Please complete your student profile.")
        return redirect("web:student_register")


@login_required
def employer_projects(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Employer Projects")


@staff_member_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Admin dashboard with employer approval management and trend analytics"""
    from datetime import datetime, timedelta

    from django.db.models import Count

    from core.models import EmployerProfile, StudentProfile

    # Get pending employer approvals
    pending_employers = EmployerProfile.objects.filter(
        approval_status="pending"
    ).order_by("-created_at")
    approved_employers = EmployerProfile.objects.filter(
        approval_status="approved"
    ).order_by("-created_at")[:5]

    # Get platform statistics
    total_students = StudentProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(is_active=True).count()

    # Generate demo trend data for the last 30 days
    from datetime import date

    def generate_demo_trend_data() -> dict[str, list[dict[str, Any]]]:
        """Generate realistic demo data for the last 30 days"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        dates = [(thirty_days_ago + timedelta(days=i)).date() for i in range(30)]

        # Generate realistic trends with some variability but always increasing overall
        def generate_trend(
            base_rate: float, growth_factor: float, variability: float = 0.3
        ) -> list[dict[str, Any]]:
            trend: list[dict[str, Any]] = []
            cumulative_base = base_rate
            for i, day in enumerate(dates):
                # Base growth with some randomness but ensure minimum growth
                daily_count = int(cumulative_base + random.uniform(0, variability))

                # Add some realistic patterns (weekends typically lower, some random spikes)
                if (
                    day.weekday() >= 5
                ):  # Weekend - reduce but don't go below previous trend
                    daily_count = max(daily_count, int(daily_count * 0.7))
                elif random.random() < 0.1:  # 10% chance of spike
                    daily_count = int(daily_count * 1.5)

                # Ensure we never decrease from the overall trend
                if i > 0 and len(trend) > 0:
                    daily_count = max(daily_count, int(trend[-1]["count"]))

                # Always add data points to show consistent growth
                trend.append({"date": day.strftime("%Y-%m-%d"), "count": daily_count})

                # Gradually increase the baseline for next day
                cumulative_base += growth_factor

            return trend

        return {
            "students": generate_trend(
                base_rate=2.5, growth_factor=0.15, variability=1.2
            ),  # Highest volume
            "employers": generate_trend(
                base_rate=0.8, growth_factor=0.05, variability=0.4
            ),  # Medium volume
            "projects": generate_trend(
                base_rate=1.2, growth_factor=0.08, variability=0.6
            ),  # Between students and employers
        }

    # Get real data first, then supplement with demo data for better visualization
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # Get actual data (might be sparse for new installations)
    real_student_trend = (
        StudentProfile.objects.filter(created_at__gte=thirty_days_ago)
        .extra({"date": "date(created_at)"})
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    real_employer_trend = (
        EmployerProfile.objects.filter(created_at__gte=thirty_days_ago)
        .extra({"date": "date(created_at)"})
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    real_project_trend = (
        Project.objects.filter(created_at__gte=thirty_days_ago)
        .extra({"date": "date(created_at)"})
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Use demo data if we don't have enough real data for a good demo
    total_real_data_points = (
        len(real_student_trend) + len(real_employer_trend) + len(real_project_trend)
    )

    if total_real_data_points < 10:  # If we have sparse real data, use demo data
        demo_data = generate_demo_trend_data()
        student_trend_data = demo_data["students"]
        employer_trend_data = demo_data["employers"]
        project_trend_data = demo_data["projects"]
    else:
        # Convert real data to the same format
        def format_real_trend_data(queryset: QuerySet) -> list[dict[str, str | int]]:
            data = []
            for item in queryset:
                data.append(
                    {
                        "date": item["date"].strftime("%Y-%m-%d")
                        if isinstance(item["date"], date)
                        else str(item["date"]),
                        "count": item["count"],
                    }
                )
            return data

        student_trend_data = format_real_trend_data(real_student_trend)
        employer_trend_data = format_real_trend_data(real_employer_trend)
        project_trend_data = format_real_trend_data(real_project_trend)

    context = {
        "pending_employers": pending_employers,
        "approved_employers": approved_employers,
        "stats": {
            "total_students": total_students,
            "total_employers": total_employers,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "pending_approvals": pending_employers.count(),
        },
        "trend_data": {
            "students": json.dumps(student_trend_data),
            "employers": json.dumps(employer_trend_data),
            "projects": json.dumps(project_trend_data),
        },
    }

    return render(request, "admin_dashboard.html", context)


@staff_member_required
@require_http_methods(["POST"])
def approve_employer(request: HttpRequest, employer_id: int) -> JsonResponse:
    """Approve a pending employer"""
    try:
        employer = EmployerProfile.objects.get(
            id=employer_id, approval_status="pending"
        )
        employer.approval_status = "approved"
        employer.save()

        messages.success(
            request, f'Employer "{employer.company_name}" has been approved.'
        )
        return JsonResponse(
            {"status": "success", "message": "Employer approved successfully"}
        )

    except EmployerProfile.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employer not found or already processed"},
            status=404,
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
def reject_employer(request: HttpRequest, employer_id: int) -> JsonResponse:
    """Reject a pending employer"""
    try:
        employer = EmployerProfile.objects.get(
            id=employer_id, approval_status="pending"
        )
        reason = request.POST.get("reason", "No reason provided")

        employer.approval_status = "rejected"
        employer.rejection_reason = reason
        employer.save()

        messages.success(
            request, f'Employer "{employer.company_name}" has been rejected.'
        )
        return JsonResponse({"status": "success", "message": "Employer rejected"})

    except EmployerProfile.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Employer not found or already processed"},
            status=404,
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
