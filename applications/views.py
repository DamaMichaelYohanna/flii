from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import Application, ApplicationRequirement, ApplicationTask
from opportunities.models import Opportunity
from documents.models import Document
from ai_core.service import AIService
from agent_hub.agent import ScholarFlowAgent
from .services import AutonomousApplicationAssembler

@login_required
def application_list(request):
    user = request.user
    applications = user.applications.all().order_by('-updated_at')
    
    context = {
        'applications': applications,
        'total_count': applications.count(),
    }
    return render(request, 'applications/list.html', context)


@login_required
def create_from_opportunity(request, opportunity_id):
    agent = ScholarFlowAgent(request.user)
    result = agent.create_application(opportunity_id)
    messages.success(request, f"Application workspace created for '{result['opportunity']}'!")
    return redirect('applications:detail', pk=result['application_id'])


@login_required
def auto_assemble_view(request, pk):
    """
    Triggers one-click autonomous assembly of essays, documents, and dossier.
    """
    application = get_object_or_404(Application, pk=pk, user=request.user)
    assembler = AutonomousApplicationAssembler(application, request.user)
    result = assembler.assemble()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(result)

    messages.success(
        request,
        f"⚡ Autonomous Assembly Complete! Linked {result['attached_docs_count']} vault documents and drafted {result['drafted_essays_count']} personalized essays."
    )
    return redirect('applications:detail', pk=application.id)


@login_required
def application_dossier_view(request, pk):
    """
    Renders the dedicated Fast-Copy Portal Dossier and export packet.
    """
    application = get_object_or_404(Application, pk=pk, user=request.user)
    assembler = AutonomousApplicationAssembler(application, request.user)
    dossier = assembler.build_dossier_data()
    
    context = {
        'application': application,
        'dossier': dossier,
    }
    return render(request, 'applications/dossier.html', context)


@login_required
def application_detail(request, pk):
    user = request.user
    application = get_object_or_404(Application, pk=pk, user=user)
    requirements = application.requirements.all()
    tasks = application.tasks.all()
    user_documents = user.documents.all()

    assembler = AutonomousApplicationAssembler(application, user)
    dossier = assembler.build_dossier_data()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_task':
            title = request.POST.get('task_title', '').strip()
            if title:
                ApplicationTask.objects.create(
                    application=application,
                    title=title,
                    description=request.POST.get('task_desc', ''),
                    due_date=request.POST.get('due_date') or None
                )
                messages.success(request, f"Task '{title}' added.")
            return redirect('applications:detail', pk=application.id)

        elif action == 'update_status':
            new_status = request.POST.get('application_status')
            if new_status in dict(Application.STATUS_CHOICES):
                application.status = new_status
                application.save()
                messages.success(request, f"Application status updated to '{application.get_status_display()}'.")
            return redirect('applications:detail', pk=application.id)

        elif action == 'update_requirement_text':
            req_id = request.POST.get('requirement_id')
            req = get_object_or_404(ApplicationRequirement, id=req_id, application=application)
            req.draft_response = request.POST.get('draft_content', '')
            req.status = request.POST.get('req_status', 'in_progress')
            req.save()
            messages.success(request, f"Saved response for '{req.name}'.")
            return redirect('applications:detail', pk=application.id)

        elif action == 'link_document':
            req_id = request.POST.get('requirement_id')
            doc_id = request.POST.get('document_id')
            req = get_object_or_404(ApplicationRequirement, id=req_id, application=application)
            if doc_id:
                doc = get_object_or_404(Document, id=doc_id, user=user)
                req.attached_document = doc
                req.status = 'complete'
                req.save()
                messages.success(request, f"Attached '{doc.title}' to '{req.name}'.")
            return redirect('applications:detail', pk=application.id)

        elif action == 'request_submission_approval':
            agent = ScholarFlowAgent(user)
            act = agent.request_user_approval(
                action_type='submit_application',
                title=f"Submit Application Package: {application.opportunity.title}",
                description=f"AI has bundled your verified documents ({application.requirements.filter(status='complete').count()} ready) for transmission.",
                payload={'application_id': application.id, 'opportunity': application.opportunity.title}
            )
            messages.info(request, f"Created Human Approval request #{act.id}. Review and confirm to proceed.")
            return redirect('agent_hub:action_detail', pk=act.id)

    essay_requirements = [r for r in requirements if r.is_essay]
    first_essay_req = essay_requirements[0] if essay_requirements else requirements.first()

    context = {
        'application': application,
        'requirements': requirements,
        'tasks': tasks,
        'user_documents': user_documents,
        'dossier': dossier,
        'first_essay_req': first_essay_req,
        'essay_requirements': essay_requirements,
    }
    return render(request, 'applications/detail.html', context)



@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(ApplicationTask, id=task_id, application__user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_completed': task.is_completed})
    return redirect(request.META.get('HTTP_REFERER', 'applications:tasks'))


@login_required
def application_tasks(request):
    user = request.user
    tasks = ApplicationTask.objects.filter(application__user=user).order_by('is_completed', 'due_date')
    context = {
        'tasks': tasks,
        'pending_count': tasks.filter(is_completed=False).count(),
        'completed_count': tasks.filter(is_completed=True).count(),
    }
    return render(request, 'applications/tasks.html', context)


@login_required
def ajax_ai_draft(request):
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        req_id = request.POST.get('requirement_id')
        instructions = request.POST.get('instructions', '')
        tone = request.POST.get('tone', 'formal')

        app = get_object_or_404(Application, id=app_id, user=request.user)
        req = get_object_or_404(ApplicationRequirement, id=req_id, application=app)

        ai_service = AIService.get_instance()
        result = ai_service.draft_essay_response(
            user=request.user,
            opportunity=app.opportunity,
            question_title=req.name,
            prompt_context=instructions,
            tone=tone
        )
        return JsonResponse(result.model_dump())
    return JsonResponse({'error': 'Invalid method'}, status=400)

