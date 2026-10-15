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
    actions = request.user.agent_actions.all()
    context = {
        'actions': actions,
        'pending_count': actions.filter(status='pending').count(),
    }
    return render(request, 'agent_hub/actions.html', context)


@login_required
def action_detail(request, pk):
    action = get_object_or_404(AgentAction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        feedback = request.POST.get('feedback', '')
        if decision == 'approve':
            action.approve(feedback)
            messages.success(request, f"Action #{action.id} '{action.title}' approved!")
            # Add audit entry
            AIAuditLog.objects.create(
                user=request.user,
                action_type="human_approval_granted",
                provider="human_in_the_loop",
                summary=f"Human approved action: {action.title}",
                output_summary=feedback or "Approved without additional comments.",
                status="success"
            )
        elif decision == 'reject':
            action.reject(feedback)
            messages.warning(request, f"Action #{action.id} rejected.")
            AIAuditLog.objects.create(
                user=request.user,
                action_type="human_approval_rejected",
                provider="human_in_the_loop",
                summary=f"Human rejected action: {action.title}",
                output_summary=feedback or "Rejected by applicant.",
                status="warning"
            )
        return redirect('agent_hub:action_list')

    return render(request, 'agent_hub/action_detail.html', {'action': action})


@login_required
def audit_log_view(request):
    logs = request.user.ai_audit_logs.all()
    context = {
        'logs': logs,
        'total_count': logs.count(),
    }
    return render(request, 'agent_hub/audit_log.html', context)
