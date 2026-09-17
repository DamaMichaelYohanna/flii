import re
from typing import Dict, Any, List
from opportunities.models import Opportunity
from applicants.models import ApplicantProfile
from ai_core.service import AIService
from ai_core.schemas import EligibilityResult

class MatchingEngine:
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'applicant_profile', None)

    def calculate_deterministic_fit(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        Fast deterministic rule matching for listings and filters.
        Calculates a Profile Fit score and quick eligibility verdict.
        """
        if not self.profile:
            return {
                "score": 50,
                "status": "needs_clarification",
                "label": "Profile Incomplete",
                "color": "amber",
                "reasons": ["Complete your profile to see tailored match scores."]
            }

        score = 40
        reasons = []

        # 1. Degree level alignment
        study_goal = getattr(self.profile, 'study_goal', None)
        target_degree = (study_goal.target_degree if study_goal else "masters").lower()
        if opportunity.degree_level in target_degree or "master" in target_degree:
            score += 15
            reasons.append(f"Matches target degree level ({opportunity.get_degree_level_display()}).")

        # 2. Field of study alignment
        user_field = (study_goal.target_fields if study_goal else "").lower()
        edu_fields = [e.field_of_study.lower() for e in self.profile.educations.all()]
        all_fields = user_field + " " + " ".join(edu_fields)
        
        opp_field_keywords = [w.lower() for w in re.findall(r'\w+', opportunity.field_of_study)]
        matched_kw = [kw for kw in opp_field_keywords if len(kw) > 3 and kw in all_fields]
        if matched_kw:
            score += 15
            reasons.append(f"Subject field overlap ({', '.join(set(matched_kw[:3]))}).")

        # 3. Country / Region preference
        user_countries = (study_goal.target_countries if study_goal else "").lower()
        if opportunity.country.lower() in user_countries or "europe" in user_countries:
            score += 10
            reasons.append(f"Target country alignment ({opportunity.country}).")

        # 4. Academic performance / First class / 2:1
        first_class = any(
            'first' in (e.grade_classification or '').lower() or (e.cgpa and e.cgpa >= 4.5)
            for e in self.profile.educations.all()
        )
        if first_class:
            score += 15
            reasons.append("Academic grade satisfies competitive threshold.")

        # 5. Nationality alignment
        if "nigeria" in opportunity.nationality_requirement.lower() or "all" in opportunity.nationality_requirement.lower() or "developing" in opportunity.nationality_requirement.lower():
            score += 10
            reasons.append("Nationality is explicitly eligible.")

        final_score = min(98, max(20, score))
        
        if final_score >= 80:
            status = "likely_eligible"
            label = "High Fit"
            color = "emerald"
        elif final_score >= 60:
            status = "likely_eligible"
            label = "Good Fit"
            color = "blue"
        elif final_score >= 45:
            status = "needs_clarification"
            label = "Potential Fit"
            color = "amber"
        else:
            status = "likely_ineligible"
            label = "Low Fit"
            color = "gray"

        return {
            "score": final_score,
            "status": status,
            "label": label,
            "color": color,
            "reasons": reasons
        }

    def assess_full_eligibility(self, opportunity: Opportunity) -> EligibilityResult:
        """
        Deep AI-assisted requirement-by-requirement evaluation.
        """
        ai_service = AIService.get_instance()
        return ai_service.assess_eligibility(self.user, opportunity)
