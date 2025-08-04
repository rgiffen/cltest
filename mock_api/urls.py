from django.urls import path
from . import views

app_name = 'mock_api'

urlpatterns = [
    # User Management
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/profile/', views.update_profile, name='update_profile'),
    path('auth/verify/', views.verify_auth, name='verify_auth'),
    
    # Skills & Matching  
    path('users/<int:user_id>/skills/', views.update_skills, name='update_skills'),
    path('projects/<int:project_id>/matches/', views.get_matches, name='get_matches'),
    path('skills/semantic-match/', views.semantic_match, name='semantic_match'),
    path('matches/evidence/', views.match_evidence, name='match_evidence'),
    
    # Document Processing
    path('documents/parse/', views.parse_document, name='parse_document'),
    path('documents/store/', views.store_document, name='store_document'),
    path('documents/highlight/', views.highlight_document, name='highlight_document'),
    
    # Content Analysis & AI Questions
    path('content/analyze-employer/', views.analyze_employer, name='analyze_employer'),
    path('content/analyze-project/', views.analyze_project, name='analyze_project'),
    path('content/generate-questions/', views.generate_questions, name='generate_questions'),
    path('content/validate-responses/', views.validate_responses, name='validate_responses'),
]