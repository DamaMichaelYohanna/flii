from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from applicants.models import ApplicantProfile, Education, StudyGoal, Skill
from stories.models import Story

def landing_page_view(request):
    return render(request, 'accounts/landing.html', {'hide_app_shell': True})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_email_verified = True  # Verified for MVP
            user.save()
            
            # Initialize empty profile
            ApplicantProfile.objects.create(
                user=user,
                country_of_origin='Nigeria',
                nationality='Nigerian'
            )
            
            login(request, user)
            messages.success(request, f"Welcome to Flii, {user.first_name}! Let's build your applicant profile.")
            return redirect('accounts:onboarding')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form, 'hide_app_shell': True})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if not user.onboarding_completed:
                return redirect('accounts:onboarding')
            return redirect('dashboard:index')
        else:
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                raw_email = request.POST.get('username', '').strip()
                from django.contrib.auth import get_user_model
                U = get_user_model()
                matched = U.objects.filter(email__iexact=raw_email).first()
                print("\n" + "=" * 70)
                print(f"  [FLII DEV LOGIN ATTEMPT FAILED]")
                print(f"  Submitted email: '{raw_email}'")
                if matched:
                    print(f"  Account found: {matched.email} (is_active: {matched.is_active})")
                    print(f"  Password check: FAILED (The submitted password did not match the stored hash)")
                else:
                    print(f"  NO USER FOUND with email matching '{raw_email}'")
                    print(f"  Existing emails in DB: {[u.email for u in U.objects.all()]}")
                print("=" * 70 + "\n")
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form, 'hide_app_shell': True})

from django.urls import reverse
from .oauth import GoogleOAuthService

def google_login_view(request):
    """
    Redirects the applicant to Google's OAuth2 consent screen.
    Currently paused (coming soon).
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    messages.info(request, "Google Sign-In is coming soon! Please sign in or register with your email.")
    return redirect('accounts:login')


def google_callback_view(request):
    """
    Handles the Google OAuth2 callback, verifies state, exchanges code for user profile,
    provisions the user, and initiates the session.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    error = request.GET.get('error')
    if error:
        messages.error(request, f"Google authentication was cancelled or failed: {error}")
        return redirect('accounts:login')

    code = request.GET.get('code')
    state = request.GET.get('state')
    expected_state = request.session.get('google_oauth_state')

    if not code or not state or state != expected_state:
        messages.error(request, "Google authentication session validation failed. Please try again.")
        return redirect('accounts:login')

    # Clear state from session
    request.session.pop('google_oauth_state', None)

    oauth = GoogleOAuthService()
    redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
    
    tokens = oauth.exchange_code_for_tokens(code, redirect_uri)
    if not tokens or 'access_token' not in tokens:
        messages.error(request, "Failed to retrieve access token from Google. Please verify credentials.")
        return redirect('accounts:login')

    google_info = oauth.fetch_user_info(tokens['access_token'])
    if not google_info or not google_info.get('email'):
        messages.error(request, "Could not retrieve your verified Google email address.")
        return redirect('accounts:login')

    try:
        user, created = oauth.get_or_create_user(google_info)
        login(request, user)
        if created:
            messages.success(request, f"Welcome to Flii, {user.first_name}! Your Google account is verified.")
            return redirect('accounts:onboarding')
        else:
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if not user.onboarding_completed:
                return redirect('accounts:onboarding')
            return redirect('dashboard:index')
    except Exception as e:
        messages.error(request, f"Failed to authenticate user: {str(e)}")
        return redirect('accounts:login')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:landing')


from documents.models import Document
from applicants.models import Employment, Project, Achievement

