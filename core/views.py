from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, StudentProfile, EmployerProfile, Education, Employment, Skill
import json
import random

def home(request):
    # If user is already logged in, redirect to appropriate dashboard
    if request.user.is_authenticated:
        # Handle admin users and users without user_type
        if not hasattr(request.user, 'user_type') or not request.user.user_type:
            if request.user.is_staff or request.user.is_superuser:
                # Admin users can stay on home page or redirect to admin
                return render(request, 'auth_choice.html', {
                    'show_admin_link': True,
                    'user': request.user
                })
            else:
                # Regular users without user_type should choose their role
                return redirect('core:register')
                
        # Handle regular users with user_type
        if request.user.user_type == 'student':
            try:
                request.user.student_profile
                return redirect('core:student_dashboard')
            except StudentProfile.DoesNotExist:
                return redirect('core:student_register')
        elif request.user.user_type == 'employer':
            return redirect('core:employer_dashboard')
    
    # Show auth choice for anonymous users
    return render(request, 'auth_choice.html')

def register(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('core:home')
    
    return render(request, 'register_choice.html')

def student_account_creation(request):
    """Step 1: Account creation with email and password"""
    # If user is already logged in, check if they need to complete their profile
    if request.user.is_authenticated:
        if request.user.user_type == 'student':
            # Check if they have a complete profile
            try:
                profile = request.user.student_profile
                return redirect('core:student_dashboard')
            except StudentProfile.DoesNotExist:
                # User exists but needs to complete profile - redirect to profile setup
                return redirect('core:student_profile_setup')
        else:
            # Not a student, redirect to appropriate place
            return redirect('core:home')
    
    return render(request, 'student_account_creation.html')

def student_profile_setup(request):
    """Step 2: Profile setup wizard (after account creation)"""
    # Check if user is authenticated and is a student
    if not request.user.is_authenticated:
        return redirect('core:student_register')
    
    if request.user.user_type != 'student':
        return redirect('core:home')
    
    # Check if profile already exists
    try:
        profile = request.user.student_profile
        return redirect('core:student_dashboard')
    except StudentProfile.DoesNotExist:
        # Show profile setup wizard
        return render(request, 'student_registration.html')

@require_http_methods(["POST"])
def process_student_registration(request):
    """Handle the profile creation steps (after account is created)"""
    current_step = int(request.POST.get('current_step', 1))
    
    if current_step == 7:  # Final step - create complete profile
        return create_student_profile(request)
    
    # For other steps, just return success (client-side navigation)
    return JsonResponse({'status': 'success', 'step': current_step})

def create_student_profile(request):
    """Create the complete student profile after account exists"""
    try:
        # User should already be authenticated at this point
        if not request.user.is_authenticated or request.user.user_type != 'student':
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid session. Please start over.'
            })
        
        user = request.user
        
        # Check if profile already exists
        if hasattr(user, 'student_profile'):
            return JsonResponse({
                'status': 'error',
                'message': 'Profile already exists.'
            })
        
        # Create student profile
        profile = StudentProfile.objects.create(
            user=user,
            phone=request.POST.get('phone', ''),
            academic_year=request.POST.get('academic_year', ''),
            program=request.POST.get('program', ''),
            currently_available=request.POST.get('currently_available', ''),
            available_date=request.POST.get('available_date') or None,
            availability_notes=request.POST.get('availability_notes', ''),
            remote_preference=request.POST.get('remote_preference', ''),
            location_flexibility=request.POST.get('location_flexibility', ''),
            career_goals=request.POST.get('career_goals', ''),
            additional_info=request.POST.get('additional_info', ''),
            availability=request.POST.getlist('availability'),
            profile_complete=True
        )
        
        # Create education entries
        education_count = 0
        while f'education_institution_{education_count}' in request.POST:
            institution = request.POST.get(f'education_institution_{education_count}')
            if institution:
                Education.objects.create(
                    student=profile,
                    institution=institution,
                    degree=request.POST.get(f'education_degree_{education_count}', ''),
                    field_of_study=request.POST.get(f'education_field_{education_count}', ''),
                    gpa=request.POST.get(f'education_gpa_{education_count}') or None,
                    start_date=request.POST.get(f'education_start_{education_count}') or None,
                    end_date=request.POST.get(f'education_end_{education_count}') or None,
                    is_current=bool(request.POST.get(f'education_current_{education_count}'))
                )
            education_count += 1
        
        # Create employment entries
        employment_count = 0
        while f'employment_company_{employment_count}' in request.POST:
            company = request.POST.get(f'employment_company_{employment_count}')
            if company:
                Employment.objects.create(
                    student=profile,
                    company=company,
                    position=request.POST.get(f'employment_position_{employment_count}', ''),
                    start_date=request.POST.get(f'employment_start_{employment_count}') or None,
                    end_date=request.POST.get(f'employment_end_{employment_count}') or None,
                    description=request.POST.get(f'employment_description_{employment_count}', ''),
                    is_current=bool(request.POST.get(f'employment_current_{employment_count}'))
                )
            employment_count += 1
        
        # Create skill entries
        skill_count = 0
        while f'skill_name_{skill_count}' in request.POST:
            skill_name = request.POST.get(f'skill_name_{skill_count}')
            if skill_name:
                Skill.objects.create(
                    student=profile,
                    name=skill_name,
                    level=request.POST.get(f'skill_level_{skill_count}', 'beginner'),
                    experience_description=request.POST.get(f'skill_description_{skill_count}', '')
                )
            skill_count += 1
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Profile created successfully!',
            'redirect': '/student/dashboard/'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating profile: {str(e)}'
        })

