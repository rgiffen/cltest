from django.urls import path

from . import views

app_name = 'web'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('register/student/', views.student_account_creation, name='student_register'),
    path('register/student/account/', views.create_student_account, name='create_student_account'),
    path('register/student/profile/', views.student_profile_setup, name='student_profile_setup'),
    path('register/student/process/', views.process_student_registration, name='process_student_registration'),
    path('register/employer/', views.employer_register, name='employer_register'),
    path('register/employer/process/', views.process_employer_registration, name='process_employer_registration'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/', views.verify_email, name='verify_email'),

    # Student dashboard and profile
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/projects/', views.browse_projects, name='browse_projects'),

    # Employer dashboard
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employer/projects/', views.employer_projects, name='employer_projects'),
    path('employer/projects/create/', views.create_project, name='create_project'),
    path('employer/projects/<int:project_id>/matches/', views.project_matches, name='project_matches'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve-employer/<int:employer_id>/', views.approve_employer, name='approve_employer'),
    path('admin/reject-employer/<int:employer_id>/', views.reject_employer, name='reject_employer'),
]
