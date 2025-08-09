from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Education,
    EmployerProfile,
    Employment,
    Project,
    Reference,
    Skill,
    StudentProfile,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'email_verified', 'is_staff')
    list_filter = ('user_type', 'email_verified', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'email_verified', 'verification_code')
        }),
    )

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'academic_year', 'profile_complete')
    list_filter = ('academic_year', 'profile_complete', 'university')
    search_fields = ('user__username', 'user__email', 'program')

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_name', 'approval_status', 'created_at')
    list_filter = ('approval_status', 'industry')
    search_fields = ('company_name', 'contact_name', 'user__email')
    actions = ['approve_employers', 'reject_employers']

    def approve_employers(self, request, queryset):
        queryset.update(approval_status='approved')
    approve_employers.short_description = "Approve selected employers"

    def reject_employers(self, request, queryset):
        queryset.update(approval_status='rejected')
    reject_employers.short_description = "Reject selected employers"

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('student', 'degree', 'institution', 'start_date', 'is_current')
    list_filter = ('is_current', 'institution')

@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'position', 'company', 'start_date', 'is_current')
    list_filter = ('is_current', 'company')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('student', 'name', 'level')
    list_filter = ('level',)
    search_fields = ('name', 'student__user__username')

@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('student', 'name', 'position', 'company')
    search_fields = ('name', 'company', 'student__user__username')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'project_type', 'duration', 'is_active')
    list_filter = ('project_type', 'duration', 'work_type', 'is_active')
    search_fields = ('title', 'employer__company_name')
