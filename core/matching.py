"""
AI-powered matching system for connecting students with projects
"""

from typing import Any

from .models import Project, StudentProfile


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
        Find matching students for a project
        Returns list of (student, match_data) tuples sorted by match score
        """
        students = (
            StudentProfile.objects.filter(profile_complete=True, user__is_active=True)
            .select_related("user")
            .prefetch_related("skills", "education", "employment")
        )

        matches = []

        for student in students:
            match_data = self._calculate_match(student, project)
            if match_data["score"] > 0:  # Only include students with some match
                matches.append((student, match_data))

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x[1]["score"], reverse=True)

        return matches[:limit]

    def _calculate_match(
        self, student: StudentProfile, project: Project
    ) -> dict[str, Any]:
        """Calculate match score and explanation for a student-project pair"""

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
        """Match student skills with project requirements"""
        student_skills = [skill.name.lower() for skill in student.skills.all()]
        required_skills = [skill.lower() for skill in project.required_skills]
        preferred_skills = [skill.lower() for skill in project.preferred_skills]

        if not required_skills and not preferred_skills:
            return 50  # Neutral score if no skills specified

        # Check required skills
        required_matches = 0
        required_total = len(required_skills)

        for req_skill in required_skills:
            if self._skill_matches(req_skill, student_skills):
                required_matches += 1
                match_data["evidence"].append(
                    f"✓ Has required skill: {req_skill.title()}"
                )
                match_data["match_reasons"].append(f"Required skill match: {req_skill}")
            else:
                match_data["missing_skills"].append(req_skill.title())

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
    """Convenience function to get matches for a project"""
    try:
        project = Project.objects.get(id=project_id, is_active=True)
        matcher = ProjectMatcher()
        return matcher.find_matches(project)
    except Project.DoesNotExist:
        return []


def get_student_projects(
    student_profile: StudentProfile,
) -> list[tuple[Project, dict[str, Any]]]:
    """Find relevant projects for a student"""
    active_projects = Project.objects.filter(
        is_active=True, employer__approval_status="approved"
    ).select_related("employer__user")

    matcher = ProjectMatcher()
    matches = []

    for project in active_projects:
        # Reverse the matching logic
        match_data = matcher._calculate_match(student_profile, project)
        if match_data["score"] > 30:  # Threshold for relevance
            matches.append((project, match_data))

    # Sort by match score
    matches.sort(key=lambda x: x[1]["score"], reverse=True)

    return matches[:10]  # Return top 10 matches
