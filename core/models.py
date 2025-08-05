from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('employer', 'Employer'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, blank=True)
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        if self.user_type == 'student' and self.email:
            if not self.email.endswith('@mun.ca'):
                raise ValidationError({'email': 'Student email must be from @mun.ca domain'})

class StudentProfile(models.Model):
    ACADEMIC_YEAR_CHOICES = [
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('graduate', 'Graduate'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('weekends', 'Weekends'),
        ('evenings', 'Evenings'),
        ('summer', 'Summer Break'),
        ('parttime', 'Part-time during semester'),
        ('coop', 'Full-time co-op'),
    ]
    
    CURRENT_AVAILABILITY_CHOICES = [
        ('yes', 'Yes, immediately'),
        ('no', 'No, not currently'),
        ('limited', 'Limited availability'),
    ]
    
    REMOTE_PREFERENCE_CHOICES = [
        ('remote', 'Fully remote'),
        ('hybrid', 'Hybrid (remote + in-person)'),
        ('onsite', 'On-site only'),
        ('flexible', 'Flexible'),
    ]
    
    LOCATION_FLEXIBILITY_CHOICES = [
        ('local', 'Local area only'),
        ('regional', 'Regional (within state)'),
        ('national', 'National'),
        ('international', 'International'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    # Basic Information
    phone = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=10, choices=ACADEMIC_YEAR_CHOICES, blank=True)
    university = models.CharField(max_length=200, default='Memorial University of Newfoundland')
    program = models.CharField(max_length=200, blank=True)
    
    # Resume
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    
    # External Links/Profiles
    external_links = models.JSONField(default=dict, blank=True)  # Store LinkedIn, GitHub, portfolio URLs
    
    # Documents and Links (from Step 8)
    documents = models.JSONField(default=list, blank=True)  # Store document information
    profile_links = models.JSONField(default=list, blank=True)  # Store external links with metadata
    
    # Availability
    availability = models.JSONField(default=list, blank=True)  # Store selected availability options
    currently_available = models.CharField(max_length=10, choices=CURRENT_AVAILABILITY_CHOICES, blank=True)
    available_date = models.DateField(blank=True, null=True)
    availability_notes = models.TextField(blank=True)
    
    # Preferences
    remote_preference = models.CharField(max_length=10, choices=REMOTE_PREFERENCE_CHOICES, blank=True)
    location_flexibility = models.CharField(max_length=15, choices=LOCATION_FLEXIBILITY_CHOICES, blank=True)
    career_goals = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)
    
    # Profile completion
    profile_complete = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.program}"

class Education(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.degree} in {self.field_of_study} - {self.institution}"

class Employment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='employment')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.position} at {self.company}"

class Skill(models.Model):
    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=15, choices=SKILL_LEVEL_CHOICES)
    experience_description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.level})"

class Reference(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='references')
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    skill_endorsements = models.TextField(blank=True, help_text="Skills this reference can endorse")
    
    def __str__(self):
        return f"{self.name} - {self.position} at {self.company}"

class EmployerProfile(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    
    # Company Information
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    company_description = models.TextField()
    company_location = models.CharField(max_length=200)
    
    # Contact Person
    contact_name = models.CharField(max_length=200)
    contact_title = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Approval
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_employers')
    approved_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company_name} - {self.approval_status}"

class Project(models.Model):
    PROJECT_TYPE_CHOICES = [
        ('web_dev', 'Web Development'),
        ('mobile_app', 'Mobile App'),
        ('data_analysis', 'Data Analysis'),
        ('research', 'Research'),
        ('design', 'Design'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]
    
    DURATION_CHOICES = [
        ('1-2_weeks', '1-2 weeks'),
        ('1_month', '1 month'),
        ('2-3_months', '2-3 months'),
        ('3-6_months', '3-6 months'),
        ('6+_months', '6+ months'),
    ]
    
    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
    ]
    
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='projects')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES)
    duration = models.CharField(max_length=15, choices=DURATION_CHOICES)
    work_type = models.CharField(max_length=10, choices=WORK_TYPE_CHOICES)
    
    required_skills = models.JSONField(default=list)  # Store list of required skills
    preferred_skills = models.JSONField(default=list)  # Store list of preferred skills
    
    # Additional requirements
    min_academic_year = models.CharField(max_length=10, choices=StudentProfile.ACADEMIC_YEAR_CHOICES, blank=True)
    preferred_programs = models.JSONField(default=list)  # Store list of preferred academic programs
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.employer.company_name}"
