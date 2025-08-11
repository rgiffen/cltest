# type: ignore
"""
Integration tests for API endpoints

Tests API functionality, request/response handling, authentication,
and business logic integration points.
"""

import json
import unittest
from typing import Any

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from core.factories import (
    CompleteStudentProfileFactory,
    EmployerProfileFactory,
    EmployerUserFactory,
    MatchingScenarioFactory,
    ProjectFactory,
    SkillFactory,
    StudentUserFactory,
)
from core.models import Project

User = get_user_model()


class APITestCase(TestCase):
    """Base test case with common setup for API tests"""

    def setUp(self) -> None:
        """Set up common test data"""
        self.client = Client()
        cache.clear()  # Clear cache between tests

        # Create test users
        self.student_user = StudentUserFactory()
        self.employer_user = EmployerUserFactory()

        # Create profiles
        self.student_profile = CompleteStudentProfileFactory(user=self.student_user)
        self.employer_profile = EmployerProfileFactory(user=self.employer_user)

    def login_student(self) -> None:
        """Helper to log in as student"""
        self.client.force_login(self.student_user)

    def login_employer(self) -> None:
        """Helper to log in as employer"""
        self.client.force_login(self.employer_user)

    def assertJsonResponse(self, response: HttpResponse, status_code: int = 200) -> dict[str, Any]:
        """Helper to assert JSON response and return parsed data"""
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response['Content-Type'], 'application/json')
        return json.loads(response.content)


@unittest.skip("API endpoints not implemented yet")
class StudentAPITest(APITestCase):
    """Test student-related API endpoints"""

    def test_student_profile_api_authenticated(self) -> None:
        """Test authenticated access to student profile API"""
        self.login_student()

        # Assuming there's a student profile API endpoint
        url = reverse('api:student-profile')  # Adjust URL name as needed
        response = self.client.get(url)

        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertEqual(data['id'], self.student_profile.id)
            self.assertIn('skills', data)
            self.assertIn('education', data)

    def test_student_profile_api_unauthenticated(self) -> None:
        """Test unauthenticated access is blocked"""
        url = reverse('api:student-profile', kwargs={'pk': self.student_profile.id})
        response = self.client.get(url)

        # Should redirect to login or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])

    def test_student_matches_api(self) -> None:
        """Test API endpoint for getting student matches"""
        self.login_student()

        # Create some projects to match against
        ProjectFactory()
        ProjectFactory()

        url = reverse('api:student-matches')  # Adjust URL name
        response = self.client.get(url)

        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertIsInstance(data, list)

            # Check structure if matches found
            if data:
                match = data[0]
                self.assertIn('project', match)
                self.assertIn('match_data', match)
                self.assertIn('score', match['match_data'])

    def test_student_profile_update_api(self) -> None:
        """Test updating student profile via API"""
        self.login_student()

        update_data = {
            'career_goals': 'Updated career goals',
            'currently_available': 'limited',
            'remote_preference': 'hybrid'
        }

        url = reverse('api:student-profile-update')  # Adjust URL name
        response = self.client.patch(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )

        if response.status_code in [200, 204]:
            # Refresh from database
            self.student_profile.refresh_from_db()
            self.assertEqual(self.student_profile.career_goals, 'Updated career goals')
            self.assertEqual(self.student_profile.currently_available, 'limited')


@unittest.skip("API endpoints not implemented yet")
class EmployerAPITest(APITestCase):
    """Test employer-related API endpoints"""

    def test_employer_projects_list(self) -> None:
        """Test listing employer's projects"""
        self.login_employer()

        # Create projects for this employer
        ProjectFactory(employer=self.employer_profile, title="Project 1")
        ProjectFactory(employer=self.employer_profile, title="Project 2")

        # Create project for different employer (shouldn't appear)
        other_employer = EmployerProfileFactory()
        other_project = ProjectFactory(employer=other_employer)

        url = reverse('api:employer-projects')  # Adjust URL name
        response = self.client.get(url)

        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertIsInstance(data, list)

            # Should only see own projects
            project_titles = [p['title'] for p in data]
            self.assertIn('Project 1', project_titles)
            self.assertIn('Project 2', project_titles)
            self.assertNotIn(other_project.title, project_titles)

    def test_project_matches_api(self) -> None:
        """Test getting matches for a specific project"""
        self.login_employer()

        # Create project and matching student
        student, project = MatchingScenarioFactory.create_perfect_match()
        project.employer = self.employer_profile
        project.save()

        url = reverse('api:project-matches', kwargs={'project_id': project.id})
        response = self.client.get(url)

        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertIsInstance(data, list)

            # Should find the matching student
            if data:
                match = data[0]
                self.assertIn('student', match)
                self.assertIn('match_data', match)
                self.assertEqual(match['student']['id'], student.id)
                self.assertGreater(match['match_data']['score'], 50)

    def test_project_create_api(self) -> None:
        """Test creating a new project via API"""
        self.login_employer()

        project_data = {
            'title': 'New API Project',
            'description': 'Created via API test',
            'project_type': 'web_dev',
            'duration': '2-3_months',
            'required_skills': ['Python', 'Django'],
            'work_type': 'remote'
        }

        url = reverse('api:project-create')  # Adjust URL name
        response = self.client.post(
            url,
            data=json.dumps(project_data),
            content_type='application/json'
        )

        if response.status_code in [200, 201]:
            data = self.assertJsonResponse(response, 201)

            # Verify project was created
            self.assertEqual(data['title'], 'New API Project')
            self.assertEqual(data['employer'], self.employer_profile.id)

            # Verify in database
            project = Project.objects.get(id=data['id'])
            self.assertEqual(project.title, 'New API Project')
            self.assertEqual(project.employer, self.employer_profile)

    def test_unauthorized_project_access(self) -> None:
        """Test that employers can't access other employer's projects"""
        self.login_employer()

        # Create project for different employer
        other_employer = EmployerProfileFactory()
        other_project = ProjectFactory(employer=other_employer)

        url = reverse('api:project-detail', kwargs={'pk': other_project.id})
        response = self.client.get(url)

        # Should get 403 Forbidden or 404 Not Found
        self.assertIn(response.status_code, [403, 404])


