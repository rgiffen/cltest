from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Education,
    EmployerProfile,
    Employment,
    Project,
    Skill,
    StudentProfile,
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with demo data for testing and presentation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing demo data...')
            # Only clear demo users, not admin users
            demo_users = User.objects.filter(
                email__in=[
                    'john.doe@mun.ca',
                    'sarah.wilson@mun.ca',
                    'mike.chen@mun.ca',
                    'testemployer@techcorp.com',
                    'hr@innovativetech.com',
                    'jobs@creativestudio.com'
                ]
            )
            demo_users.delete()
            self.stdout.write(self.style.SUCCESS('Demo data cleared.'))

        self.stdout.write('Creating demo users and data...')

        # Create demo students
        self.create_demo_students()

        # Create demo employers (with different approval statuses)
        self.create_demo_employers()

        # Create demo projects
        self.create_demo_projects()

        self.stdout.write(self.style.SUCCESS('Demo data populated successfully!'))
        self.stdout.write('')
        self.stdout.write('Demo Login Credentials:')
        self.stdout.write('Students:')
        self.stdout.write('  john.doe@mun.ca / password123')
        self.stdout.write('  sarah.wilson@mun.ca / password123')
        self.stdout.write('  mike.chen@mun.ca / password123')
        self.stdout.write('')
        self.stdout.write('Employers:')
        self.stdout.write('  testemployer@techcorp.com / password123 (approved)')
        self.stdout.write('  hr@innovativetech.com / password123 (pending approval)')
        self.stdout.write('  jobs@creativestudio.com / password123 (approved)')

    def create_demo_students(self):
        # Student 1: John Doe - Computer Science
        if not User.objects.filter(email='john.doe@mun.ca').exists():
            john = User.objects.create_user(
                username='john.doe@mun.ca',
                email='john.doe@mun.ca',
                first_name='John',
                last_name='Doe',
                password='password123',
                user_type='student'
            )

            john_profile = StudentProfile.objects.create(
                user=john,
                phone='709-555-0123',
                academic_year='third',
                program='Computer Science',
                university='Memorial University of Newfoundland',
                currently_available='yes',
                available_date=date.today(),
                availability=['internship', 'part_time', 'contract'],
                availability_notes='Available for summer internship and part-time work during semester',
                remote_preference='hybrid',
                location_flexibility='local',
                career_goals='Interested in full-stack web development and machine learning applications',
                additional_info='Active in programming competitions and hackathons',
                profile_complete=True
            )

            # Education
            Education.objects.create(
                student=john_profile,
                institution='Memorial University of Newfoundland',
                degree='Bachelor of Science',
                field_of_study='Computer Science',
                gpa=3.75,
                start_date=date(2022, 9, 1),
                is_current=True
            )

            # Skills
            skills_data = [
                ('Python', 'advanced', 'Used in multiple projects and coursework'),
                ('JavaScript', 'intermediate', 'React and Node.js experience'),
                ('SQL', 'intermediate', 'Database design and queries'),
                ('Git', 'advanced', 'Version control for all projects'),
                ('Django', 'beginner', 'Currently learning web frameworks')
            ]

            for skill_name, level, desc in skills_data:
                Skill.objects.create(
                    student=john_profile,
                    name=skill_name,
                    level=level,
                    experience_description=desc
                )

            # Employment
            Employment.objects.create(
                student=john_profile,
                company='Local Web Solutions',
                position='Junior Developer (Part-time)',
                start_date=date(2023, 5, 1),
                end_date=date(2023, 8, 31),
                description='Developed small business websites using HTML, CSS, and JavaScript',
                is_current=False
            )

        # Student 2: Sarah Wilson - Business Administration
        if not User.objects.filter(email='sarah.wilson@mun.ca').exists():
            sarah = User.objects.create_user(
                username='sarah.wilson@mun.ca',
                email='sarah.wilson@mun.ca',
                first_name='Sarah',
                last_name='Wilson',
                password='password123',
                user_type='student'
            )

            sarah_profile = StudentProfile.objects.create(
                user=sarah,
                phone='709-555-0456',
                academic_year='fourth',
                program='Business Administration',
                university='Memorial University of Newfoundland',
                currently_available='available_soon',
                available_date=date.today() + timedelta(days=30),
                availability=['internship', 'full_time'],
                availability_notes='Graduating in spring, looking for full-time opportunities',
                remote_preference='remote',
                location_flexibility='flexible',
                career_goals='Digital marketing and business analysis with focus on data-driven decision making',
                profile_complete=True
            )

            # Education
            Education.objects.create(
                student=sarah_profile,
                institution='Memorial University of Newfoundland',
                degree='Bachelor of Business Administration',
                field_of_study='Marketing and Analytics',
                gpa=3.90,
                start_date=date(2021, 9, 1),
                is_current=True
            )

            # Skills
            skills_data = [
                ('Digital Marketing', 'advanced', 'Social media campaigns and SEO'),
                ('Data Analysis', 'intermediate', 'Excel, Google Analytics, basic R'),
                ('Project Management', 'intermediate', 'Led multiple team projects'),
                ('Adobe Creative Suite', 'beginner', 'Photoshop and Illustrator basics'),
                ('Google Ads', 'intermediate', 'Certified in Google Ads fundamentals')
            ]

            for skill_name, level, desc in skills_data:
                Skill.objects.create(
                    student=sarah_profile,
                    name=skill_name,
                    level=level,
                    experience_description=desc
                )

        # Student 3: Mike Chen - Engineering
        if not User.objects.filter(email='mike.chen@mun.ca').exists():
            mike = User.objects.create_user(
                username='mike.chen@mun.ca',
                email='mike.chen@mun.ca',
                first_name='Mike',
                last_name='Chen',
                password='password123',
                user_type='student'
            )

            mike_profile = StudentProfile.objects.create(
                user=mike,
                phone='709-555-0789',
                academic_year='second',
                program='Electrical Engineering',
                university='Memorial University of Newfoundland',
                currently_available='no',
                available_date=date(2024, 5, 1),
                availability=['internship'],
                availability_notes='Looking for summer internship in engineering or tech',
                remote_preference='onsite',
                location_flexibility='local',
                career_goals='Embedded systems development and IoT applications',
                profile_complete=True
            )

            # Education
            Education.objects.create(
                student=mike_profile,
                institution='Memorial University of Newfoundland',
                degree='Bachelor of Engineering',
                field_of_study='Electrical Engineering',
                gpa=3.60,
                start_date=date(2023, 9, 1),
                is_current=True
            )

            # Skills
            skills_data = [
                ('C/C++', 'intermediate', 'Embedded programming projects'),
                ('Arduino', 'advanced', 'Multiple IoT and robotics projects'),
                ('MATLAB', 'intermediate', 'Signal processing and simulation'),
                ('PCB Design', 'beginner', 'Introduction to circuit design'),
                ('Python', 'beginner', 'Automation scripts and data analysis')
            ]

            for skill_name, level, desc in skills_data:
                Skill.objects.create(
                    student=mike_profile,
                    name=skill_name,
                    level=level,
                    experience_description=desc
                )

    def create_demo_employers(self):
        # Employer 1: TechCorp (Approved)
        if not User.objects.filter(email='testemployer@techcorp.com').exists():
            tech_user = User.objects.create_user(
                username='testemployer@techcorp.com',
                email='testemployer@techcorp.com',
                first_name='Alex',
                last_name='Thompson',
                password='password123',
                user_type='employer'
            )

            EmployerProfile.objects.create(
                user=tech_user,
                company_name='TechCorp Solutions',
                industry='technology',
                website='https://techcorp.com',
                company_description='Leading technology consulting firm specializing in digital transformation and software development solutions for businesses across Atlantic Canada.',
                company_location='St. John\'s, NL',
                contact_name='Alex Thompson',
                contact_title='Talent Acquisition Manager',
                contact_phone='709-555-1000',
                approval_status='approved',
                approved_at=timezone.now() - timedelta(days=7)
            )

        # Employer 2: Innovative Tech (Pending)
        if not User.objects.filter(email='hr@innovativetech.com').exists():
            innov_user = User.objects.create_user(
                username='hr@innovativetech.com',
                email='hr@innovativetech.com',
                first_name='Jane',
                last_name='Smith',
                password='password123',
                user_type='employer'
            )

            EmployerProfile.objects.create(
                user=innov_user,
                company_name='Innovative Tech Solutions',
                industry='technology',
                website='https://innovativetech.com',
                company_description='A cutting-edge technology company specializing in AI-powered solutions for businesses.',
                company_location='Halifax, NS',
                contact_name='Jane Smith',
                contact_title='HR Director',
                contact_phone='902-555-0123',
                approval_status='pending'
            )

        # Employer 3: Creative Studio (Approved)
        if not User.objects.filter(email='jobs@creativestudio.com').exists():
            creative_user = User.objects.create_user(
                username='jobs@creativestudio.com',
                email='jobs@creativestudio.com',
                first_name='Maria',
                last_name='Rodriguez',
                password='password123',
                user_type='employer'
            )

            EmployerProfile.objects.create(
                user=creative_user,
                company_name='Atlantic Creative Studio',
                industry='marketing',
                website='https://atlanticcreative.ca',
                company_description='Full-service digital marketing agency serving clients across the Maritimes with creative campaigns and brand development.',
                company_location='Fredericton, NB',
                contact_name='Maria Rodriguez',
                contact_title='Creative Director',
                contact_phone='506-555-2000',
                approval_status='approved',
                approved_at=timezone.now() - timedelta(days=14)
            )

    def create_demo_projects(self):
        # Get approved employers
        tech_corp = EmployerProfile.objects.filter(company_name='TechCorp Solutions').first()
        creative_studio = EmployerProfile.objects.filter(company_name='Atlantic Creative Studio').first()

        if tech_corp:
            # Project 1: Web Development
            Project.objects.get_or_create(
                employer=tech_corp,
                title='E-commerce Website Development',
                defaults={
                    'description': 'Develop a modern, responsive e-commerce website for a local retail client. The project involves building a user-friendly online store with payment integration, inventory management, and customer account features.',
                    'project_type': 'web_dev',
                    'duration': '2-3_months',
                    'work_type': 'hybrid',
                    'required_skills': ['JavaScript', 'HTML/CSS', 'React'],
                    'preferred_skills': ['Node.js', 'MongoDB', 'Git'],
                    'min_academic_year': 'second',
                    'preferred_programs': ['Computer Science', 'Software Engineering'],
                    'is_active': True
                }
            )

            # Project 2: Data Analysis
            Project.objects.get_or_create(
                employer=tech_corp,
                title='Business Intelligence Dashboard',
                defaults={
                    'description': 'Create an interactive dashboard to help clients visualize their business data and make informed decisions. Project includes data cleaning, analysis, and creating compelling visualizations.',
                    'project_type': 'data_analysis',
                    'duration': '1_month',
                    'work_type': 'remote',
                    'required_skills': ['Python', 'Data Analysis'],
                    'preferred_skills': ['Tableau', 'SQL', 'Statistics'],
                    'min_academic_year': 'third',
                    'preferred_programs': ['Computer Science', 'Business Administration', 'Mathematics'],
                    'is_active': True
                }
            )

        if creative_studio:
            # Project 3: Marketing Campaign
            Project.objects.get_or_create(
                employer=creative_studio,
                title='Social Media Marketing Campaign',
                defaults={
                    'description': 'Develop and execute a comprehensive social media marketing campaign for a tourism client. Includes content creation, campaign strategy, and performance analysis.',
                    'project_type': 'marketing',
                    'duration': '1-2_weeks',
                    'work_type': 'hybrid',
                    'required_skills': ['Digital Marketing', 'Social Media'],
                    'preferred_skills': ['Adobe Creative Suite', 'Google Analytics', 'Content Creation'],
                    'min_academic_year': 'second',
                    'preferred_programs': ['Business Administration', 'Marketing', 'Communications'],
                    'is_active': True
                }
            )