@login_required
def onboarding_view(request):
    profile, _ = ApplicantProfile.objects.get_or_create(user=request.user)
    step = int(request.GET.get('step', 1))

    if request.method == 'POST':
        current_step = int(request.POST.get('step', 1))

        if current_step == 1:
            # Step 1: Personal Information
            profile.middle_name = request.POST.get('middle_name', '')
            profile.phone = request.POST.get('phone', '')
            profile.country_of_origin = request.POST.get('country_of_origin', 'Nigeria')
            profile.nationality = request.POST.get('nationality', 'Nigerian')
            profile.gender = request.POST.get('gender', '')
            profile.current_location = request.POST.get('current_location', '')
            profile.headline = request.POST.get('headline', '')
            profile.save()
            return redirect('/onboarding/?step=2')

        elif current_step == 2:
            # Step 2: Education
            inst = request.POST.get('institution', '').strip()
            if inst:
                Education.objects.create(
                    profile=profile,
                    institution=inst,
                    country=request.POST.get('edu_country', 'Nigeria'),
                    degree_level=request.POST.get('degree_level', 'bachelors'),
                    field_of_study=request.POST.get('field_of_study', ''),
                    graduation_year=int(request.POST.get('graduation_year', 2024)) if request.POST.get('graduation_year') else None,
                    grade_classification=request.POST.get('grade_classification', ''),
                    cgpa=float(request.POST.get('cgpa')) if request.POST.get('cgpa') else None,
                    max_cgpa=float(request.POST.get('max_cgpa', 5.0)) if request.POST.get('max_cgpa') else 5.0,
                    relevant_coursework=request.POST.get('relevant_coursework', '')
                )
            return redirect('/onboarding/?step=3')

        elif current_step == 3:
            # Step 3: Employment / Experience
            org = request.POST.get('organization', '').strip()
            if org:
                Employment.objects.create(
                    profile=profile,
                    organization=org,
                    job_title=request.POST.get('job_title', ''),
                    location=request.POST.get('location', ''),
                    is_current=request.POST.get('is_current') == 'on',
                    responsibilities=request.POST.get('responsibilities', ''),
                    achievements=request.POST.get('achievements', '')
                )
            return redirect('/onboarding/?step=4')

        elif current_step == 4:
            # Step 4: Achievements & Projects
            proj_title = request.POST.get('project_title', '').strip()
            if proj_title:
                Project.objects.create(
                    profile=profile,
                    title=proj_title,
                    role=request.POST.get('project_role', ''),
                    technologies=request.POST.get('technologies', ''),
                    description=request.POST.get('project_description', ''),
                    outcome=request.POST.get('project_outcome', '')
                )
            return redirect('/onboarding/?step=5')

        elif current_step == 5:
            # Step 5: Study Goals
            StudyGoal.objects.update_or_create(
                profile=profile,
                defaults={
                    'target_degree': request.POST.get('target_degree', "Master's (MSc)"),
                    'target_fields': request.POST.get('target_fields', ''),
                    'target_countries': request.POST.get('target_countries', ''),
                    'funding_preference': request.POST.get('funding_preference', 'fully_funded'),
                    'career_goals': request.POST.get('career_goals', ''),
                }
            )
            return redirect('/onboarding/?step=6')

        elif current_step == 6:
            # Step 6: Core Documents Upload
            uploaded_cv = request.FILES.get('cv_file')
            if uploaded_cv:
                Document.objects.create(
                    user=request.user,
                    title=f"{request.user.first_name or 'Applicant'} Academic CV",
                    document_type='cv',
                    file=uploaded_cv,
                    verification_status='verified'
                )
            uploaded_transcript = request.FILES.get('transcript_file')
            if uploaded_transcript:
                Document.objects.create(
                    user=request.user,
                    title=f"Official Academic Transcript",
                    document_type='transcript',
                    file=uploaded_transcript,
                    verification_status='verified'
                )
            uploaded_cert = request.FILES.get('cert_file')
            if uploaded_cert:
                Document.objects.create(
                    user=request.user,
                    title=f"Degree Certificate / Statement of Result",
                    document_type='degree_certificate',
                    file=uploaded_cert,
                    verification_status='verified'
                )
            return redirect('/onboarding/?step=7')

        elif current_step == 7:
            # Step 7: Initial Story Bank Entry
            title = request.POST.get('story_title', '').strip()
            if title:
                Story.objects.create(
                    user=request.user,
                    category=request.POST.get('story_category', 'leadership'),
                    title=title,
                    situation=request.POST.get('situation', ''),
                    challenge=request.POST.get('challenge', ''),
                    action=request.POST.get('action', ''),
                    result=request.POST.get('result', ''),
                    lesson_learned=request.POST.get('lesson_learned', ''),
                    skills_demonstrated=request.POST.get('skills_demonstrated', '')
                )

            # Mark onboarding complete
            request.user.onboarding_completed = True
            request.user.save()
            messages.success(request, "🎉 Your profile and Document Vault are ready! Explore verified scholarship matches.")
            return redirect('dashboard:index')

    context = {
        'profile': profile,
        'step': step,
        'hide_app_shell': True
    }
    return render(request, 'accounts/onboarding.html', context)

