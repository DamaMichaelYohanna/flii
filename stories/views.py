from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Story

@login_required
def story_list(request):
    user = request.user
    category = request.GET.get('category', '')
    
    stories = user.stories.all()
    if category:
        stories = stories.filter(category=category)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            Story.objects.create(
                user=user,
                category=request.POST.get('category', 'leadership'),
                title=title,
                situation=request.POST.get('situation', ''),
                challenge=request.POST.get('challenge', ''),
                action=request.POST.get('action', ''),
                result=request.POST.get('result', ''),
                lesson_learned=request.POST.get('lesson_learned', ''),
                skills_demonstrated=request.POST.get('skills_demonstrated', ''),
                supporting_evidence=request.POST.get('supporting_evidence', '')
            )
            messages.success(request, f"Story '{title}' added to your Story Bank.")
            return redirect('stories:list')

    context = {
        'stories': stories,
        'selected_category': category,
        'categories': Story.CATEGORY_CHOICES,
        'total_count': stories.count(),
    }
    return render(request, 'stories/list.html', context)


@login_required
def story_delete(request, pk):
    story = get_object_or_404(Story, pk=pk, user=request.user)
    title = story.title
    story.delete()
    messages.info(request, f"Story '{title}' deleted from Story Bank.")
    return redirect('stories:list')
