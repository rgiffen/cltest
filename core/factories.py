# type: ignore
"""
Test data factories for creating consistent test objects

This module uses factory_boy to create test data with realistic defaults
and relationships. Factories help maintain test isolation and reduce
boilerplate code in test setup.
"""

from collections.abc import Sequence
from datetime import date, timedelta

import factory  # type: ignore[import-untyped]
from django.contrib.auth import get_user_model
from factory import Faker, SubFactory, django  # type: ignore[import-untyped]

from .models import (
    Education,
    EmployerProfile,
    Employment,
    Project,
    Reference,
    Skill,
    StudentProfile,
)

User = get_user_model()


class UserFactory(django.DjangoModelFactory):
    """Factory for creating User instances"""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = True
    user_type = "student"


class StudentUserFactory(UserFactory):
    """Factory for creating Student User instances with @mun.ca email"""

    email = factory.LazyAttribute(lambda obj: f"{obj.username}@mun.ca")
    user_type = "student"


class EmployerUserFactory(UserFactory):
    """Factory for creating Employer User instances"""

    email = factory.LazyAttribute(lambda obj: f"{obj.username}@company.com")
    user_type = "employer"


class StudentProfileFactory(django.DjangoModelFactory):
    """Factory for creating StudentProfile instances"""

    class Meta:
        model = StudentProfile

    user = SubFactory(StudentUserFactory)
    phone = Faker("phone_number")

    academic_year = factory.Iterator(
        ["freshman", "sophomore", "junior", "senior", "graduate"]
    )

    university = "Memorial University of Newfoundland"
    program = factory.Iterator(
        [
            "Computer Science",
            "Software Engineering",
            "Information Technology",
            "Computer Engineering",
            "Data Science",
            "Mathematics",
        ]
    )

    currently_available = factory.Iterator(["yes", "no", "limited"])

    remote_preference = factory.Iterator(["remote", "onsite", "hybrid", "flexible"])

    location_flexibility = factory.Iterator(
        ["local", "regional", "national", "international"]
    )

    career_goals = Faker("text", max_nb_chars=500)
    additional_info = Faker("text", max_nb_chars=300)

    @factory.post_generation
    def skills(
        self,
        create: bool,
        extracted: Sequence[Skill] | None,
        **kwargs: dict[str, object],
    ) -> None:
        """Add skills to the student profile after creation"""
        if not create:
            return

        if extracted:
            # Skills are already associated via ForeignKey, no need to add
            pass
        else:
            # Add 3-5 random skills by default
            import random

            skill_count = random.randint(3, 5)
            for _ in range(skill_count):
                SkillFactory.create(student=self)


class SkillFactory(django.DjangoModelFactory):
    """Factory for creating Skill instances"""

    class Meta:
        model = Skill
        django_get_or_create = ("name", "student")  # Avoid duplicates per student

    student = SubFactory(StudentProfileFactory)
    name = factory.Iterator(
        [
            "Python",
            "Django",
            "JavaScript",
            "React",
            "SQL",
            "PostgreSQL",
            "Git",
            "Docker",
            "AWS",
            "Machine Learning",
            "Data Analysis",
            "HTML",
            "CSS",
            "Node.js",
            "Java",
            "C++",
            "MongoDB",
            "Redis",
        ]
    )
    level = factory.Iterator(["beginner", "intermediate", "advanced", "expert"])


class CompleteStudentProfileFactory(StudentProfileFactory):
    """Factory for creating complete student profiles with education and skills"""

    @factory.post_generation
    def education(
        self,
        create: bool,
        extracted: Sequence[Education] | None,
        **kwargs: dict[str, object],
    ) -> None:
        """Add education records after creation"""
        if not create:
            return

        if extracted:
            for edu in extracted:
                edu.student = self
                edu.save()
        else:
            # Create at least one education record
            EducationFactory(student=self)


class EmployerProfileFactory(django.DjangoModelFactory):
    """Factory for creating EmployerProfile instances"""

    class Meta:
        model = EmployerProfile

    user = SubFactory(EmployerUserFactory)
    company_name = Faker("company")
    industry = factory.Iterator(
        [
            "Technology",
            "Healthcare",
            "Finance",
            "Education",
            "Manufacturing",
            "Retail",
            "Non-profit",
            "Government",
            "Consulting",
            "Media",
        ]
    )
    website = factory.LazyAttribute(
        lambda obj: f"https://www.{obj.company_name.lower().replace(' ', '')}.com"
        if obj.company_name
        else "https://www.example.com"
    )
    company_description = Faker("text", max_nb_chars=1000)
    company_location = Faker("city")
    contact_name = Faker("name")
    contact_title = factory.Iterator(
        ["HR Manager", "Hiring Manager", "CEO", "CTO", "Project Manager"]
    )
    approval_status = "approved"


