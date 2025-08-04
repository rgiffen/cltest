# Student-Employer Skills Matching Platform

Build a responsive web application that connects students with employers based on project skill requirements. Students register their skills and availability, employers describe projects, and the platform provides AI-powered matching.

**Note**: These instructions provide a comprehensive starting point, but please ask questions or suggest alternative approaches if you see opportunities for improvement, have concerns about any design decisions, or need clarification on requirements. Your expertise in suggesting better patterns, libraries, or architectural choices is valued and encouraged.

## Technology Stack
- **Backend**: Django 5
- **Frontend**: Bootstrap 5 + HTMX 2
- **Database**: MySQL for now, PostgreSQL later (with plans for vector/graph DB integration)
- **Authentication**: Django auth + social login + email verification
- **File Processing**: Support PDF, DOCX, plain text, markdown

## Core Requirements

### Authentication System
- Email-based registration with verification required
- Student registrations limited to @mun.ca email domains
- Email verification codes for both registration and login (2FA style)
- Social login integration (Google, LinkedIn)
- Django's built-in User model extended with profiles

### User Types & Profiles

#### Student Profile
- **Resume Upload**: Auto-parse and pre-populate profile data for confirmation
- **Basic Info**: Name, email, phone, academic year, university, program/major
- **Education History**: List of - Institution, Degree/Program, Field of study, GPA (Optional), Start date, End date
- **Employment**: List of - Company/Organization, Position Title, Start date, End date, Description
- **Skills**: List of - Self-reported skills with description of Experience and Context
- **References** List of - Name, Position, Company, Skill Endorsements
- **Availability Options**:
  - Predefined slots: Weekends, Evenings, Summer break, Part-time during semester, Full-time co-op
  - Currently available (boolean)
  - Available as of specific date
  - Free-form availability notes
- **Preferences**: Remote work preference, location flexibility, Preferred Project Types, Career Goals, Additional Information

#### Employer Profile
- **Company Info**: Name, location, industry, website, description
- **Contact Person**: Name, title, email, phone
- **Approval Status**: Pending/Approved/Rejected (admin controlled)
- **Verification**: LLM-assisted screening for approval process

### Project Management
- **Project Creation**: Employers describe projects for AI matching only
- **Required Fields**: Project title, description, required skills, project type, duration, remote/on-site
- **AI Processing**: Use business operations platform to analyze project requirements
- **Matching Results**: Ranked list of suitable students with match explanations

### Admin Experience
1. **Dashboard**: Key metrics, pending approvals, system health
2. **User Management**: Approve employers, manage student accounts
3. **Content Review**: Monitor project descriptions, handle reports
4. **Analytics**: Usage patterns, matching effectiveness, user feedback


### Business Operations Platform Integration

#### Mock API Endpoints (for development)
Create a mock API service with these endpoints:

```python
# User Management
POST /api/users/create
PUT /api/users/{user_id}/profile
POST /api/auth/verify

# Skills & Matching  
POST /api/users/{user_id}/skills
POST /api/projects/{project_id}/matches
POST /api/skills/semantic-match
POST /api/matches/evidence  # Generate detailed evidence for matches

# Document Processing
POST /api/documents/parse
POST /api/documents/store
POST /api/documents/highlight  # Get specific text sections with positions

# Content Analysis & AI Questions
POST /api/content/analyze-employer
POST /api/content/analyze-project
POST /api/content/generate-questions
POST /api/content/validate-responses
```

## Application Structure

### Apps to Create
1. **core** - All UI, models, views, templates for the main application (users, students, employers, projects, matching, admin dashboard)
2. **mock_api** - Business operations platform mock implementation and integration layer

### Key Models

#### User Extensions
```python
# core/models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(choices=[('student', 'Student'), ('employer', 'Employer')])
    phone = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(choices=[('registration', 'Registration'), ('login', 'Login')])
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
```

#### Student Models
```python
# core/models.py (continued)
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)
    program = models.CharField(max_length=100)
    currently_available = models.BooleanField(default=False)
    available_from_date = models.DateField(null=True, blank=True)
    availability_notes = models.TextField(blank=True)
    remote_preference = models.CharField(choices=[...])
    
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)  # Programming, Design, etc.

class StudentSkill(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.CharField(choices=[('beginner', 'Beginner'), ...])
    
class AvailabilitySlot(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    slot_type = models.CharField(choices=[('weekends', 'Weekends'), ...])

class AIQuestion(models.Model):
    content_object = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    question_text = models.TextField()
    question_type = models.CharField(choices=[
        ('clarification', 'Needs Clarification'),
        ('enhancement', 'Suggested Enhancement'), 
        ('verification', 'Please Verify'),
        ('missing_info', 'Missing Information')
    ])
    field_reference = models.CharField(max_length=100, blank=True)  # Which field triggered this
    priority = models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    
    answered = models.BooleanField(default=False)
    answer_text = models.TextField(blank=True)
    dismissed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Employer & Project Models
```python
# core/models.py (continued)
class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    description = models.TextField()
    approval_status = models.CharField(choices=[('pending', 'Pending'), ...])
    llm_screening_result = models.JSONField(null=True, blank=True)

