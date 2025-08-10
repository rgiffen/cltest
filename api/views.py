from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def create_user(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "success", "message": "User created"})


@csrf_exempt
def update_profile(request: HttpRequest, user_id: int) -> JsonResponse:
    return JsonResponse(
        {"status": "success", "message": f"Profile updated for user {user_id}"}
    )


@csrf_exempt
def verify_auth(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "success", "verified": True})


@csrf_exempt
def update_skills(request: HttpRequest, user_id: int) -> JsonResponse:
    return JsonResponse(
        {"status": "success", "message": f"Skills updated for user {user_id}"}
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
def validate_responses(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        field_name = request.POST.get("field_name", "")
        field_value = request.POST.get("field_value", "")

        # AI validation logic based on field and value
        validation_result = get_ai_validation(field_name, field_value)
        return JsonResponse({"validation": validation_result})

    return JsonResponse({"validation": {"status": "valid", "suggestions": []}})


@csrf_exempt
def scan_webpage(request: HttpRequest) -> JsonResponse:
    """Simulate webpage scanning and data extraction"""
    if request.method == "POST":
        webpage_url = request.POST.get("webpage_url", "")
        scan_type = request.POST.get("scan_type", "employer")  # 'employer' or 'student'

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
    """Simulate AI validation with contextual responses"""
    value = value.strip().lower()

    # # Email validation
    # if 'email' in field_name:
    #     if value and '@mun.ca' in value:
    #         return {"message": "✓ University email detected", "type": "success"}
    #     elif value and '@' in value:
    #         return {"message": "Consider using your university email", "type": "info"}

    # # Name validation
    # if 'name' in field_name:
    #     if value and len(value.split()) >= 2:
    #         return {"message": "✓ Looks good!", "type": "success"}
    #     elif value:
    #         return {"message": "Consider including your full name", "type": "info"}

    # # Program validation
    # if 'program' in field_name:
    #     if 'computer' in value or 'engineering' in value:
    #         return {"message": "Great! I can suggest relevant skills", "type": "info"}
    #     elif 'science' in value:
    #         return {"message": "STEM programs have high demand", "type": "success"}

    # # Academic year validation
    # if 'academic' in field_name:
    #     if value in ['junior', 'senior', 'graduate']:
    #         return {"message": "✓ Good experience level for projects", "type": "success"}

    # # Phone validation
    # if 'phone' in field_name:
    #     if '709' in value:
    #         return {"message": "✓ Newfoundland number detected", "type": "success"}
    #     elif value and len(value) >= 10:
    #         return {"message": "✓ Valid phone format", "type": "success"}

    # # Skills validation
    # if 'skill' in field_name:
    #     high_demand_skills = ['python', 'javascript', 'react', 'sql', 'java', 'aws', 'docker']
    #     if any(skill in value for skill in high_demand_skills):
    #         return {"message": "High demand skill in current market", "type": "success"}
    #     elif value:
    #         return {"message": "Consider adding specific frameworks or tools", "type": "info"}

    # # Availability validation
    # if 'availability' in field_name and len(value) > 50:
    #     return {"message": "✓ Detailed availability info", "type": "success"}
    # elif 'availability' in field_name and value:
    #     return {"message": "Consider adding more details", "type": "info"}

    # # Career goals validation
    # if 'career' in field_name and value:
    #     if len(value) > 100:
    #         return {"message": "✓ Well-defined career goals", "type": "success"}
    #     else:
    #         return {"message": "Consider expanding on your goals", "type": "info"}

    # # Password validation
    # if 'password' in field_name:
    #     if len(value) >= 12:
    #         return {"message": "✓ Strong password", "type": "success"}
    #     elif len(value) >= 8:
    #         return {"message": "Good password length", "type": "info"}
    #     elif value:
    #         return {"message": "Password should be at least 8 characters", "type": "warning"}

    # # Confirm password validation
    # if 'confirm' in field_name and 'password' in field_name:
    #     return {"message": "Make sure passwords match", "type": "info"}

    # # Company name validation
    # if 'company' in field_name and 'name' in field_name:
    #     if len(value) > 3:
    #         return {"message": "✓ Company name looks good", "type": "success"}
    #     elif value:
    #         return {"message": "Company name seems short", "type": "info"}

    # # Website validation
    # if 'website' in field_name:
    #     if value and ('http' in value or 'www' in value):
    #         return {"message": "✓ Valid website format", "type": "success"}
    #     elif value:
    #         return {"message": "Include http:// or https://", "type": "info"}

    # # Industry validation
    # if 'industry' in field_name:
    #     if value:
    #         return {"message": "✓ Industry selected", "type": "success"}

    # # Company description validation
    # if 'company_description' in field_name or 'description' in field_name:
    #     if len(value) > 150:
    #         return {"message": "✓ Detailed company description", "type": "success"}
    #     elif len(value) > 50:
    #         return {"message": "Good description, consider adding more detail", "type": "info"}
    #     elif value:
    #         return {"message": "Add more details about your company", "type": "info"}

    return None  # No validation message
