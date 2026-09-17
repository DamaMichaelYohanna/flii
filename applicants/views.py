from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    ApplicantProfile, Education, Employment, Skill, Project,
    Achievement, Certification, ResearchExperience, StudyGoal, LanguageProficiency
)

from documents.models import Document

@login_required
def profile_view(request):
    profile, _ = ApplicantProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_personal':
            profile.middle_name = request.POST.get('middle_name', '')
            profile.phone = request.POST.get('phone', '')
            profile.country_of_origin = request.POST.get('country_of_origin', 'Nigeria')
            profile.nationality = request.POST.get('nationality', 'Nigerian')
            profile.gender = request.POST.get('gender', '')
            profile.current_location = request.POST.get('current_location', '')
            profile.headline = request.POST.get('headline', '')
            profile.bio_summary = request.POST.get('bio_summary', '')
            profile.save()
            messages.success(request, "Personal information updated.")
            return redirect('applicants:profile_view')

        elif action == 'upload_document':
            title = request.POST.get('title', '').strip()
            doc_type = request.POST.get('document_type', 'cv')
            uploaded_file = request.FILES.get('file')
            if uploaded_file and title:
                doc = Document.objects.create(
                    user=request.user,
                    title=title,
                    document_type=doc_type,
                    file=uploaded_file,
                    notes=request.POST.get('notes', ''),
                    verification_status='verified'
                )
                messages.success(request, f"Document '{doc.title}' ({doc.get_document_type_display()}) successfully uploaded!")
            else:
                messages.error(request, "Please provide a document title and select a valid file.")
            return redirect('applicants:profile_view')

        elif action == 'add_education':
            Education.objects.create(
                profile=profile,
                institution=request.POST.get('institution'),
                country=request.POST.get('country', 'Nigeria'),
                degree_level=request.POST.get('degree_level', 'bachelors'),
                field_of_study=request.POST.get('field_of_study'),
                graduation_year=int(request.POST.get('graduation_year', 2024)) if request.POST.get('graduation_year') else None,
                grade_classification=request.POST.get('grade_classification', ''),
                cgpa=float(request.POST.get('cgpa')) if request.POST.get('cgpa') else None,
                max_cgpa=float(request.POST.get('max_cgpa', 5.0)) if request.POST.get('max_cgpa') else 5.0,
                relevant_coursework=request.POST.get('relevant_coursework', '')
            )
            messages.success(request, "Education record added.")
            return redirect('applicants:profile_view')

        elif action == 'add_employment':
            Employment.objects.create(
                profile=profile,
                organization=request.POST.get('organization'),
                job_title=request.POST.get('job_title'),
                location=request.POST.get('location', ''),
                is_current=request.POST.get('is_current') == 'on',
                responsibilities=request.POST.get('responsibilities', ''),
                achievements=request.POST.get('achievements', '')
            )
            messages.success(request, "Employment record added.")
            return redirect('applicants:profile_view')

        elif action == 'update_goals':
            StudyGoal.objects.update_or_create(
                profile=profile,
                defaults={
                    'target_degree': request.POST.get('target_degree', "Master's (MSc)"),
                    'target_fields': request.POST.get('target_fields', ''),
                    'target_countries': request.POST.get('target_countries', ''),
                    'funding_preference': request.POST.get('funding_preference', 'fully_funded'),
                    'career_goals': request.POST.get('career_goals', ''),
                    'long_term_goals': request.POST.get('long_term_goals', ''),
                }
            )
            messages.success(request, "Study goals updated.")
            return redirect('applicants:profile_view')

    educations = profile.educations.all()
    employments = profile.employments.all()
    skills = profile.skills.all()
    projects = profile.projects.all()
    achievements = profile.achievements.all()
    certifications = profile.certifications.all()
    research = getattr(profile, 'research_profile', None)
    goal = getattr(profile, 'study_goal', None)
    languages = profile.languages.all()
    documents = request.user.documents.all()

    context = {
        'profile': profile,
        'educations': educations,
        'employments': employments,
        'skills': skills,
        'projects': projects,
        'achievements': achievements,
        'certifications': certifications,
        'research': research,
        'goal': goal,
        'languages': languages,
        'documents': documents,
        'doc_types': Document.DOCUMENT_TYPES,
    }
    return render(request, 'applicants/profile.html', context)