# core/models.py (continued)
class Project(models.Model):
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    project_type = models.CharField(max_length=50)
    duration = models.CharField(max_length=100)
    is_remote = models.BooleanField()
    required_skills = models.ManyToManyField(Skill, through='ProjectSkill')
    
class ProjectMatch(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    match_score = models.FloatField()
    match_explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class MatchEvidence(models.Model):
    """Stores specific evidence supporting a match with document references"""
    match = models.ForeignKey(ProjectMatch, on_delete=models.CASCADE, related_name='evidence')
    evidence_type = models.CharField(choices=[
        ('skill_mention', 'Skill Mention'),
        ('project_experience', 'Project Experience'), 
        ('education', 'Education'),
        ('achievement', 'Achievement'),
        ('availability', 'Availability')
    ])
    evidence_text = models.TextField()  # The actual text that supports the match
    confidence_score = models.FloatField()  # How confident AI is in this evidence
    
    # Document reference fields
    source_document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    document_section = models.CharField(max_length=100, blank=True)  # e.g., "experience", "skills"
    text_start_position = models.IntegerField(null=True, blank=True)  # Character position in document
    text_end_position = models.IntegerField(null=True, blank=True)
    page_number = models.IntegerField(null=True, blank=True)  # For PDFs
    
    created_at = models.DateTimeField(auto_now_add=True)
```

## Key Features Implementation

### 1. Registration Flow
- **Student Registration**: 
  - Email validation (@mun.ca only)
  - Send verification code
  - Smart multi-step form: Resume upload → AI parsing & prefill → Confirm/edit basic info → Confirm/edit skills → Set availability
  - HTMX for smooth step transitions and real-time parsing feedback
- **Employer Registration**:
  - Company information form
  - Automatic LLM screening
  - Admin approval required

### AI-Powered Form Intelligence

#### Smart Verification & Questions System
- **AI-Generated Field Validation**: Beyond standard form validation, AI analyzes content and generates contextual questions/suggestions
- **Adaptive Questioning**: AI asks follow-up questions based on incomplete or ambiguous information
- **Progressive Disclosure**: Additional fields appear based on AI analysis of existing content

#### For Students:
- **Resume Analysis Questions (examples)**: 
  - "I see you mention 'database experience' - could you specify which databases? (SQL Server, MongoDB, etc.)"
  - "Your resume shows leadership roles - would you like to add 'Team Leadership' to your skills?"
  - "I notice a gap between 2022-2023 - were you studying, working, or taking a break?"
- **Skill Verification (examples)**: 
  - "You listed 'Advanced Python' - I see you've worked with Flask. Have you used Django or FastAPI?"
  - "Your portfolio shows React projects - should I add 'Frontend Development' and 'JavaScript' to your skills?"

#### For Employers:
- **Project Clarification Questions (examples)**:
  - "Your project mentions 'web development' - are you looking for frontend, backend, or full-stack developers?"
  - "You need someone 'ASAP' - what's your preferred project duration? (days, weeks, months)"
  - "I see you want 'database skills' - what type of data will they be working with?"
- **Requirements Refinement (examples)**:
  - "Based on your description, you might also benefit from students with 'UI/UX Design' skills - should I include this in the search?"
  - "Your project seems suitable for remote work - should I include remote-only students in matches?"
- **Missing Information Alert (examples)**:
  - "To improve matches, consider adding: expected time commitment, preferred experience level, or project timeline"

#### Implementation Approach:
- **Real-time Analysis**: As users type or upload content, AI analyzes in background
- **Contextual Prompts**: Questions appear as expandable cards below relevant fields
- **Optional Enhancement**: Users can skip AI suggestions but get better matches by engaging
- **Learning System**: Track which questions lead to better matches to improve question generation
- File upload with drag-and-drop interface
- Parse PDF/DOCX/TXT/MD files to extract:
  - Skills mentioned
  - Education details
  - Work experience
  - Contact information
- Pre-populate profile fields for user confirmation

### 2. Document Processing
- Comprehensive skill taxonomy (auto-complete search)
- Proficiency level selection
- Skill suggestions based on resume parsing
- Category organization (Technical, Soft Skills, Industry-specific)

### 3. Skills Management
- Weighted scoring based on:
  - Skill matches (exact + semantic)
  - Proficiency levels
  - Availability alignment
  - Project type preferences
- LLM-powered semantic matching
- Explanation generation for match reasoning

### 4. Matching Algorithm
- **Activity Metrics**:
  - User registrations (students/employers)
  - Project postings
  - Successful matches/contacts
  - Popular skills
- **Approval Management**:
  - Employer review queue
  - LLM screening results
  - Bulk approval actions
- **Content Moderation**:
  - Project content review
  - User-reported issues

### 5. Admin Dashboard
- Mobile-first Bootstrap 5 implementation
- Optimized forms for mobile devices
- Progressive web app features
- Touch-friendly interfaces

### 6. Responsive Design

### Student Journey
1. **Registration**: Email → Verification → Resume upload → Review AI-parsed data → Confirm basic info → Confirm skills → Set availability
2. **Dashboard**: Profile completeness, skill gaps, project matches, contact history
3. **Profile Management**: Update skills, availability, upload new documents

### Employer Journey  
1. **Registration**: Company info → Admin approval → Account activation
2. **Project Creation**: Describe project → AI analysis → View matches
3. **Candidate Review**: Browse matched students with detailed explanations → Review supporting documents → Contact information → Track outreach

#### Rich Match Explanations
- **Detailed Match Breakdown**: Show why each student was selected with specific reasoning
- **Document References**: Clickable links to specific sections of resumes/portfolios that support the match
- **Skill Evidence**: Direct quotes or references from documents that demonstrate required skills
- **Interactive Document Viewer**: Embedded viewer with highlighting of relevant sections
- **Match Confidence**: Visual indicators of match strength with detailed explanations

**Example Match Display**:
```
Sarah Johnson - Strong Match
┌─ Skills Match
│  ✓ Python (Advanced) - mentioned 3 times in resume [View Section]
│  ✓ Django (Intermediate) - described in course project [View Details]
│  ✓ PostgreSQL - database design experience [View Experience]
│
├─ Experience Relevance
│  ✓ Similar project scope - Built student portal for CS department [View Description]
│  ✓ Team experience - Led 4-person capstone team [View Leadership Example]
│
├─ Availability Match
│  ✓ Available immediately
│  ✓ Prefers remote work (matches your requirement)
│
└─ Additional Strengths
   ✓ Strong communication skills - Multiple presentation awards [View Awards]
```

### Admin Experience
1. **Dashboard**: Key metrics, pending approvals, system health
2. **User Management**: Approve employers, manage student accounts
3. **Content Review**: Monitor project descriptions, handle reports
4. **Analytics**: Usage patterns, matching effectiveness, user feedback

## Technical Implementation Notes

**Important**: If you have suggestions for better approaches, alternative libraries, or see potential issues with any of these technical choices, please discuss them before implementation.

### Authentication & Security
- Use Django's `django-allauth` for social authentication
- Implement custom email verification system
- Rate limiting for verification code requests
- CSRF protection on all forms
- Input sanitization and validation

### Performance Considerations
- Database indexing for skill searches
- Caching for frequently accessed match results
- Lazy loading for large skill lists
- Optimized queries for dashboard metrics

### File Processing
- Use `python-docx` for DOCX files
- `PyPDF2` or `pdfplumber` for PDFs  
- Background task processing for large files
- Virus scanning for uploaded documents

### API Integration
- Create abstract base classes for business operations platform
- Mock implementations for development
- Error handling and fallback mechanisms
- Async processing for LLM operations

## Testing Requirements
- Unit tests for all models and core business logic
- Integration tests for API endpoints
- End-to-end tests for user registration flows
- Performance tests for matching algorithm
- Security tests for authentication system

## Deployment Considerations
- Docker containerization
- Environment-specific settings
- Database migrations strategy
- Static file handling
- Email service configuration
- Monitoring and logging setup

Create a fully functional, production-ready application following Django best practices, with comprehensive error handling, logging, and documentation.



UNIVERSITY COLOR PALETTE
============================================================

MAIN COLOR
----------------------------------------
  ████   Pantone 202          RGB(146,  39,  36)  #922724


PRIMARY PALETTE:
----------------------------------------
  ████   COOL GREY 7          RGB(153, 153, 153)  #999999
  ████   COOL GREY 10         RGB( 99, 102, 106)  #63666a
  ████   WARM GREY 6          RGB(169, 160, 149)  #a9a095
  ████   WARM GREY 8          RGB(147, 135, 123)  #93877b
  ████   BLACK                RGB(  0,   0,   0)  #000000
  ████   WHITE                RGB(255, 255, 255)  #ffffff


SECONDARY PALETTE:
----------------------------------------
  ████   RHODAMINE RED        RGB(233,  30, 132)  #e91e84
  ████   PURPLE               RGB(102,  45, 145)  #662d91
  ████   Pantone 3275         RGB(  0, 166, 156)  #00a69c
  ████   YELLOW               RGB(255, 242,   0)  #fff200
  ████   Pantone 185          RGB(237,  41,  57)  #ed2939
  ████   Pantone 3125         RGB(  0, 160, 176)  #00a0b0
  ████   Pantone 2727         RGB(  0, 123, 191)  #007bbf
  ████   Pantone 396          RGB(181, 189,   0)  #b5bd00
  ████   Pantone 1235         RGB(255, 184,  28)  #ffb81c
  ████   Pantone 368          RGB(105, 190,  40)  #69be28
  ████   Pantone 2736         RGB(  0,  56, 147)  #003893
  ████   ORANGE 021           RGB(255,  88,   0)  #ff5800