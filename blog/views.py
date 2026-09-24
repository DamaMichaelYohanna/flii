from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.http import Http404
from .models import Post, PostCategory
from opportunities.models import Opportunity

def blog_list_view(request):
    """
    Public listing of published insights, breaking migration news,
    and scholarship guides.
    """
    posts = Post.objects.filter(status='published').select_related('category', 'author')
    categories = PostCategory.objects.annotate(
        published_posts_count=Count('posts', filter=Q(posts__status='published'))
    )
    total_published_count = Post.objects.filter(status='published').count()

    # Search query
    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query)
        )

    # Category filter
    category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(PostCategory, slug=category_slug)
        posts = posts.filter(category=selected_category)

    # Tag filter
    tag = request.GET.get('tag', '').strip()
    if tag:
        posts = posts.filter(tags__icontains=tag)

    # Highlighted / Breaking news post (first breaking or pinned post if on page 1 and no search)
    featured_post = None
    if not query and not category_slug and not tag:
        featured_post = posts.filter(Q(is_breaking_news=True) | Q(is_pinned=True)).first()
        if featured_post:
            posts = posts.exclude(pk=featured_post.pk)

    # Pagination: 9 articles per page
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Active opportunities highlight
    featured_opportunities = Opportunity.objects.filter(status='active')[:3]

    context = {
        'page_obj': page_obj,
        'featured_post': featured_post,
        'categories': categories,
        'total_published_count': total_published_count,
        'selected_category': selected_category,
        'query': query,
        'active_tag': tag,
        'featured_opportunities': featured_opportunities,
        'hide_app_shell': not request.user.is_authenticated,
    }
    return render(request, 'blog/list.html', context)


def blog_detail_view(request, slug):
    """
    Full article reading page with related posts and matching scholarships.
    """
    post_qs = Post.objects.select_related('category', 'author')
    if not request.user.is_staff:
        post_qs = post_qs.filter(status='published')

    post = get_object_or_404(post_qs, slug=slug)

    # Increment view counter atomically
    Post.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
    post.refresh_from_db(fields=['views_count'])

    # Related articles in same category
    related_posts = Post.objects.filter(
        status='published',
        category=post.category
    ).exclude(pk=post.pk)[:3] if post.category else Post.objects.filter(status='published').exclude(pk=post.pk)[:3]

    # Matching opportunities to link editorial knowledge with application workspaces
    matching_opportunities = Opportunity.objects.filter(status='active')[:4]

    context = {
        'post': post,
        'related_posts': related_posts,
        'matching_opportunities': matching_opportunities,
        'hide_app_shell': not request.user.is_authenticated,
    }
    return render(request, 'blog/detail.html', context)