@require_http_methods(["POST"])
def create_student_account(request):
    """Create student account with email/password validation"""
    try:
        # Get form data
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validate @mun.ca email
        if not email.endswith('@mun.ca'):
            return JsonResponse({
                'status': 'error',
                'message': 'Only @mun.ca email addresses are accepted for student accounts.'
            })
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'An account with this email already exists. Please sign in instead.'
            })
        
        # Validate required fields
        if not all([email, password, first_name, last_name]):
            return JsonResponse({
                'status': 'error',
                'message': 'All fields are required.'
            })
        
        # Validate password
        if len(password) < 8:
            return JsonResponse({
                'status': 'error',
                'message': 'Password must be at least 8 characters long.'
            })
        
        if password != confirm_password:
            return JsonResponse({
                'status': 'error',
                'message': 'Passwords do not match.'
            })
        
        # Create user account
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type='student'
        )
        
        # Log the user in
        login(request, user)
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Account created successfully!',
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating account: {str(e)}'
        })

def employer_register(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('core:home')
    
    return render(request, 'employer_registration.html')

@require_http_methods(["POST"])
def process_employer_registration(request):
    current_step = int(request.POST.get('current_step', 1))
    
    if current_step == 4:  # Final step - create employer account
        return create_employer_account(request)
    
    # For other steps, just return success (client-side navigation)
    return JsonResponse({'status': 'success', 'step': current_step})

def create_employer_account(request):
    try:
        # Check if email already exists
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'An account with this email already exists. Please sign in instead.'
            })
        
        # Get and validate password
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not password or len(password) < 8:
            return JsonResponse({
                'status': 'error',
                'message': 'Password must be at least 8 characters long.'
            })
        
        if password != confirm_password:
            return JsonResponse({
                'status': 'error',
                'message': 'Passwords do not match.'
            })
        
        # Create user
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            password=password,
            user_type='employer'
        )
        
        # Create employer profile
        profile = EmployerProfile.objects.create(
            user=user,
            company_name=request.POST.get('company_name'),
            industry=request.POST.get('industry'),
            website=request.POST.get('website', ''),
            company_description=request.POST.get('company_description'),
            company_location=request.POST.get('company_location'),
            contact_name=request.POST.get('contact_name'),
            contact_title=request.POST.get('contact_title'),
            contact_phone=request.POST.get('contact_phone', ''),
            approval_status='pending'  # Requires admin approval
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Your registration has been submitted for review. You will receive an email notification once approved.',
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating account: {str(e)}'
        })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            # Try to find user by email (which is used as username)
            try:
                user = User.objects.get(email=email)
                # Authenticate using username and password
                auth_user = authenticate(request, username=user.username, password=password)
                
                if auth_user:
                    login(request, auth_user)
                    messages.success(request, f'Welcome back, {auth_user.get_full_name()}!')
                    
                    # Redirect based on user type
                    if auth_user.user_type == 'student':
                        return redirect('core:student_dashboard')
                    elif auth_user.user_type == 'employer':
                        return redirect('core:employer_dashboard')
                    else:
                        return redirect('core:home')
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
        else:
            messages.error(request, 'Please provide both email and password.')
    
    return render(request, 'login.html')

def logout_view(request):
    if request.user.is_authenticated:
        name = request.user.get_full_name()
        logout(request)
        messages.success(request, f'Successfully signed out. See you later, {name}!')
    
    return redirect('core:home')

def verify_email(request):
    return HttpResponse("Email Verification")

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        logout(request)
        return redirect('core:login')
    
    try:
        profile = request.user.student_profile
        return render(request, 'student_dashboard.html', {'profile': profile})
    except StudentProfile.DoesNotExist:
        messages.info(request, 'Please complete your student profile.')
        return redirect('core:student_register')

@login_required
def student_profile(request):
    return HttpResponse("Student Profile")

