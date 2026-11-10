import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator

from accounts.models import User
from blog.models import Post, PostCategory
from opportunities.models import Opportunity, OpportunitySource
from assistance.models import AssistanceBooking, AssistancePackage
from subscriptions.models import Subscription, SubscriptionPlan, PaymentTransaction
from applications.models import Application, ApplicationTask
from documents.models import Document
from stories.models import Story
from agent_hub.models import AgentAction, AIAuditLog
from notifications.models import Notification

from .forms import BlogPostForm, OpportunityForm, PostCategoryForm


def staff_required(view_func):
    """Decorator ensuring only active staff members access the admin portal."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_staff:
            messages.error(request, "Access denied: Staff privileges required to access the Platform Admin Portal.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==============================================================================
# 1. EXECUTIVE COMMAND CENTER / OVERVIEW
# ==============================================================================

@staff_required
def dashboard_view(request):
    """
    Central Executive Admin Dashboard: Real-time platform pulse, key metrics,
    financial performance, recent applications, and system telemetry.
    """
    # High-level KPIs
    total_users = User.objects.count()
    onboarded_users = User.objects.filter(onboarding_completed=True).count()
    staff_count = User.objects.filter(is_staff=True).count()
    
    total_opportunities = Opportunity.objects.count()
    active_opportunities = Opportunity.objects.filter(status='active', verification_status='source_verified').count()
    staged_opportunities = Opportunity.objects.filter(verification_status='needs_review').count()

    total_applications = Application.objects.count()
    submitted_applications = Application.objects.filter(status__in=['submitted', 'offer']).count()

    total_blog_posts = Post.objects.count()
    published_blog_posts = Post.objects.filter(status='published').count()

    # Financial / Paid Requests KPIs
    paid_bookings_count = AssistanceBooking.objects.filter(payment_status='paid').count()
    pending_bookings_count = AssistanceBooking.objects.filter(payment_status__in=['pending_verification', 'unpaid']).count()
    
    revenue_bookings = AssistanceBooking.objects.filter(payment_status='paid').aggregate(total=Sum('price'))['total'] or Decimal('0.00')
    successful_txs = PaymentTransaction.objects.filter(status='success')
    tx_count = successful_txs.count()

    # Recent Streams
    recent_users = User.objects.all().order_by('-date_joined')[:6]
    recent_bookings = AssistanceBooking.objects.select_related('user', 'package').order_by('-created_at')[:5]
    recent_applications = Application.objects.select_related('user', 'opportunity').order_by('-created_at')[:5]
    recent_audit_logs = AIAuditLog.objects.select_related('user').order_by('-created_at')[:6]

    context = {
        'total_users': total_users,
        'onboarded_users': onboarded_users,
        'onboarding_rate': int((onboarded_users / total_users * 100)) if total_users > 0 else 0,
        'staff_count': staff_count,

        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'staged_opportunities': staged_opportunities,

        'total_applications': total_applications,
        'submitted_applications': submitted_applications,

        'total_blog_posts': total_blog_posts,
        'published_blog_posts': published_blog_posts,

        'paid_bookings_count': paid_bookings_count,
        'pending_bookings_count': pending_bookings_count,
        'revenue_bookings': revenue_bookings,
        'successful_transactions_count': tx_count,

        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'recent_applications': recent_applications,
        'recent_audit_logs': recent_audit_logs,
    }
    return render(request, 'platform_admin/dashboard.html', context)


# ==============================================================================
# 2. BLOG MANAGEMENT MODULE ("POST BLOGS")
# ==============================================================================

@staff_required
def blog_list(request):
    """Lists all blog articles with filtering, search, view metrics, and quick status toggles."""
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    search_q = request.GET.get('q', '').strip()

    posts = Post.objects.select_related('author', 'category').order_by('-created_at')

    if status_filter != 'all':
        posts = posts.filter(status=status_filter)
    if category_filter != 'all':
        posts = posts.filter(category__slug=category_filter)
    if search_q:
        posts = posts.filter(
            Q(title__icontains=search_q) |
            Q(summary__icontains=search_q) |
            Q(tags__icontains=search_q)
        )

    categories = PostCategory.objects.all().order_by('name')
    total_count = posts.count()
    published_count = Post.objects.filter(status='published').count()
    draft_count = Post.objects.filter(status='draft').count()

    paginator = Paginator(posts, 15)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page,
        'categories': categories,
        'current_status': status_filter,
        'current_category': category_filter,
        'search_q': search_q,
        'total_count': total_count,
        'published_count': published_count,
        'draft_count': draft_count,
    }
    return render(request, 'platform_admin/blogs/list.html', context)


@staff_required
def blog_create(request):
    """Create a new blog article with title, categories, markdown/body content, and cover image."""
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, f"✨ Blog post '{post.title}' created successfully!")
            return redirect('platform_admin:blog_list')
    else:
        form = BlogPostForm(initial={'status': 'published'})

    categories = PostCategory.objects.all()
    return render(request, 'platform_admin/blogs/form.html', {
        'form': form,
        'is_edit': False,
        'categories': categories,
    })


@staff_required
def blog_edit(request, pk):
    """Edit an existing blog article."""
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Blog post '{post.title}' updated successfully!")
            return redirect('platform_admin:blog_list')
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'platform_admin/blogs/form.html', {
        'form': form,
        'post': post,
        'is_edit': True,
    })


@staff_required
def blog_delete(request, pk):
    """Delete a blog post."""
    post = get_object_or_404(Post, pk=pk)
    title = post.title
    if request.method == 'POST':
        post.delete()
        messages.success(request, f"🗑️ Deleted blog post '{title}'.")
        return redirect('platform_admin:blog_list')
    return render(request, 'platform_admin/blogs/confirm_delete.html', {'post': post})


@staff_required
def blog_toggle_status(request, pk):
    """Quick 1-click toggle between Published and Draft."""
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=pk)
        post.status = 'draft' if post.status == 'published' else 'published'
        post.save(update_fields=['status'])
        messages.success(request, f"Updated status of '{post.title}' to {post.get_status_display()}.")
    return redirect('platform_admin:blog_list')


@staff_required
def blog_category_list(request):
    """View and manage all blog categories with article counts and add new category form."""
    if request.method == 'POST':
        form = PostCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"✨ Category '{cat.name}' created successfully!")
            return redirect('platform_admin:blog_category_list')
    else:
        form = PostCategoryForm()

    categories = PostCategory.objects.annotate(posts_count=Count('posts')).order_by('name')
    return render(request, 'platform_admin/blogs/categories.html', {
        'categories': categories,
        'form': form,
    })


@staff_required
def blog_category_quick_create(request):
    """Quick AJAX endpoint to create a category on the fly while drafting a blog post."""
    if request.method == 'POST':
        form = PostCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@staff_required
def blog_category_delete(request, pk):
    """Delete a blog category. Linked articles have category set to null."""
    category = get_object_or_404(PostCategory, pk=pk)
    name = category.name
    if request.method == 'POST':
        category.delete()
        messages.success(request, f"🗑️ Category '{name}' deleted. Associated articles are now uncategorized.")
        return redirect('platform_admin:blog_category_list')
    return redirect('platform_admin:blog_category_list')


# ==============================================================================
# 3. SCHOLARSHIP OPPORTUNITIES MODULE ("UPLOAD SCHOLARSHIP OPPORTUNITIES")
# ==============================================================================

@staff_required
def opportunity_list(request):
    """Comprehensive scholarship directory with filters, status badges, and management tools."""
    status_filter = request.GET.get('status', 'all')
    verification_filter = request.GET.get('verification', 'all')
    degree_filter = request.GET.get('degree', 'all')
    funding_filter = request.GET.get('funding', 'all')
    search_q = request.GET.get('q', '').strip()

    opps = Opportunity.objects.all().order_by('-created_at')

    if status_filter != 'all':
        opps = opps.filter(status=status_filter)
    if verification_filter != 'all':
        opps = opps.filter(verification_status=verification_filter)
    if degree_filter != 'all':
        opps = opps.filter(degree_level=degree_filter)
    if funding_filter != 'all':
        opps = opps.filter(funding_type=funding_filter)
    if search_q:
        opps = opps.filter(
            Q(title__icontains=search_q) |
            Q(provider__icontains=search_q) |
            Q(country__icontains=search_q) |
            Q(field_of_study__icontains=search_q)
        )

    total_count = opps.count()
    active_count = Opportunity.objects.filter(status='active', verification_status='source_verified').count()
    staged_count = Opportunity.objects.filter(verification_status='needs_review').count()

    paginator = Paginator(opps, 20)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page,
        'current_status': status_filter,
        'current_verification': verification_filter,
        'current_degree': degree_filter,
        'current_funding': funding_filter,
        'search_q': search_q,
        'total_count': total_count,
        'active_count': active_count,
        'staged_count': staged_count,
        'degree_choices': Opportunity.DEGREE_LEVELS,
        'funding_choices': Opportunity.FUNDING_TYPES,
        'verification_choices': Opportunity.VERIFICATION_STATUSES,
    }
    return render(request, 'platform_admin/opportunities/list.html', context)


@staff_required
def opportunity_create(request):
    """Upload / Create a new scholarship opportunity manually with full structured criteria."""
    if request.method == 'POST':
        form = OpportunityForm(request.POST, request.FILES)
        if form.is_valid():
            opp = form.save()
            messages.success(request, f"🎉 Opportunity '{opp.title}' uploaded and added to the database successfully!")
            return redirect('platform_admin:opportunity_list')
    else:
        form = OpportunityForm(initial={
            'status': 'active',
            'verification_status': 'source_verified',
            'degree_level': 'masters',
            'funding_type': 'fully_funded',
            'portal_type': 'direct_portal',
            'application_fee': 'Free / No Application Fee',
            'deadline_timezone': 'UTC',
            'duration': '24 Months (2 Years)',
            'cycle_name': '2026/2027 Academic Year',
        })

    return render(request, 'platform_admin/opportunities/form.html', {
        'form': form,
        'is_edit': False,
    })


@staff_required
def opportunity_edit(request, pk):
    """Edit an existing scholarship opportunity."""
    opp = get_object_or_404(Opportunity, pk=pk)
    if request.method == 'POST':
        form = OpportunityForm(request.POST, request.FILES, instance=opp)
        if form.is_valid():
            opp = form.save()
            messages.success(request, f"✅ Scholarship '{opp.title}' updated successfully!")
            return redirect('platform_admin:opportunity_list')
    else:
        form = OpportunityForm(instance=opp)

    return render(request, 'platform_admin/opportunities/form.html', {
        'form': form,
        'opp': opp,
        'is_edit': True,
    })


@staff_required
def opportunity_delete(request, pk):
    """Delete a scholarship opportunity."""
    opp = get_object_or_404(Opportunity, pk=pk)
    title = opp.title
    if request.method == 'POST':
        opp.delete()
        messages.success(request, f"🗑️ Scholarship '{title}' deleted.")
        return redirect('platform_admin:opportunity_list')
    return render(request, 'platform_admin/opportunities/confirm_delete.html', {'opp': opp})


@staff_required
def opportunity_toggle_featured(request, pk):
    """Toggle the featured hero banner status for an opportunity."""
    if request.method == 'POST':
        opp = get_object_or_404(Opportunity, pk=pk)
        opp.is_featured = not opp.is_featured
        opp.save(update_fields=['is_featured'])
        status_text = "Featured Hero" if opp.is_featured else "Standard Listing"
        messages.success(request, f"Updated '{opp.title}' to {status_text}.")
    return redirect('platform_admin:opportunity_list')


# ==============================================================================
# 4. REGISTERED USERS MODULE ("SEE REGISTERED USERS")
# ==============================================================================

@staff_required
def user_list(request):
    """Comprehensive registered user directory with search, filtering, and 360-degree drilldown."""
    search_q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')
    verified_filter = request.GET.get('verified', 'all')
    tier_filter = request.GET.get('tier', 'all')

    users = User.objects.all().order_by('-date_joined')

    if search_q:
        users = users.filter(
            Q(email__icontains=search_q) |
            Q(first_name__icontains=search_q) |
            Q(last_name__icontains=search_q) |
            Q(applicant_profile__country_of_origin__icontains=search_q) |
            Q(applicant_profile__nationality__icontains=search_q)
        )

    if role_filter == 'staff':
        users = users.filter(is_staff=True)
    elif role_filter == 'user':
        users = users.filter(is_staff=False)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'suspended':
        users = users.filter(is_active=False)

    if verified_filter == 'verified':
        users = users.filter(is_email_verified=True)
    elif verified_filter == 'unverified':
        users = users.filter(is_email_verified=False)

    if tier_filter == 'premium':
        users = users.filter(subscriptions__status='active', subscriptions__plan__tier='premium').distinct()
    elif tier_filter == 'free':
        users = users.exclude(subscriptions__status='active', subscriptions__plan__tier='premium').distinct()

    total_count = users.count()
    verified_count = User.objects.filter(is_email_verified=True).count()
    staff_count = User.objects.filter(is_staff=True).count()

    paginator = Paginator(users, 25)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page,
        'search_q': search_q,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'verified_filter': verified_filter,
        'tier_filter': tier_filter,
        'total_count': total_count,
        'verified_count': verified_count,
        'staff_count': staff_count,
    }
    return render(request, 'platform_admin/users/list.html', context)


@staff_required
def user_detail(request, user_id):
    """360-degree applicant profile inspector, applications history, and account privilege controls."""
    target_user = get_object_or_404(User.objects.prefetch_related(
        'applications__opportunity',
        'documents',
        'stories',
        'assistance_bookings__package',
        'payment_transactions',
        'subscriptions__plan'
    ), id=user_id)

    profile = getattr(target_user, 'applicant_profile', None)
    applications = target_user.applications.all().order_by('-created_at')
    documents = target_user.documents.all().order_by('-upload_date')
    stories = target_user.stories.all().order_by('-created_at')
    bookings = target_user.assistance_bookings.all().order_by('-created_at')
    transactions = target_user.payment_transactions.all().order_by('-created_at')
    subscription = target_user.subscriptions.filter(status='active').first()

    context = {
        'target_user': target_user,
        'profile': profile,
        'applications': applications,
        'documents': documents,
        'stories': stories,
        'bookings': bookings,
        'transactions': transactions,
        'subscription': subscription,
    }
    return render(request, 'platform_admin/users/detail.html', context)


@staff_required
def user_toggle_staff(request, user_id):
    """Toggle staff status of a user."""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if target_user == request.user:
            messages.error(request, "Security protection: You cannot remove your own staff privileges.")
            return redirect('platform_admin:user_detail', user_id=user_id)

        target_user.is_staff = not target_user.is_staff
        target_user.save(update_fields=['is_staff'])
        status_text = "Staff Admin" if target_user.is_staff else "Regular Applicant"
        messages.success(request, f"User '{target_user.email}' is now set to {status_text}.")
    return redirect('platform_admin:user_detail', user_id=user_id)


@staff_required
def user_toggle_active(request, user_id):
    """Toggle active/suspended status of a user."""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if target_user == request.user:
            messages.error(request, "Security protection: You cannot suspend your own account.")
            return redirect('platform_admin:user_detail', user_id=user_id)

        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=['is_active'])
        status_text = "Active" if target_user.is_active else "Suspended"
        messages.success(request, f"User '{target_user.email}' account status updated to {status_text}.")
    return redirect('platform_admin:user_detail', user_id=user_id)


@staff_required
def user_toggle_verified(request, user_id):
    """Toggle verified status of a user's email."""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        target_user.is_email_verified = not target_user.is_email_verified
        target_user.save(update_fields=['is_email_verified'])
        status_text = "Verified" if target_user.is_email_verified else "Unverified"
        messages.success(request, f"Email verification for '{target_user.email}' marked as {status_text}.")
    return redirect('platform_admin:user_detail', user_id=user_id)


