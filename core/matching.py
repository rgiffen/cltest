"""
AI-powered matching system for connecting students with projects
"""

import logging
from typing import Any

from django.core.cache import cache
from django.db import DatabaseError

from .models import Project, StudentProfile

logger = logging.getLogger(__name__)



class ProjectMatcher:
    """Handles matching students to projects based on skills, availability, and preferences"""

    def __init__(self) -> None:
        self.skill_synonyms = {
            "javascript": [
                "js",
                "javascript",
                "node.js",
                "nodejs",
                "react",
                "vue",
                "angular",
            ],
            "python": ["python", "django", "flask", "fastapi", "pandas", "numpy"],
            "web_development": [
                "html",
                "css",
                "frontend",
                "backend",
                "fullstack",
                "web dev",
            ],
            "database": ["sql", "mysql", "postgresql", "mongodb", "database", "db"],
            "mobile": ["ios", "android", "swift", "kotlin", "react native", "flutter"],
            "data_science": [
                "data analysis",
                "machine learning",
                "ml",
                "ai",
                "analytics",
            ],
        }

    def find_matches(
        self, project: Project, limit: int = 20
    ) -> list[tuple[StudentProfile, dict]]:
        """
        Find matching students for a project with defensive error handling
        Returns list of (student, match_data) tuples sorted by match score
        """
        # Input validation
        if not isinstance(project, Project):
            raise ValueError("project must be a Project instance")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if limit > 100:
            logger.warning(f"Large limit requested: {limit}, capping at 100")
            limit = 100

        # Try to get students with error recovery
        try:
            students = self._get_eligible_students()
        except DatabaseError as e:
            logger.error(f"Database error fetching students: {e}")
            # Try cached results as fallback
            students = self._get_cached_students()
            if not students:
                logger.error("No cached students available, returning empty results")
                return []

        matches = []
        failed_matches = 0

        for student in students:
            try:
                match_data = self._calculate_match(student, project)
                if match_data["score"] > 0:  # Only include students with some match
                    matches.append((student, match_data))
            except Exception as e:
                failed_matches += 1
                logger.warning(
                    f"Failed to calculate match for student {student.id}: {e}",
                    extra={"student_id": student.id, "project_id": project.id},
                )
                continue

        if failed_matches > 0:
            logger.info(
                f"Failed to match {failed_matches} students out of {len(students)}"
            )

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x[1]["score"], reverse=True)

        # Return fallback matches if no good matches found
        if not matches and len(students) > 0:
            logger.info(
                f"No matches found for project {project.id}, returning fallback matches"
            )
            return self._get_fallback_matches(project, limit)

        return matches[:limit]

    def _get_eligible_students(self) -> list[StudentProfile]:
        """Get eligible students with proper error handling"""
        return list(
            StudentProfile.objects.filter(profile_complete=True, user__is_active=True)
            .select_related("user")
            .prefetch_related("skills", "education", "employment")
        )

    def _get_cached_students(self) -> list[StudentProfile]:
        """Get cached student list as fallback"""
        cache_key = "eligible_students_fallback"
        cached_students: list[StudentProfile] | None = cache.get(cache_key)
        if cached_students is None:
            logger.warning("No cached students available")
            return []
        return cached_students

    def _get_fallback_matches(
        self, project: Project, limit: int
    ) -> list[tuple[StudentProfile, dict]]:
        """Get basic fallback matches when normal matching fails"""
        try:
            # Get a few random active students as fallback
            fallback_students = StudentProfile.objects.filter(
                profile_complete=True, user__is_active=True
            ).select_related("user")[:limit]

            fallback_matches = []
            for student in fallback_students:
                match_data = {
                    "score": 25,  # Low fallback score
                    "skills_match": 0,
                    "availability_match": 25,
                    "academic_match": 25,
                    "experience_match": 0,
                    "evidence": ["Fallback match - profile complete"],
                    "missing_skills": [],
                    "match_reasons": ["Basic eligibility fallback"],
                }
                fallback_matches.append((student, match_data))

            return fallback_matches
        except Exception as e:
            logger.error(f"Even fallback matching failed: {e}")
            return []

    def _calculate_match(
        self, student: StudentProfile, project: Project
    ) -> dict[str, Any]:
        """Calculate match score and explanation for a student-project pair with validation"""
        # Input validation
        if not student or not project:
            raise ValueError("Both student and project must be provided")

        if not hasattr(student, "skills") or not hasattr(student, "education"):
            raise ValueError(
                "Student must have skills and education relationships loaded"
            )

        match_data = {
            "score": 0,
            "skills_match": 0,
            "availability_match": 0,
            "academic_match": 0,
            "experience_match": 0,
            "evidence": [],
            "missing_skills": [],
            "match_reasons": [],
        }

        # 1. Skills matching (40% of total score)
        skills_score = self._match_skills(student, project, match_data)
        match_data["skills_match"] = skills_score

        # 2. Availability matching (25% of total score)
        availability_score = self._match_availability(student, project, match_data)
        match_data["availability_match"] = availability_score

        # 3. Academic level matching (20% of total score)
        academic_score = self._match_academic_level(student, project, match_data)
        match_data["academic_match"] = academic_score

        # 4. Experience matching (15% of total score)
        experience_score = self._match_experience(student, project, match_data)
        match_data["experience_match"] = experience_score

        # Calculate total weighted score
        match_data["score"] = (
            skills_score * 0.4
            + availability_score * 0.25
            + academic_score * 0.2
            + experience_score * 0.15
        )

        return match_data

    def _match_skills(
        self, student: StudentProfile, project: Project, match_data: dict[str, Any]
    ) -> float:
        """Match student skills with project requirements with error handling"""
        try:
            student_skills = [skill.name.lower() for skill in student.skills.all()]
        except Exception as e:
            logger.warning(f"Error fetching student skills for {student.id}: {e}")
            student_skills = []

        # Safely get project skills with fallback to empty lists
        try:
            required_skills = [
                skill.lower() for skill in (project.required_skills or [])
            ]
            preferred_skills = [
                skill.lower() for skill in (project.preferred_skills or [])
            ]
        except (AttributeError, TypeError) as e:
            logger.warning(f"Error parsing project skills for {project.id}: {e}")
            required_skills = []
            preferred_skills = []

        if not required_skills and not preferred_skills:
            return 50  # Neutral score if no skills specified

        # Check required skills with error handling
        required_matches = 0
        required_total = len(required_skills)

        for req_skill in required_skills:
            try:
                if self._skill_matches(req_skill, student_skills):
                    required_matches += 1
                    match_data["evidence"].append(
                        f"✓ Has required skill: {req_skill.title()}"
                    )
                    match_data["match_reasons"].append(
                        f"Required skill match: {req_skill}"
                    )
                else:
                    match_data["missing_skills"].append(req_skill.title())
            except Exception as e:
                logger.warning(f"Error checking skill match for '{req_skill}': {e}")
                continue

        # Check preferred skills
        preferred_matches = 0
        preferred_total = len(preferred_skills)

        for pref_skill in preferred_skills:
            if self._skill_matches(pref_skill, student_skills):
                preferred_matches += 1
                match_data["evidence"].append(f"+ Bonus skill: {pref_skill.title()}")
                match_data["match_reasons"].append(
                    f"Preferred skill match: {pref_skill}"
                )

        # Calculate skills score
        if required_total > 0:
            required_score = (
                required_matches / required_total
            ) * 80  # 80% for required
            preferred_bonus = (
                preferred_matches / max(preferred_total, 1)
            ) * 20  # 20% bonus
            return min(100, required_score + preferred_bonus)
        else:
            # Only preferred skills
            return (preferred_matches / max(preferred_total, 1)) * 100

    def _skill_matches(self, target_skill: str, student_skills: list[str]) -> bool:
        """Check if target skill matches any student skill (including synonyms)"""
        target_skill = target_skill.lower().strip()

        # Direct match
        if target_skill in student_skills:
            return True

        # Check synonyms
        for _category, synonyms in self.skill_synonyms.items():
            if target_skill in synonyms:
                # If target is in a category, check if student has any skill from that category
                for student_skill in student_skills:
                    if student_skill in synonyms:
                        return True

        # Partial string matching for compound skills
        for student_skill in student_skills:
            if target_skill in student_skill or student_skill in target_skill:
                return True

        return False

    def _match_availability(
        self, student: StudentProfile, project: Project, match_data: dict[str, Any]
    ) -> float:
        """Match student availability with project work type and duration"""
        score = 50  # Base score

        # Check work type compatibility
        if project.work_type == "remote" and student.remote_preference in [
            "remote",
            "hybrid",
            "flexible",
        ]:
            score += 25
            match_data["evidence"].append("✓ Remote work compatible")
        elif project.work_type == "onsite" and student.remote_preference in [
            "onsite",
            "flexible",
        ]:
            score += 25
            match_data["evidence"].append("✓ On-site work compatible")
        elif project.work_type == "hybrid" and student.remote_preference != "remote":
            score += 20
            match_data["evidence"].append("✓ Hybrid work compatible")

        # Check current availability
        if student.currently_available == "yes":
            score += 25
            match_data["evidence"].append("✓ Currently available")
        elif student.currently_available == "limited":
            score += 10
            match_data["evidence"].append("~ Limited availability")

        return min(100, score)

    def _match_academic_level(
        self, student: StudentProfile, project: Project, match_data: dict[str, Any]
    ) -> float:
        """Match student academic level with project requirements"""
        if not project.min_academic_year:
            return 75  # Neutral score if no requirement

        academic_levels = {
            "freshman": 1,
            "sophomore": 2,
            "junior": 3,
            "senior": 4,
            "graduate": 5,
        }

        student_level = academic_levels.get(student.academic_year, 0)
        required_level = academic_levels.get(project.min_academic_year, 0)

        if student_level >= required_level:
            score = 100
            match_data["evidence"].append(
                f"✓ Academic level: {student.get_academic_year_display()}"
            )
            if student_level > required_level:
                match_data["match_reasons"].append(
                    "Exceeds minimum academic requirements"
                )
        else:
            score = max(0, 50 - (required_level - student_level) * 15)
            match_data["evidence"].append("⚠ Academic level below minimum requirement")

        return score

    def _match_experience(
        self, student: StudentProfile, project: Project, match_data: dict[str, Any]
    ) -> float:
        """Match student experience with project complexity"""
        score = 50  # Base score

        # Count relevant experience
        total_employment = student.employment.count()
        relevant_projects = 0

        # Check employment descriptions for relevant keywords
        project_keywords = project.description.lower().split()
        for employment in student.employment.all():
            if employment.description:
                emp_words = employment.description.lower().split()
                common_words = set(project_keywords) & set(emp_words)
                if len(common_words) > 3:  # Arbitrary threshold
                    relevant_projects += 1

        # Adjust score based on experience
        if total_employment > 0:
            score += min(25, total_employment * 8)
            match_data["evidence"].append(
                f"✓ {total_employment} work experience entries"
            )

        if relevant_projects > 0:
            score += 25
            match_data["evidence"].append(
                f"✓ {relevant_projects} relevant project experience"
            )

        # Check education relevance
        if project.preferred_programs:
            for education in student.education.all():
                for preferred_program in project.preferred_programs:
                    if preferred_program.lower() in education.field_of_study.lower():
                        score += 15
                        match_data["evidence"].append(
                            f"✓ Relevant education: {education.field_of_study}"
                        )
                        break

        return min(100, score)


