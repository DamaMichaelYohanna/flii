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
            user.is_email_verified = False  # Requires email verification
            user.save()
            
            # Initialize empty profile
            ApplicantProfile.objects.create(
                user=user,
                country_of_origin='Nigeria',
                nationality='Nigerian'
            )
            
            login(request, user)

            # Dispatch confirmation email
            from .emails import send_verification_email
            email_sent = send_verification_email(request, user)
            if email_sent:
                messages.success(request, f"Welcome to Flii, {user.first_name}! We sent a confirmation link to {user.email}.")
            else:
                messages.info(request, f"Welcome to Flii, {user.first_name}! Let's build your applicant profile.")
            
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


from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

def verify_email_view(request, uidb64, token):
    User = get_user_model()
    user = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.filter(pk=uid).first()
    except (TypeError, ValueError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        messages.success(request, "🎉 Your email address has been successfully verified! Your Flii workspace is now fully secured.")

        if request.user.is_authenticated and request.user.pk == user.pk:
            if not request.user.onboarding_completed:
                return redirect('accounts:onboarding')
            return redirect('dashboard:index')

        return render(request, 'accounts/verify_email_success.html', {'verified_user': user, 'hide_app_shell': True})
    else:
        return render(request, 'accounts/verify_email_failed.html', {'hide_app_shell': True})


def resend_verification_view(request):
    User = get_user_model()

    if request.user.is_authenticated:
        if request.user.is_email_verified:
            messages.info(request, "Your email address is already verified!")
            return redirect('dashboard:index')

        from .emails import send_verification_email
        send_verification_email(request, request.user)
        messages.success(request, f"A fresh verification email has been sent to {request.user.email}. Please check your inbox.")

        next_url = request.META.get('HTTP_REFERER')
        if next_url and next_url.startswith('http'):
            return redirect(next_url)
        return redirect('dashboard:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_email_verified:
            from .emails import send_verification_email
            send_verification_email(request, user)

        messages.success(request, "If an unverified account exists with that email, a verification link has been sent. Please check your inbox.")
        return redirect('accounts:login')

    return render(request, 'accounts/resend_verification.html', {'hide_app_shell': True})


from documents.models import Document
from applicants.models import Employment, Project, Achievement

@login_required
def onboarding_view(request):
    # Support immediate skip via GET ?skip=true or POST action=skip
    if request.GET.get('skip') == 'true' or request.POST.get('action') == 'skip':
        request.user.onboarding_completed = True
        request.user.save(update_fields=['onboarding_completed'])
        messages.success(request, "👋 Welcome to Flii! You can complete your academic profile and upload documents anytime from your settings.")
        return redirect('dashboard:index')

    profile, _ = ApplicantProfile.objects.get_or_create(user=request.user)
    study_goal = getattr(profile, 'study_goal', None) if hasattr(profile, 'study_goal') else None
    education = profile.educations.first()

    try:
        step = int(request.GET.get('step', 1))
    except (ValueError, TypeError):
        step = 1

    if step not in (1, 2):
        step = 1

    if request.method == 'POST':
        current_step = int(request.POST.get('step', step))

        if current_step == 1:
            # Step 1: Study Ambitions & Target Goals
            target_degree = request.POST.get('target_degree', "Master's (MSc)").strip()
            target_fields = request.POST.get('target_fields', '').strip()
            target_countries = request.POST.get('target_countries', '').strip()
            funding_preference = request.POST.get('funding_preference', 'fully_funded').strip()
            career_goals = request.POST.get('career_goals', '').strip()

            StudyGoal.objects.update_or_create(
                profile=profile,
                defaults={
                    'target_degree': target_degree,
                    'target_fields': target_fields,
                    'target_countries': target_countries,
                    'funding_preference': funding_preference,
                    'career_goals': career_goals,
                    'long_term_goals': '',
                }
            )
            return redirect('/onboarding/?step=2')

        elif current_step == 2:
            # Step 2: Academic Snapshot & Personal Details
            country_of_origin = request.POST.get('country_of_origin', '').strip() or profile.country_of_origin or 'Nigeria'
            nationality = request.POST.get('nationality', '').strip() or profile.nationality or 'Nigerian'
            profile.country_of_origin = country_of_origin
            profile.nationality = nationality
            profile.phone = request.POST.get('phone', '').strip()
            profile.current_location = request.POST.get('current_location', '').strip()
            profile.headline = request.POST.get('headline', '').strip()
            profile.save()

            inst = request.POST.get('institution', '').strip()
            field = request.POST.get('field_of_study', '').strip()
            if inst or field:
                grade = request.POST.get('grade_classification', '').strip()
                deg_level = request.POST.get('degree_level', 'bachelors').strip()
                cgpa_val = None
                if request.POST.get('cgpa'):
                    try:
                        cgpa_val = float(request.POST.get('cgpa'))
                    except ValueError:
                        pass
                max_cgpa_val = 5.0
                if request.POST.get('max_cgpa'):
                    try:
                        max_cgpa_val = float(request.POST.get('max_cgpa'))
                    except ValueError:
                        pass

                existing_edu = profile.educations.first()
                if existing_edu:
                    existing_edu.institution = inst or existing_edu.institution
                    existing_edu.field_of_study = field or existing_edu.field_of_study
                    existing_edu.degree_level = deg_level
                    existing_edu.grade_classification = grade
                    existing_edu.cgpa = cgpa_val
                    existing_edu.max_cgpa = max_cgpa_val
                    existing_edu.country = country_of_origin
                    existing_edu.save()
                else:
                    Education.objects.create(
                        profile=profile,
                        institution=inst or 'University of Degree',
                        field_of_study=field or 'General Studies',
                        degree_level=deg_level,
                        grade_classification=grade,
                        cgpa=cgpa_val,
                        max_cgpa=max_cgpa_val,
                        country=country_of_origin
                    )

            # Mark onboarding complete
            request.user.onboarding_completed = True
            request.user.save(update_fields=['onboarding_completed'])
            messages.success(request, "🎉 Profile setup complete! Explore scholarships tailored to your ambitions.")
            return redirect('dashboard:index')

    context = {
        'profile': profile,
        'study_goal': study_goal,
        'education': education,
        'step': step,
        'hide_app_shell': True
    }
    return render(request, 'accounts/onboarding.html', context)

