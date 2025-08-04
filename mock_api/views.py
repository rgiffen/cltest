from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def create_user(request):
    return JsonResponse({"status": "success", "message": "User created"})

@csrf_exempt
def update_profile(request, user_id):
    return JsonResponse({"status": "success", "message": f"Profile updated for user {user_id}"})

@csrf_exempt
def verify_auth(request):
    return JsonResponse({"status": "success", "verified": True})

@csrf_exempt
def update_skills(request, user_id):
    return JsonResponse({"status": "success", "message": f"Skills updated for user {user_id}"})

@csrf_exempt
def get_matches(request, project_id):
    return JsonResponse({"matches": [], "count": 0})

@csrf_exempt
def semantic_match(request):
    return JsonResponse({"matches": [], "similarity_scores": []})

@csrf_exempt
def match_evidence(request):
    return JsonResponse({"evidence": "Mock matching evidence"})

@csrf_exempt
def parse_document(request):
    return JsonResponse({"status": "success", "parsed_data": {}})

@csrf_exempt
def store_document(request):
    return JsonResponse({"status": "success", "document_id": "mock_doc_123"})

@csrf_exempt
def highlight_document(request):
    return JsonResponse({"highlights": []})

@csrf_exempt
def analyze_employer(request):
    return JsonResponse({"analysis": "Mock employer analysis"})

@csrf_exempt
def analyze_project(request):
    return JsonResponse({"analysis": "Mock project analysis"})

@csrf_exempt
def generate_questions(request):
    return JsonResponse({"questions": ["Mock question 1", "Mock question 2"]})

@csrf_exempt
def validate_responses(request):
    if request.method == 'POST':
        field_name = request.POST.get('field_name', '')
        field_value = request.POST.get('field_value', '')
        
        # AI validation logic based on field and value
        validation_result = get_ai_validation(field_name, field_value)
        return JsonResponse({"validation": validation_result})
    
    return JsonResponse({"validation": {"status": "valid", "suggestions": []}})

def get_ai_validation(field_name, value):
    """Simulate AI validation with contextual responses"""
    value = value.strip().lower()
    
    # Email validation
    if 'email' in field_name:
        if value and '@mun.ca' in value:
            return {"message": "✓ University email detected", "type": "success"}
        elif value and '@' in value:
            return {"message": "Consider using your university email", "type": "info"}
    
    # Name validation
    if 'name' in field_name:
        if value and len(value.split()) >= 2:
            return {"message": "✓ Looks good!", "type": "success"}
        elif value:
            return {"message": "Consider including your full name", "type": "info"}
    
    # Program validation
    if 'program' in field_name:
        if 'computer' in value or 'engineering' in value:
            return {"message": "Great! I can suggest relevant skills", "type": "info"}
        elif 'science' in value:
            return {"message": "STEM programs have high demand", "type": "success"}
    
    # Academic year validation
    if 'academic' in field_name:
        if value in ['junior', 'senior', 'graduate']:
            return {"message": "✓ Good experience level for projects", "type": "success"}
    
    # Phone validation
    if 'phone' in field_name:
        if '709' in value:
            return {"message": "✓ Newfoundland number detected", "type": "success"}
        elif value and len(value) >= 10:
            return {"message": "✓ Valid phone format", "type": "success"}
    
    # Skills validation
    if 'skill' in field_name:
        high_demand_skills = ['python', 'javascript', 'react', 'sql', 'java', 'aws', 'docker']
        if any(skill in value for skill in high_demand_skills):
            return {"message": "High demand skill in current market", "type": "success"}
        elif value:
            return {"message": "Consider adding specific frameworks or tools", "type": "info"}
    
    # Availability validation
    if 'availability' in field_name and len(value) > 50:
        return {"message": "✓ Detailed availability info", "type": "success"}
    elif 'availability' in field_name and value:
        return {"message": "Consider adding more details", "type": "info"}
    
    # Career goals validation
    if 'career' in field_name and value:
        if len(value) > 100:
            return {"message": "✓ Well-defined career goals", "type": "success"}
        else:
            return {"message": "Consider expanding on your goals", "type": "info"}
    
    # Password validation
    if 'password' in field_name:
        if len(value) >= 12:
            return {"message": "✓ Strong password", "type": "success"}
        elif len(value) >= 8:
            return {"message": "Good password length", "type": "info"}
        elif value:
            return {"message": "Password should be at least 8 characters", "type": "warning"}
    
    # Confirm password validation
    if 'confirm' in field_name and 'password' in field_name:
        return {"message": "Make sure passwords match", "type": "info"}
    
    # Company name validation
    if 'company' in field_name and 'name' in field_name:
        if len(value) > 3:
            return {"message": "✓ Company name looks good", "type": "success"}
        elif value:
            return {"message": "Company name seems short", "type": "info"}
    
    # Website validation
    if 'website' in field_name:
        if value and ('http' in value or 'www' in value):
            return {"message": "✓ Valid website format", "type": "success"}
        elif value:
            return {"message": "Include http:// or https://", "type": "info"}
    
    # Industry validation
    if 'industry' in field_name:
        if value:
            return {"message": "✓ Industry selected", "type": "success"}
    
    # Company description validation
    if 'company_description' in field_name or 'description' in field_name:
        if len(value) > 150:
            return {"message": "✓ Detailed company description", "type": "success"}
        elif len(value) > 50:
            return {"message": "Good description, consider adding more detail", "type": "info"}
        elif value:
            return {"message": "Add more details about your company", "type": "info"}
    
    return None  # No validation message