def get_project_matches(project_id: int) -> list[tuple[StudentProfile, dict[str, Any]]]:
    """Convenience function to get matches for a project with validation"""
    # Input validation
    if not isinstance(project_id, int) or project_id <= 0:
        raise ValueError("project_id must be a positive integer")

    try:
        project = Project.objects.select_related("employer").get(
            id=project_id, is_active=True
        )

        # Validate project has required data for matching
        if not project.employer or project.employer.approval_status != "approved":
            logger.warning(
                f"Project {project_id} has unapproved employer, returning empty matches"
            )
            return []

        matcher = ProjectMatcher()

        # Cache results for 10 minutes to reduce database load
        cache_key = f"project_matches_{project_id}"
        cached_result: list[tuple[StudentProfile, dict[str, Any]]] | None = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Returning cached matches for project {project_id}")
            return cached_result

        matches: list[tuple[StudentProfile, dict[str, Any]]] = matcher.find_matches(project)

        # Cache successful results
        if matches:
            cache.set(cache_key, matches, timeout=600)  # 10 minutes

        return matches

    except Project.DoesNotExist:
        logger.warning(f"Project {project_id} not found or inactive")
        return []
    except Exception as e:
        logger.error(
            f"Error getting matches for project {project_id}: {e}", exc_info=True
        )
        return []