@staff_required
def user_send_notification(request, user_id):
    """Send an immediate in-app notification to a user."""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        action_url = request.POST.get('action_url', '').strip()

        if title and message:
            Notification.objects.create(
                user=target_user,
                title=title,
                message=message,
                action_url=action_url or '/dashboard/',
                notification_type='system'
            )
            messages.success(request, f"Notification successfully dispatched to {target_user.email}.")
        else:
            messages.error(request, "Both Title and Message are required.")
    return redirect('platform_admin:user_detail', user_id=user_id)


@staff_required
def user_export_csv(request):
    """Export all registered users with key profile fields to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="flii_users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Email', 'First Name', 'Last Name', 'Date Joined',
        'Is Staff', 'Is Active', 'Email Verified', 'Country of Origin',
        'Nationality', 'Target Degree', 'Applications Count'
    ])

    users = User.objects.select_related('applicant_profile').prefetch_related('applications').all()
    for u in users:
        prof = getattr(u, 'applicant_profile', None)
        writer.writerow([
            u.id,
            u.email,
            u.first_name,
            u.last_name,
            u.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            u.is_staff,
            u.is_active,
            u.is_email_verified,
            prof.country_of_origin if prof else '',
            prof.nationality if prof else '',
            prof.target_degree_level if prof else '',
            u.applications.count()
        ])
    return response


# ==============================================================================
# 5. PAID REQUESTS & FINANCIALS MODULE ("SEE PAID REQUEST")
# ==============================================================================

@staff_required
def paid_requests_hub(request):
    """
    Central Financial & Service Orders Management Hub:
    - Tab 1: Pay-Per-Application Expert Assistance Bookings (Paid, Pending, Completed)
    - Tab 2: Subscription Payment Transactions & Revenue Metrics
    """
    tab = request.GET.get('tab', 'assistance')
    status_filter = request.GET.get('status', 'all')
    search_q = request.GET.get('q', '').strip()

    # Metrics
    total_service_orders = AssistanceBooking.objects.count()
    paid_service_orders = AssistanceBooking.objects.filter(payment_status='paid').count()
    pending_payment_orders = AssistanceBooking.objects.filter(payment_status__in=['pending_verification', 'unpaid']).count()
    completed_orders = AssistanceBooking.objects.filter(status='completed').count()
    
    total_revenue_assistance = AssistanceBooking.objects.filter(payment_status='paid').aggregate(total=Sum('price'))['total'] or Decimal('0.00')
    total_revenue_subscriptions = PaymentTransaction.objects.filter(status='success', transaction_type='subscription').aggregate(total=Sum('amount'))['total'] if hasattr(PaymentTransaction, 'amount') else Decimal('0.00')

    # Tab 1: Service Orders Query
    bookings = AssistanceBooking.objects.select_related('user', 'package', 'assigned_reviewer').order_by('-created_at')
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    if search_q and tab == 'assistance':
        bookings = bookings.filter(
            Q(order_number__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(package_title__icontains=search_q)
        )

    # Tab 2: Subscription Transactions Query
    transactions = PaymentTransaction.objects.select_related('user', 'subscription__plan').order_by('-created_at')
    if search_q and tab == 'transactions':
        transactions = transactions.filter(
            Q(reference__icontains=search_q) |
            Q(user__email__icontains=search_q)
        )

    # Available Reviewers for Assignment
    available_reviewers = User.objects.filter(is_staff=True).order_by('first_name')

    bookings_paginator = Paginator(bookings, 20)
    bookings_page = bookings_paginator.get_page(request.GET.get('page') if tab == 'assistance' else 1)

    tx_paginator = Paginator(transactions, 25)
    tx_page = tx_paginator.get_page(request.GET.get('page') if tab == 'transactions' else 1)

    context = {
        'active_tab': tab,
        'status_filter': status_filter,
        'search_q': search_q,
        'bookings_page': bookings_page,
        'transactions_page': tx_page,
        'available_reviewers': available_reviewers,

        'total_service_orders': total_service_orders,
        'paid_service_orders': paid_service_orders,
        'pending_payment_orders': pending_payment_orders,
        'completed_orders': completed_orders,
        'total_revenue_assistance': total_revenue_assistance,
        'status_choices': AssistanceBooking.STATUS_CHOICES,
    }
    return render(request, 'platform_admin/paid_requests/list.html', context)


@staff_required
def paid_request_detail(request, pk):
    """Workbench for inspecting, updating payment status, assigning reviewer, and fulfilling a service order."""
    booking = get_object_or_404(AssistanceBooking.objects.select_related('user', 'package', 'application', 'assigned_reviewer'), pk=pk)
    available_reviewers = User.objects.filter(is_staff=True).order_by('first_name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_payment_status':
            new_payment_status = request.POST.get('payment_status')
            if new_payment_status in dict(AssistanceBooking.PAYMENT_STATUS_CHOICES):
                booking.payment_status = new_payment_status
                if new_payment_status == 'paid' and booking.status == 'pending_payment':
                    booking.status = 'awaiting_assignment'
                booking.save(update_fields=['payment_status', 'status', 'updated_at'])
                messages.success(request, f"Payment status updated to '{booking.get_payment_status_display()}'.")

        elif action == 'assign_reviewer':
            reviewer_id = request.POST.get('reviewer_id')
            if reviewer_id:
                reviewer = get_object_or_404(User, id=reviewer_id, is_staff=True)
                booking.assigned_reviewer = reviewer
                booking.assigned_admin = reviewer
                if booking.status in ['awaiting_assignment', 'pending_payment']:
                    booking.status = 'in_progress'
                booking.save(update_fields=['assigned_reviewer', 'assigned_admin', 'status', 'updated_at'])
                messages.success(request, f"Order assigned to reviewer {reviewer.get_full_name() or reviewer.email}.")

        elif action == 'update_workflow_status':
            new_status = request.POST.get('status')
            admin_notes = request.POST.get('admin_notes', '')
            meeting_link = request.POST.get('meeting_link', '')

            if new_status in dict(AssistanceBooking.STATUS_CHOICES):
                booking.status = new_status
                booking.admin_notes = admin_notes
                booking.meeting_link = meeting_link
                if new_status == 'completed' and not booking.completed_at:
                    booking.completed_at = timezone.now()
                booking.save(update_fields=['status', 'admin_notes', 'meeting_link', 'completed_at', 'updated_at'])
                messages.success(request, f"Workflow status updated to '{booking.get_status_display()}'.")

        elif action == 'submit_deliverable':
            deliverable_feedback = request.POST.get('deliverable_feedback', '')
            deliverable_file = request.FILES.get('deliverable_file')
            booking.deliverable_feedback = deliverable_feedback
            if deliverable_file:
                booking.deliverable_file = deliverable_file
            booking.status = 'completed'
            booking.completed_at = timezone.now()
            booking.save(update_fields=['deliverable_feedback', 'deliverable_file', 'status', 'completed_at', 'updated_at'] if deliverable_file else ['deliverable_feedback', 'status', 'completed_at', 'updated_at'])

            Notification.objects.create(
                user=booking.user,
                title=f"🎉 Order Completed: #{booking.order_number}",
                message=f"Your expert review deliverable for '{booking.package_title}' is ready for download in your workspace.",
                action_url=f"/assistance/orders/{booking.id}/",
                notification_type='system'
            )
            messages.success(request, f"Deliverable uploaded and order marked Completed! Applicant notified.")

        return redirect('platform_admin:paid_request_detail', pk=booking.id)

    return render(request, 'platform_admin/paid_requests/detail.html', {
        'booking': booking,
        'available_reviewers': available_reviewers,
    })


# ==============================================================================
# 6. APPLICATIONS PIPELINE & SYSTEM HEALTH
# ==============================================================================

@staff_required
def applications_pipeline(request):
    """View application pipeline dossiers across all applicants."""
    status_filter = request.GET.get('status', 'all')
    search_q = request.GET.get('q', '').strip()

    apps = Application.objects.select_related('user', 'opportunity').order_by('-created_at')
    if status_filter != 'all':
        apps = apps.filter(status=status_filter)
    if search_q:
        apps = apps.filter(
            Q(user__email__icontains=search_q) |
            Q(opportunity__title__icontains=search_q)
        )

    paginator = Paginator(apps, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'platform_admin/applications_list.html', {
        'page_obj': page,
        'status_filter': status_filter,
        'search_q': search_q,
        'total_count': apps.count(),
        'status_choices': Application.STATUS_CHOICES,
    })


@staff_required
def system_health(request):
    """Platform system diagnostics, AI audit logs, and agent action records."""
    audit_logs = AIAuditLog.objects.select_related('user').order_by('-created_at')
    agent_actions = AgentAction.objects.select_related('user').order_by('-created_at')

    paginator = Paginator(audit_logs, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'platform_admin/system_health.html', {
        'page_obj': page,
        'total_logs_count': audit_logs.count(),
        'total_actions_count': agent_actions.count(),
        'pending_actions_count': agent_actions.filter(status='pending').count(),
    })
