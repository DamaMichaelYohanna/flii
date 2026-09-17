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
