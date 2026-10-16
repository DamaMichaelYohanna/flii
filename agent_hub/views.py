from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import AgentAction, AIAuditLog
from .agent import FliiAgent


@login_required
def agent_chat_view(request):
    return redirect('dashboard:index')


@login_required
def action_list(request):
    return redirect('dashboard:index')


@login_required
def action_detail(request, pk):
    return redirect('dashboard:index')


@login_required
def audit_log_view(request):
    logs = request.user.ai_audit_logs.all()
    context = {
        'logs': logs,
        'total_count': logs.count(),
    }
    return render(request, 'agent_hub/audit_log.html', context)