@login_required
def employer_dashboard(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employer':
        messages.error(request, 'Access denied. Employer account required.')
        return redirect('core:login')
    
    try:
        profile = request.user.employer_profile
        
        # Check approval status
        if profile.approval_status != 'approved':
            return render(request, 'employer_pending.html', {'profile': profile})
        
        # Get projects for approved employers
        projects = profile.projects.all().order_by('-created_at')
        
        return render(request, 'employer_dashboard.html', {
            'profile': profile,
            'projects': projects
        })
        
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer registration.')
        return redirect('core:employer_register')

@login_required
def create_project(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employer':
        messages.error(request, 'Access denied. Employer account required.')
        return redirect('core:login')
    
    try:
        profile = request.user.employer_profile
        
        # Check if employer is approved
        if profile.approval_status != 'approved':
            messages.warning(request, 'Your account must be approved before you can post projects.')
            return redirect('core:employer_dashboard')
        
        if request.method == 'POST':
            return process_project_creation(request, profile)
        
        return render(request, 'create_project.html', {'profile': profile})
        
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer registration.')
        return redirect('core:employer_register')

def process_project_creation(request, profile):
    try:
        # Collect required skills
        required_skills = []
        skill_index = 0
        while f'required_skills_{skill_index}' in request.POST:
            skill = request.POST.get(f'required_skills_{skill_index}', '').strip()
            if skill:
                required_skills.append(skill)
            skill_index += 1
        
        # Collect preferred skills
        preferred_skills = []
        skill_index = 0
        while f'preferred_skills_{skill_index}' in request.POST:
            skill = request.POST.get(f'preferred_skills_{skill_index}', '').strip()
            if skill:
                preferred_skills.append(skill)
            skill_index += 1
        
        # Handle preferred programs
        preferred_programs_str = request.POST.get('preferred_programs', '')
        preferred_programs = [p.strip() for p in preferred_programs_str.split(',') if p.strip()] if preferred_programs_str else []
        
        # Create project
        from .models import Project
        project = Project.objects.create(
            employer=profile,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            project_type=request.POST.get('project_type'),
            duration=request.POST.get('duration'),
            work_type=request.POST.get('work_type'),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_academic_year=request.POST.get('min_academic_year', ''),
            preferred_programs=preferred_programs,
            is_active=True
        )
        
        messages.success(request, f'Project "{project.title}" has been posted successfully!')
        return redirect('core:employer_dashboard')
        
    except Exception as e:
        messages.error(request, f'Error creating project: {str(e)}')
        return render(request, 'create_project.html', {'profile': profile})

@login_required
def project_matches(request, project_id):
    """Show student matches for a specific project"""
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employer':
        messages.error(request, 'Access denied. Employer account required.')
        return redirect('core:login')
    
    try:
        profile = request.user.employer_profile
        if profile.approval_status != 'approved':
            messages.warning(request, 'Your account must be approved to view matches.')
            return redirect('core:employer_dashboard')
        
        # Get project and verify ownership
        from .models import Project
        project = Project.objects.get(id=project_id, employer=profile)
        
        # Get matches using our matching algorithm
        from .matching import get_project_matches
        matches = get_project_matches(project_id)
        
        return render(request, 'project_matches.html', {
            'project': project,
            'matches': matches,
            'profile': profile
        })
        
    except Project.DoesNotExist:
        messages.error(request, 'Project not found or you do not have permission to view it.')
        return redirect('core:employer_dashboard')
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer registration.')
        return redirect('core:employer_register')

@login_required
def browse_projects(request):
    """Show projects that match the current student"""
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('core:login')
    
    try:
        student_profile = request.user.student_profile
        
        # Get project matches using our matching algorithm
        from .matching import get_student_projects
        project_matches = get_student_projects(student_profile)
        
        return render(request, 'browse_projects.html', {
            'student_profile': student_profile,
            'project_matches': project_matches
        })
        
    except StudentProfile.DoesNotExist:
        messages.info(request, 'Please complete your student profile.')
        return redirect('core:student_register')

@login_required
def employer_projects(request):
    return HttpResponse("Employer Projects")

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with employer approval management"""
    from .models import EmployerProfile, Project, StudentProfile
    
    # Get pending employer approvals
    pending_employers = EmployerProfile.objects.filter(approval_status='pending').order_by('-created_at')
    approved_employers = EmployerProfile.objects.filter(approval_status='approved').order_by('-created_at')[:5]
    
    # Get platform statistics
    total_students = StudentProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(is_active=True).count()
    
    context = {
        'pending_employers': pending_employers,
        'approved_employers': approved_employers,
        'stats': {
            'total_students': total_students,
            'total_employers': total_employers,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'pending_approvals': pending_employers.count()
        }
    }
    
    return render(request, 'admin_dashboard.html', context)

@staff_member_required
@require_http_methods(["POST"])
def approve_employer(request, employer_id):
    """Approve a pending employer"""
    try:
        employer = EmployerProfile.objects.get(id=employer_id, approval_status='pending')
        employer.approval_status = 'approved'
        employer.save()
        
        messages.success(request, f'Employer "{employer.company_name}" has been approved.')
        return JsonResponse({'status': 'success', 'message': 'Employer approved successfully'})
        
    except EmployerProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Employer not found or already processed'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@staff_member_required
@require_http_methods(["POST"])
def reject_employer(request, employer_id):
    """Reject a pending employer"""
    try:
        employer = EmployerProfile.objects.get(id=employer_id, approval_status='pending')
        reason = request.POST.get('reason', 'No reason provided')
        
        employer.approval_status = 'rejected'
        employer.rejection_reason = reason
        employer.save()
        
        messages.success(request, f'Employer "{employer.company_name}" has been rejected.')
        return JsonResponse({'status': 'success', 'message': 'Employer rejected'})
        
    except EmployerProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Employer not found or already processed'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