class PendingEmployerProfileFactory(EmployerProfileFactory):
    """Factory for creating pending employer profiles"""

    approval_status = "pending"


class EducationFactory(django.DjangoModelFactory):
    """Factory for creating Education instances"""

    class Meta:
        model = Education

    student = SubFactory(StudentProfileFactory)
    institution = factory.Iterator(
        [
            "Memorial University of Newfoundland",
            "University of Toronto",
            "McGill University",
            "University of British Columbia",
            "University of Waterloo",
        ]
    )
    degree = factory.Iterator(["Bachelor", "Master", "PhD", "Diploma", "Certificate"])
    field_of_study = factory.Iterator(
        [
            "Computer Science",
            "Software Engineering",
            "Information Technology",
            "Computer Engineering",
            "Data Science",
            "Mathematics",
            "Physics",
            "Business Administration",
            "Engineering",
        ]
    )

    start_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365 * 3)  # 3 years ago
    )
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(days=365 * 4)  # 4 year program
    )
    gpa = factory.LazyFunction(lambda: round(__import__("random").uniform(3.0, 4.0), 2))
    is_current = False


class CurrentEducationFactory(EducationFactory):
    """Factory for current education (no end date)"""

    end_date = None
    is_current = True


class EmploymentFactory(django.DjangoModelFactory):
    """Factory for creating Employment instances"""

    class Meta:
        model = Employment

    student = SubFactory(StudentProfileFactory)
    company = Faker("company")
    position = factory.Iterator(
        [
            "Software Developer Intern",
            "Data Analyst",
            "Web Developer",
            "Research Assistant",
            "Teaching Assistant",
            "IT Support",
            "Junior Developer",
            "QA Tester",
            "Business Analyst",
        ]
    )
    description = Faker("text", max_nb_chars=500)

    start_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365)  # 1 year ago
    )
    end_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=30)  # 1 month ago
    )
    is_current = False


class CurrentEmploymentFactory(EmploymentFactory):
    """Factory for current employment (no end date)"""

    end_date = None
    is_current = True


class ProjectFactory(django.DjangoModelFactory):
    """Factory for creating Project instances"""

    class Meta:
        model = Project

    employer = SubFactory(EmployerProfileFactory)
    title = factory.Iterator(
        [
            "Software Developer Internship",
            "Data Analysis Project",
            "Web Development Opportunity",
            "Machine Learning Research",
            "Mobile App Development",
            "Database Design Project",
            "UI/UX Design Internship",
        ]
    )
    description = Faker("text", max_nb_chars=1000)

    required_skills = factory.LazyFunction(
        lambda: ["Python", "Django", "JavaScript", "SQL"][:2]
    )

    preferred_skills = factory.LazyFunction(lambda: ["React", "Docker", "AWS"][:2])

    project_type = factory.Iterator(
        [
            "web_dev",
            "mobile_app",
            "data_analysis",
            "research",
            "design",
            "marketing",
            "other",
        ]
    )

    duration = factory.Iterator(
        ["1-2_weeks", "1_month", "2-3_months", "3-6_months", "6+_months"]
    )

    work_type = factory.Iterator(["remote", "onsite", "hybrid"])

    is_active = True


class ReferenceFactory(django.DjangoModelFactory):
    """Factory for creating Reference instances"""

    class Meta:
        model = Reference

    student = SubFactory(StudentProfileFactory)
    name = Faker("name")
    position = factory.Iterator(
        ["Professor", "Supervisor", "Mentor", "Manager", "Colleague"]
    )
    company = factory.Iterator(
        ["Memorial University", "Acme Corp", "Tech Solutions", "Data Inc"]
    )
    email = Faker("email")
    phone = Faker("phone_number")
    skill_endorsements = Faker("text", max_nb_chars=200)


# Convenience factories for common test scenarios


class MatchingScenarioFactory:
    """Creates a complete matching scenario with student and project"""

    @staticmethod
    def create_perfect_match() -> tuple[StudentProfile, Project]:
        """Create a student and project that should match perfectly"""
        # Create student profile first
        student = CompleteStudentProfileFactory(
            academic_year="senior",
            currently_available="yes",
            remote_preference="remote",
        )
        # Skills are already associated via ForeignKey in creation

        # Create project with same required skills
        project = ProjectFactory(
            required_skills=["Python", "Django"],
            preferred_skills=["JavaScript"],
            work_type="remote",
        )

        return student, project

    @staticmethod
    def create_poor_match() -> tuple[StudentProfile, Project]:
        """Create a student and project that should match poorly"""
        # Create student profile first
        student = CompleteStudentProfileFactory(
            academic_year="freshman",
            currently_available="no",
            remote_preference="onsite",
        )

        # Skills are already associated via ForeignKey in creation

        project = ProjectFactory(
            required_skills=["Python", "Machine Learning"], work_type="remote"
        )

        return student, project
