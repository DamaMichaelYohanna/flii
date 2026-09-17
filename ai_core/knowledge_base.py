"""
Personal Knowledge Base context compiler.
Extracts verified facts from the applicant's relational profile, educations,
employments, projects, achievements, and STAR stories.
"""
from typing import Dict, Any

class PersonalKnowledgeBase:
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'applicant_profile', None)

    def assemble_context(self) -> Dict[str, Any]:
        """
        Gathers only verified user-provided information into a structured payload.
        Prevents AI hallucinations by supplying explicit ground truth facts.
        """
        if not self.profile:
            return {
                "applicant_name": self.user.get_full_name() or self.user.username,
                "email": self.user.email,
                "profile_completed": False,
                "facts": "No profile has been created yet."
            }

        educations = [
            {
                "institution": edu.institution,
                "country": edu.country,
                "degree_level": edu.get_degree_level_display(),
                "field_of_study": edu.field_of_study,
                "graduation_year": edu.graduation_year,
                "grade": edu.grade_classification,
                "cgpa": f"{edu.cgpa}/{edu.max_cgpa}" if edu.cgpa else "N/A",
                "coursework": edu.relevant_coursework
            }
            for edu in self.profile.educations.all()
        ]

        employments = [
            {
                "organization": emp.organization,
                "job_title": emp.job_title,
                "location": emp.location,
                "is_current": emp.is_current,
                "responsibilities": emp.responsibilities,
                "achievements": emp.achievements
            }
            for emp in self.profile.employments.all()
        ]

        skills = [f"{s.name} ({s.get_category_display()})" for s in self.profile.skills.all()]

        projects = [
            {
                "title": p.title,
                "role": p.role,
                "technologies": p.technologies,
                "description": p.description,
                "outcome": p.outcome,
                "url": p.project_url
            }
            for p in self.profile.projects.all()
        ]

        achievements = [
            {
                "title": a.title,
                "organization": a.organization,
                "description": a.description,
                "date": str(a.date_awarded) if a.date_awarded else "N/A"
            }
            for a in self.profile.achievements.all()
        ]

        certifications = [
            {
                "title": c.title,
                "issuer": c.issuer,
                "credential_id": c.credential_id
            }
            for c in self.profile.certifications.all()
        ]

        stories = [
            {
                "id": s.id,
                "title": s.title,
                "category": s.get_category_display(),
                "situation": s.situation,
                "challenge": s.challenge,
                "action": s.action,
                "result": s.result,
                "lesson_learned": s.lesson_learned,
                "skills_demonstrated": s.skills_demonstrated,
                "evidence": s.supporting_evidence
            }
            for s in self.user.stories.all()
        ]

        documents = [
            {
                "title": d.title,
                "type": d.get_document_type_display(),
                "verification_status": d.get_verification_status_display()
            }
            for d in self.user.documents.all()
        ]

        goal = getattr(self.profile, 'study_goal', None)
        goal_data = {
            "target_degree": goal.target_degree if goal else "Master's (MSc)",
            "target_fields": goal.target_fields if goal else "Computer Science / AI",
            "target_countries": goal.target_countries if goal else "Europe",
            "funding_preference": goal.get_funding_preference_display() if goal else "Fully Funded",
            "career_goals": goal.career_goals if goal else "",
            "long_term_goals": goal.long_term_goals if goal else "",
        } if goal else {}

        languages = [
            {
                "language": lang.language,
                "proficiency": lang.proficiency_level,
                "test": lang.get_test_type_display(),
                "score": lang.overall_score,
                "notes": lang.notes
            }
            for lang in self.profile.languages.all()
        ]

        research = getattr(self.profile, 'research_profile', None)
        research_data = {
            "interests": research.research_interests if research else "",
            "publications": research.publications if research else "",
            "experience": research.summary_experience if research else ""
        } if research else {}

        return {
            "personal": {
                "name": self.profile.full_name,
                "email": self.user.email,
                "phone": self.profile.phone,
                "nationality": self.profile.nationality,
                "country_of_origin": self.profile.country_of_origin,
                "location": self.profile.current_location,
                "headline": self.profile.headline,
                "bio": self.profile.bio_summary
            },
            "education": educations,
            "employment": employments,
            "skills": skills,
            "projects": projects,
            "achievements": achievements,
            "certifications": certifications,
            "stories": stories,
            "documents": documents,
            "study_goals": goal_data,
            "languages": languages,
            "research": research_data
        }

    def get_summary_text(self) -> str:
        ctx = self.assemble_context()
        lines = []
        p = ctx.get("personal", {})
        lines.append(f"Applicant: {p.get('name')} | Nationality: {p.get('nationality')} | Country: {p.get('country_of_origin')}")
        if p.get("headline"):
            lines.append(f"Headline: {p.get('headline')}")
        
        if ctx.get("education"):
            edu_strs = [f"{e['degree_level']} in {e['field_of_study']} ({e['institution']}, Grade: {e['grade']}, CGPA: {e['cgpa']})" for e in ctx["education"]]
            lines.append("Education: " + "; ".join(edu_strs))
            
        if ctx.get("study_goals"):
            g = ctx["study_goals"]
            lines.append(f"Goals: Target Degree: {g.get('target_degree')} | Target Fields: {g.get('target_fields')} | Countries: {g.get('target_countries')} | Funding: {g.get('funding_preference')}")

        if ctx.get("skills"):
            lines.append("Key Skills: " + ", ".join(ctx["skills"][:10]))

        if ctx.get("stories"):
            story_titles = [f"'{s['title']}' ({s['category']})" for s in ctx["stories"]]
            lines.append("Story Bank Experiences: " + ", ".join(story_titles))

        return "\n".join(lines)
