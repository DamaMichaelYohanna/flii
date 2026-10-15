from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import datetime
from opportunities.models import Opportunity
from applications.models import Application, ApplicationTask
from matching.engine import MatchingEngine

@login_required
def dashboard_index(request):
    user = request.user
    now = timezone.now()
    seven_days = now + datetime.timedelta(days=7)
    thirty_days = now + datetime.timedelta(days=30)

    # Core metrics
    total_opportunities = Opportunity.objects.filter(status='active').count()
    shortlisted_count = user.shortlisted_opportunities.count()
    active_applications = user.applications.all()
    in_progress_count = active_applications.exclude(status__in=['submitted', 'rejected', 'withdrawn']).count()
    
    tasks_due = ApplicationTask.objects.filter(
        application__user=user,
        is_completed=False
    ).count()

    deadlines_this_week = Opportunity.objects.filter(
        status='active',
        deadline__gte=now,
        deadline__lte=seven_days
    ).count()

    # Upcoming deadlines (sorted by urgency)
    upcoming_deadlines = Opportunity.objects.filter(
        status='active',
        deadline__gte=now
    ).order_by('deadline')[:5]

    # Matching engine recommendations
    matching_engine = MatchingEngine(user)
    opportunities = Opportunity.objects.filter(status='active')[:8]
    scored_opps = []
    for opp in opportunities:
        fit = matching_engine.calculate_deterministic_fit(opp)
        scored_opps.append({
            'opp': opp,
            'fit': fit
        })
    scored_opps.sort(key=lambda x: x['fit']['score'], reverse=True)
    ai_recommendations = scored_opps[:4]

    # Pending human approval actions
    pending_actions = user.agent_actions.filter(status='pending')[:3]

    # Tasks due list
    urgent_tasks = ApplicationTask.objects.filter(
        application__user=user,
        is_completed=False
    ).order_by('due_date')[:5]

    context = {
        'total_opportunities': total_opportunities,
        'shortlisted_count': shortlisted_count,
        'in_progress_count': in_progress_count,
        'tasks_due': tasks_due,
        'deadlines_this_week': deadlines_this_week,
        'active_applications': active_applications[:4],
        'upcoming_deadlines': upcoming_deadlines,
        'ai_recommendations': ai_recommendations,
        'pending_actions': pending_actions,
        'urgent_tasks': urgent_tasks,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def admin_system_dashboard(request):
    """
    Central System Executive Admin Dashboard:
    Aggregates high-level metrics across all core modules:
    - User registrations, onboarding progression, and staff privileges
    - Opportunities, scout engine staging queue, and official sources
    - Application pipeline lifecycle (Planning -> Offer)
    - Document vault and Story bank repository assets
    - AI governance, human approval actions, and audit logs
    """
    if not request.user.is_staff:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.warning(request, "Staff privileges required to access the System Admin Dashboard.")
        return redirect('dashboard:index')

    from accounts.models import User
    from opportunities.models import Opportunity, OpportunitySource
    from applications.models import Application, ApplicationTask
    from documents.models import Document
    from stories.models import Story
    from agent_hub.models import AgentAction, AIAuditLog
    from django.db.models import Count

    # User Metrics
    total_users = User.objects.count()
    onboarded_users = User.objects.filter(onboarding_completed=True).count()
    staff_users_count = User.objects.filter(is_staff=True).count()
    recent_users = User.objects.all().order_by('-date_joined')[:6]

    # Opportunity & Scout Metrics
    total_opportunities = Opportunity.objects.count()
    active_opportunities = Opportunity.objects.filter(status='active', verification_status='source_verified').count()
    staged_opportunities = Opportunity.objects.filter(verification_status='needs_review').count()
    total_sources = OpportunitySource.objects.count()
    active_sources = OpportunitySource.objects.filter(is_active=True).count()

    # Application Pipeline Metrics
    total_applications = Application.objects.count()
    applications_by_status = {
        'planning': Application.objects.filter(status='planning').count(),
        'preparing': Application.objects.filter(status='preparing').count(),
        'in_progress': Application.objects.filter(status='in_progress').count(),
        'ready_for_review': Application.objects.filter(status='ready_for_review').count(),
        'submitted': Application.objects.filter(status='submitted').count(),
        'offer': Application.objects.filter(status='offer').count(),
        'rejected': Application.objects.filter(status='rejected').count(),
    }
    submitted_applications = applications_by_status['submitted']
    offer_applications = applications_by_status['offer']
    recent_applications = Application.objects.select_related('user', 'opportunity').order_by('-created_at')[:6]

    # Task & Document Metrics
    total_tasks = ApplicationTask.objects.count()
    completed_tasks = ApplicationTask.objects.filter(is_completed=True).count()
    total_documents = Document.objects.count()
    total_stories = Story.objects.count()

    # Document classification breakdown
    doc_types = (
        Document.objects.values('document_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # AI Governance Metrics
    total_agent_actions = AgentAction.objects.count()
    pending_agent_actions = AgentAction.objects.filter(status='pending').count()
    approved_agent_actions = AgentAction.objects.filter(status='approved').count()
    total_audit_logs = AIAuditLog.objects.count()
    recent_audit_logs = AIAuditLog.objects.select_related('user').order_by('-created_at')[:8]

    context = {
        'total_users': total_users,
        'onboarded_users': onboarded_users,
        'staff_users_count': staff_users_count,
        'onboarding_rate': int((onboarded_users / total_users * 100)) if total_users > 0 else 0,
        'recent_users': recent_users,

        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'staged_opportunities': staged_opportunities,
        'total_sources': total_sources,
        'active_sources': active_sources,

        'total_applications': total_applications,
        'applications_by_status': applications_by_status,
        'submitted_applications': submitted_applications,
        'offer_applications': offer_applications,
        'recent_applications': recent_applications,

        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'total_documents': total_documents,
        'total_stories': total_stories,
        'doc_types': doc_types,

        'total_agent_actions': total_agent_actions,
        'pending_agent_actions': pending_agent_actions,
        'approved_agent_actions': approved_agent_actions,
        'total_audit_logs': total_audit_logs,
        'recent_audit_logs': recent_audit_logs,
    }
    return render(request, 'dashboard/admin_system.html', context)


@login_required
def admin_users_view(request):
    """
    User Management Console:
    View, filter, search, and manage user accounts and staff privileges.
    """
    if not request.user.is_staff:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.warning(request, "Staff privileges required.")
        return redirect('dashboard:index')

    from accounts.models import User
    from django.db.models import Count, Q

    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    onboarding = request.GET.get('onboarding', '')

    users_qs = User.objects.annotate(
        apps_count=Count('applications', distinct=True),
        docs_count=Count('documents', distinct=True),
        stories_count=Count('stories', distinct=True)
    ).order_by('-date_joined')

    if q:
        users_qs = users_qs.filter(
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(username__icontains=q)
        )

    if role == 'staff':
        users_qs = users_qs.filter(is_staff=True)
    elif role == 'applicant':
        users_qs = users_qs.filter(is_staff=False)

    if onboarding == 'completed':
        users_qs = users_qs.filter(onboarding_completed=True)
    elif onboarding == 'pending':
        users_qs = users_qs.filter(onboarding_completed=False)

    context = {
        'users_list': users_qs,
        'total_users': users_qs.count(),
        'query': q,
        'selected_role': role,
        'selected_onboarding': onboarding,
    }
    return render(request, 'dashboard/admin_users.html', context)


@login_required
def admin_toggle_user_staff(request, user_id):
    """
    Toggles a user's staff/admin status.
    """
    if not request.user.is_staff:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from accounts.models import User
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from django.http import JsonResponse

    target_user = get_object_or_404(User, id=user_id)

    # Protect the active superuser from accidentally revoking their own staff access
    if target_user == request.user and target_user.is_superuser:
        messages.warning(request, "You cannot revoke your own staff status.")
        return redirect('dashboard:admin_users')

    target_user.is_staff = not target_user.is_staff
    target_user.save(update_fields=['is_staff'])

    state_str = "granted staff privileges to" if target_user.is_staff else "revoked staff privileges from"
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'user_id': target_user.id,
            'is_staff': target_user.is_staff,
            'message': f"Successfully {state_str} {target_user.email}."
        })

    messages.success(request, f"Successfully {state_str} {target_user.email}.")
    return redirect('dashboard:admin_users')


@login_required
def admin_applications_view(request):
    """
    System Applications Pipeline Console:
    Monitor all applications, requirements, and progress across all applicants.
    """
    if not request.user.is_staff:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.warning(request, "Staff privileges required.")
        return redirect('dashboard:index')

    from applications.models import Application
    from django.db.models import Q

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    apps_qs = Application.objects.select_related('user', 'opportunity').order_by('-updated_at')

    if q:
        apps_qs = apps_qs.filter(
            Q(user__email__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(opportunity__title__icontains=q) |
            Q(opportunity__provider__icontains=q)
        )

    if status_filter:
        apps_qs = apps_qs.filter(status=status_filter)

    context = {
        'applications': apps_qs,
        'total_count': apps_qs.count(),
        'query': q,
        'selected_status': status_filter,
        'status_choices': Application.STATUS_CHOICES,
    }
    return render(request, 'dashboard/admin_applications.html', context)

