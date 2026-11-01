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
        Fast multi-factor deterministic matching engine.
        Evaluates Degree Level, Academic Standing, Field Affinity, Nationality/Region,
        Work Experience, and Geographic Preference with realistic, grounded variance.
        """
        reasons = []

        if not self.profile:
            return {
                "score": 45,
                "status": "needs_clarification",
                "label": "Profile Incomplete",
                "color": "amber",
                "reasons": ["Complete your profile to see tailored match scores."]
            }

        study_goal = getattr(self.profile, 'study_goal', None)
        educations = list(self.profile.educations.all()) if hasattr(self.profile, 'educations') else []
        employments = list(self.profile.employments.all()) if hasattr(self.profile, 'employments') else []
        skills = list(self.profile.skills.all()) if hasattr(self.profile, 'skills') else []

        has_education = len(educations) > 0
        has_goal = study_goal is not None

        # -------------------------------------------------------------
        # 1. Degree Level Alignment (Max 22 pts)
        # -------------------------------------------------------------
        target_degree = (study_goal.target_degree if has_goal and study_goal.target_degree else "masters").lower()
        opp_degree = (opportunity.degree_level or "").lower()

        if opp_degree in target_degree or ("master" in opp_degree and "master" in target_degree):
            deg_score = 22
            reasons.append(f"Matches target degree level ({opportunity.get_degree_level_display()}).")
        elif "fellowship" in opp_degree:
            deg_score = 14
            reasons.append("Fellowship / Research format.")
        elif "phd" in opp_degree:
            deg_score = 18 if ("phd" in target_degree or "doctorate" in target_degree) else 8
        else:
            deg_score = 12

        # -------------------------------------------------------------
        # 2. Field of Study Alignment (Max 26 pts)
        # -------------------------------------------------------------
        opp_field = (opportunity.field_of_study or "").lower()
        is_all_fields = any(p in opp_field for p in ["all academic", "all master", "all full-time", "all subjects", "open to all"])

        user_field_tokens = set()
        if has_goal and study_goal.target_fields:
            user_field_tokens.update(re.findall(r'[a-zA-Z]{3,}', study_goal.target_fields.lower()))
        for edu in educations:
            user_field_tokens.update(re.findall(r'[a-zA-Z]{3,}', (edu.field_of_study or "").lower()))
        for sk in skills:
            user_field_tokens.update(re.findall(r'[a-zA-Z]{3,}', (sk.name or "").lower()))

        if is_all_fields:
            field_score = 24
            reasons.append("Open to all academic disciplines.")
        elif user_field_tokens:
            opp_tokens = set(re.findall(r'[a-zA-Z]{3,}', opp_field)) - {'and', 'the', 'for', 'with', 'all', 'available', 'degree', 'courses', 'programmes', 'studies'}
            common = user_field_tokens.intersection(opp_tokens)
            if common:
                field_score = 26
                reasons.append(f"Direct subject match ({', '.join(list(common)[:3])}).")
            else:
                stem_keywords = {'computer', 'science', 'technology', 'engineering', 'data', 'robotics', 'ai', 'software', 'informatics'}
                if user_field_tokens.intersection(stem_keywords) and opp_tokens.intersection(stem_keywords):
                    field_score = 20
                    reasons.append("Related STEM field discipline overlap.")
                else:
                    field_score = 8
        else:
            if is_all_fields:
                field_score = 20
                reasons.append("Open to all disciplines (add field in Profile).")
            elif any(k in opp_field for k in ['computer', 'engineering', 'data']):
                field_score = 14
            elif any(k in opp_field for k in ['development', 'health', 'policy', 'conflict']):
                field_score = 16
            else:
                field_score = 11

        # -------------------------------------------------------------
        # 3. Academic Standing & GPA Threshold (Max 20 pts)
        # -------------------------------------------------------------
        opp_acad = (opportunity.academic_requirement or "").lower()
        requires_first_class = any(term in opp_acad for term in ["first class", "top 10", "grade a", "outstanding academic"])

        if has_education:
            user_has_first = any(
                'first' in (e.grade_classification or '').lower() or
                (e.cgpa and e.max_cgpa and (float(e.cgpa) / float(e.max_cgpa)) >= 0.88) or
                (e.cgpa and not e.max_cgpa and float(e.cgpa) >= 4.5)
                for e in educations
            )
            user_has_second_upper = any(
                'upper' in (e.grade_classification or '').lower() or
                '2:1' in (e.grade_classification or '').lower() or
                (e.cgpa and e.max_cgpa and (float(e.cgpa) / float(e.max_cgpa)) >= 0.70) or
                (e.cgpa and not e.max_cgpa and float(e.cgpa) >= 3.5)
                for e in educations
            )

            if user_has_first:
                acad_score = 20
                reasons.append("First Class / Distinction satisfies competitive threshold.")
            elif user_has_second_upper:
                if requires_first_class:
                    acad_score = 13
                    reasons.append("Second Class Upper (competitive, First Class preferred).")
                else:
                    acad_score = 18
                    reasons.append("Academic degree satisfies 2:1 honours prerequisite.")
            else:
                acad_score = 8
        else:
            acad_score = 9 if requires_first_class else (13 if any(k in opp_acad for k in ['second class', '2:1']) else 14)

        # -------------------------------------------------------------
        # 4. Nationality & Regional Eligibility (Max 16 pts)
        # -------------------------------------------------------------
        opp_nat = (opportunity.nationality_requirement or "").lower()
        user_nat = (self.profile.nationality or "Nigerian").lower()
        user_country = (self.profile.country_of_origin or "Nigeria").lower()
        is_nigerian = "nigeri" in user_nat or "nigeri" in user_country

        if is_nigerian and any(k in opp_nat for k in ["nigeria", "commonwealth", "dac", "developing", "sub-saharan", "african"]):
            nat_score = 16
            reasons.append("Nationality is explicitly prioritized for funding.")
        elif any(k in opp_nat for k in ["all nationalities", "open to all", "global", "worldwide"]):
            nat_score = 14
            reasons.append("Open to all international nationalities.")
        elif is_nigerian and "non-french" in opp_nat:
            nat_score = 15
            reasons.append("Eligible international applicant.")
        else:
            nat_score = 10

        # -------------------------------------------------------------
        # 5. Work Experience Prerequisite (Max 10 pts)
        # -------------------------------------------------------------
        opp_exp = (opportunity.work_experience_requirement or "").lower()
        requires_exp = any(term in opp_exp for term in ["2 years", "3 years", "2,800", "3,000", "relevant work", "professional experience"])

        if employments:
            exp_score = 10
            if requires_exp:
                reasons.append("Employment record satisfies professional experience prerequisite.")
        else:
            exp_score = 4 if requires_exp else 9

        # -------------------------------------------------------------
        # 6. Destination Country / Region Alignment (Max 6 pts)
        # -------------------------------------------------------------
        opp_country = (opportunity.country or "").lower()
        if has_goal and study_goal.target_countries:
            targets = study_goal.target_countries.lower()
            if opp_country in targets:
                country_score = 6
                reasons.append(f"Matches preferred study destination ({opportunity.country}).")
            elif "europe" in targets and any(c in opp_country for c in ["germany", "switzerland", "france", "belgium", "sweden", "united kingdom", "eu"]):
                country_score = 5
                reasons.append(f"European destination alignment ({opportunity.country}).")
            else:
                country_score = 2
        else:
            country_score = 4

        raw_score = deg_score + field_score + acad_score + nat_score + exp_score + country_score
        
        # Add deterministic pseudo-variation based on opportunity ID to avoid identical ties (±2 pts)
        salt = ((opportunity.id * 7 + (self.user.id or 1) * 13) % 5) - 2
        final_score = min(98, max(25, raw_score + salt))

        if final_score >= 80:
            status = "likely_eligible"
            label = "High Fit"
            color = "emerald"
        elif final_score >= 65:
            status = "likely_eligible"
            label = "Good Fit"
            color = "blue"
        elif final_score >= 50:
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