def get_student_projects(
    student_profile: StudentProfile,
) -> list[tuple[Project, dict[str, Any]]]:
    """Find relevant projects for a student with defensive programming"""
    # Input validation
    if not isinstance(student_profile, StudentProfile):
        raise ValueError("student_profile must be a StudentProfile instance")

    if not student_profile.profile_complete:
        logger.warning(
            f"Student {student_profile.id} profile incomplete, returning empty results"
        )
        return []

    try:
        # Cache check first
        cache_key = f"student_projects_{student_profile.id}"
        cached_result: list[tuple[Project, dict[str, Any]]] | None = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Returning cached projects for student {student_profile.id}")
            return cached_result

        active_projects = Project.objects.filter(
            is_active=True, employer__approval_status="approved"
        ).select_related("employer__user")[:50]  # Limit to prevent excessive processing

        if not active_projects.exists():
            logger.info("No active approved projects available")
            return []

        matcher = ProjectMatcher()
        matches = []
        failed_matches = 0

        for project in active_projects:
            try:
                # Reverse the matching logic
                match_data = matcher._calculate_match(student_profile, project)
                if match_data["score"] > 30:  # Threshold for relevance
                    matches.append((project, match_data))
            except Exception as e:
                failed_matches += 1
                logger.warning(
                    f"Failed to match project {project.id} to student {student_profile.id}: {e}"
                )
                continue

        if failed_matches > 0:
            logger.info(
                f"Failed to match {failed_matches} projects for student {student_profile.id}"
            )

        # Sort by match score
        matches.sort(key=lambda x: x[1]["score"], reverse=True)

        result = matches[:10]  # Return top 10 matches

        # Cache successful results
        if result:
            cache.set(cache_key, result, timeout=300)  # 5 minutes

        return result

    except Exception as e:
        logger.error(
            f"Error finding projects for student {student_profile.id}: {e}",
            exc_info=True,
        )
        return []