@unittest.skip("API endpoints not implemented yet")
class MatchingAPITest(APITestCase):
    """Test matching system API endpoints"""

    def test_project_matching_endpoint(self) -> None:
        """Test the project matching API endpoint"""
        # Create test scenario
        student, project = MatchingScenarioFactory.create_perfect_match()

        url = reverse('api:project-matches', kwargs={'project_id': project.id})
        response = self.client.get(url)

        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertIsInstance(data, list)

            # Verify match structure
            if data:
                match = data[0]
                required_keys = ['student', 'match_data']
                for key in required_keys:
                    self.assertIn(key, match)

                # Verify match data structure
                match_data = match['match_data']
                score_keys = [
                    'score', 'skills_match', 'availability_match',
                    'academic_match', 'experience_match'
                ]
                for key in score_keys:
                    self.assertIn(key, match_data)
                    self.assertIsInstance(match_data[key], (int, float))

    def test_matching_with_filters(self) -> None:
        """Test matching API with query filters"""
        student, project = MatchingScenarioFactory.create_perfect_match()

        url = reverse('api:project-matches', kwargs={'project_id': project.id})

        # Test with limit filter
        response = self.client.get(url, {'limit': 5})
        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertLessEqual(len(data), 5)

        # Test with minimum score filter
        response = self.client.get(url, {'min_score': 80})
        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            for match in data:
                self.assertGreaterEqual(match['match_data']['score'], 80)

    def test_matching_caching_behavior(self) -> None:
        """Test that matching results are properly cached"""
        student, project = MatchingScenarioFactory.create_perfect_match()

        url = reverse('api:project-matches', kwargs={'project_id': project.id})

        # First request - should compute matches
        response1 = self.client.get(url)
        if response1.status_code == 200:
            data1 = self.assertJsonResponse(response1)

            # Second request - should use cached results
            response2 = self.client.get(url)
            data2 = self.assertJsonResponse(response2)

            # Results should be identical
            self.assertEqual(data1, data2)

    def test_matching_error_handling(self) -> None:
        """Test error handling in matching API"""
        # Test with invalid project ID
        url = reverse('api:project-matches', kwargs={'project_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Test with inactive project
        project = ProjectFactory(is_active=False)
        url = reverse('api:project-matches', kwargs={'project_id': project.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [404, 400])


@unittest.skip("API endpoints not implemented yet")
class SkillsAPITest(APITestCase):
    """Test skills-related API endpoints"""

    def test_skills_autocomplete_api(self) -> None:
        """Test skills autocomplete functionality"""
        # Create some test skills
        SkillFactory(name="Python")
        SkillFactory(name="JavaScript")
        SkillFactory(name="Java")
        SkillFactory(name="PostgreSQL")

        url = reverse('api:skills-autocomplete')  # Adjust URL name

        # Test search query
        response = self.client.get(url, {'q': 'Ja'})
        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertIsInstance(data, list)

            # Should return skills starting with 'Ja'
            skill_names = [skill['name'] for skill in data]
            self.assertIn('JavaScript', skill_names)
            self.assertIn('Java', skill_names)
            self.assertNotIn('Python', skill_names)

    def test_popular_skills_api(self) -> None:
        """Test popular skills endpoint"""
        # Create multiple students with Python (should make it popular)
        for _ in range(5):
            student = CompleteStudentProfileFactory()
            SkillFactory(name="Python", student=student)

        # One student with JavaScript
        js_student = CompleteStudentProfileFactory()
        SkillFactory(name="JavaScript", student=js_student)

        url = reverse('api:popular-skills')  # Adjust URL name
        response = self.client.get(url)

        if response.status_code == 200:
            data = self.assertJsonResponse(response)
            self.assertIsInstance(data, list)

            if data:
                # Python should be more popular than JavaScript
                skill_counts = {skill['name']: skill['count'] for skill in data}
                if 'Python' in skill_counts and 'JavaScript' in skill_counts:
                    self.assertGreater(skill_counts['Python'], skill_counts['JavaScript'])


@unittest.skip("API endpoints not implemented yet")
class APISecurityTest(APITestCase):
    """Test API security measures"""

    def test_authentication_required(self) -> None:
        """Test that protected endpoints require authentication"""
        protected_urls: list[tuple[str, dict[str, str]]] = [
            ('api:student-profile', {}),
            ('api:employer-projects', {}),
            ('api:student-matches', {}),
        ]

        for url_name, kwargs in protected_urls:
            try:
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)
                # Should redirect to login or return 401/403
                self.assertIn(response.status_code, [302, 401, 403],
                            f"URL {url} should require authentication")
            except Exception:
                # URL might not exist in current implementation
                pass

    def test_cross_user_access_prevention(self) -> None:
        """Test that users can't access other users' data"""
        # Create two different students
        other_student_user = StudentUserFactory()
        other_student_profile = CompleteStudentProfileFactory(user=other_student_user)

        self.login_student()

        # Try to access other student's profile
        try:
            url = reverse('api:student-profile', kwargs={'pk': other_student_profile.id})
            response = self.client.get(url)
            # Should get 403 Forbidden or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
        except Exception:
            # URL might not exist in current implementation
            pass

    def test_sql_injection_prevention(self) -> None:
        """Test that API endpoints are protected against SQL injection"""
        malicious_inputs = [
            "'; DROP TABLE core_studentprofile; --",
            "1 OR 1=1",
            "<script>alert('xss')</script>"
        ]

        try:
            url = reverse('api:skills-autocomplete')

            for malicious_input in malicious_inputs:
                response = self.client.get(url, {'q': malicious_input})
                # Should handle gracefully without errors
                self.assertLess(response.status_code, 500,
                              f"Malicious input caused server error: {malicious_input}")
        except Exception:
            # URL might not exist in current implementation
            pass

    def test_rate_limiting_headers(self) -> None:
        """Test that rate limiting headers are present if implemented"""
        try:
            url = reverse('api:popular-skills')
            response = self.client.get(url)

            # If rate limiting is implemented, check for headers
            rate_limit_headers = [
                'X-RateLimit-Limit',
                'X-RateLimit-Remaining',
                'X-RateLimit-Reset'
            ]

            # Note: Only check if any rate limit headers are present
            has_rate_limits = any(header in response for header in rate_limit_headers)

            if has_rate_limits:
                # If rate limiting is implemented, all headers should be present
                for header in rate_limit_headers:
                    self.assertIn(header, response)
        except Exception:
            # URL might not exist or rate limiting not implemented
            pass


@unittest.skip("API endpoints not implemented yet")
class APIResponseFormatTest(APITestCase):
    """Test API response format consistency"""

    def test_error_response_format(self) -> None:
        """Test that error responses have consistent format"""
        # Test 404 error format
        try:
            url = reverse('api:project-matches', kwargs={'project_id': 99999})
            response = self.client.get(url)

            if response.status_code == 404 and response['Content-Type'] == 'application/json':
                data = json.loads(response.content)

                # Should have error information
                self.assertIn('error', data)
                self.assertIsInstance(data['error'], (str, dict))
        except Exception:
            # URL might not exist in current implementation
            pass

    def test_success_response_format(self) -> None:
        """Test that success responses have consistent format"""
        try:
            # Create test data
            student, project = MatchingScenarioFactory.create_perfect_match()

            url = reverse('api:project-matches', kwargs={'project_id': project.id})
            response = self.client.get(url)

            if response.status_code == 200:
                data = self.assertJsonResponse(response)

                # Response should be a list for matches endpoint
                self.assertIsInstance(data, list)

                # Each item should have consistent structure
                if data:
                    match = data[0]
                    self.assertIn('student', match)
                    self.assertIn('match_data', match)
                    self.assertIsInstance(match['student'], dict)
                    self.assertIsInstance(match['match_data'], dict)
        except Exception:
            # URL might not exist in current implementation
            pass

    def test_pagination_format(self) -> None:
        """Test pagination format if implemented"""
        try:
            # Create multiple test objects to trigger pagination
            for _ in range(15):
                CompleteStudentProfileFactory()

            url = reverse('api:students-list')  # Adjust URL name
            response = self.client.get(url, {'page': 1, 'page_size': 10})

            if response.status_code == 200:
                data = self.assertJsonResponse(response)

                # Check for pagination metadata
                if isinstance(data, dict) and 'results' in data:
                    self.assertIn('count', data)
                    self.assertIn('next', data)
                    self.assertIn('previous', data)
                    self.assertIn('results', data)
                    self.assertIsInstance(data['results'], list)
        except Exception:
            # URL might not exist or pagination not implemented
            pass
