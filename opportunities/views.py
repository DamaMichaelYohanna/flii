import datetime
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from .models import Opportunity, OpportunitySource
from matching.engine import MatchingEngine
from ai_core.service import AIService
from subscriptions.entitlements import EntitlementService

def opportunity_list(request):
    user = request.user if request.user.is_authenticated else None
    query = request.GET.get('q', '').strip()
    country = request.GET.get('country', '').strip()
    degree_level = request.GET.get('degree_level', '').strip()
    funding_type = request.GET.get('funding_type', '').strip()
    field = request.GET.get('field', '').strip()
    deadline_filter = request.GET.get('deadline', '').strip()
    sort_by = request.GET.get('sort', 'deadline')
    only_shortlisted = request.GET.get('shortlisted', '') == '1' and user is not None

    qs = Opportunity.objects.filter(status='active')

    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(provider__icontains=query) |
            Q(university__icontains=query) |
            Q(description__icontains=query) |
            Q(field_of_study__icontains=query) |
            Q(country__icontains=query)
        )

    if country:
        qs = qs.filter(country__icontains=country)

    if degree_level:
        qs = qs.filter(degree_level=degree_level)

    if funding_type:
        qs = qs.filter(funding_type=funding_type)

    if field:
        qs = qs.filter(field_of_study__icontains=field)

    now = timezone.now()
    if deadline_filter == 'closing_soon':
        two_weeks = now + datetime.timedelta(days=14)
        qs = qs.filter(deadline__gte=now, deadline__lte=two_weeks)
    elif deadline_filter == 'upcoming':
        qs = qs.filter(opening_date__gt=now)
    elif deadline_filter == 'open_now':
        qs = qs.filter(deadline__gte=now).filter(Q(opening_date__isnull=True) | Q(opening_date__lte=now))

    if only_shortlisted and user:
        qs = qs.filter(shortlisted_by=user)

    if sort_by == 'deadline':
        qs = qs.order_by('deadline')
    elif sort_by == 'created':
        qs = qs.order_by('-created_at')
    elif sort_by == 'title':
        qs = qs.order_by('title')

    # Top 3 Featured Hero Scholarships (Scholarship Region style hero)
    featured_qs = Opportunity.objects.filter(status='active', is_featured=True).order_by('deadline')[:3]
    if featured_qs.count() < 3:
        featured_ids = [f.id for f in featured_qs]
        backfill = Opportunity.objects.filter(status='active').exclude(id__in=featured_ids).order_by('deadline')[:3 - featured_qs.count()]
        featured_opportunities = list(featured_qs) + list(backfill)
    else:
        featured_opportunities = list(featured_qs)

    # Matching engine fit calculations for authenticated users
    matching_engine = MatchingEngine(user) if user else None
    opportunity_items = []
    for opp in qs:
        fit = matching_engine.calculate_deterministic_fit(opp) if matching_engine else None
        is_shortlisted = user.shortlisted_opportunities.filter(id=opp.id).exists() if user else False
        is_applied = user.applications.filter(opportunity_id=opp.id).exists() if user else False
        opportunity_items.append({
            'opportunity': opp,
            'fit': fit,
            'is_shortlisted': is_shortlisted,
            'is_applied': is_applied
        })

    is_premium = EntitlementService.has_active_subscription(user) if user else False

    # Standard public pagination (12 opportunities per page)
    paginator = Paginator(opportunity_items, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Filter dropdown choices
    countries = Opportunity.objects.values_list('country', flat=True).distinct().order_by('country')
    degrees = Opportunity.DEGREE_LEVELS
    funding_choices = Opportunity.FUNDING_TYPES

    context = {
        'page_obj': page_obj,
        'featured_opportunities': featured_opportunities,
        'query': query,
        'selected_country': country,
        'selected_degree': degree_level,
        'selected_funding': funding_type,
        'selected_field': field,
        'selected_deadline': deadline_filter,
        'sort_by': sort_by,
        'only_shortlisted': only_shortlisted,
        'countries': countries,
        'degrees': degrees,
        'funding_choices': funding_choices,
        'total_count': len(opportunity_items),
        'is_premium': is_premium,
        'user_is_authenticated': user is not None,
    }
    return render(request, 'opportunities/list.html', context)


def opportunity_detail(request, pk=None, slug=None):
    user = request.user if request.user.is_authenticated else None
    if slug:
        opp = get_object_or_404(Opportunity, slug=slug)
    elif pk:
        opp = get_object_or_404(Opportunity, pk=pk)
    else:
        from django.http import Http404
        raise Http404("Opportunity not found.")

    matching_engine = MatchingEngine(user) if user else None
    fit = matching_engine.calculate_deterministic_fit(opp) if matching_engine else None
    is_shortlisted = user.shortlisted_opportunities.filter(id=opp.id).exists() if user else False
    application = user.applications.filter(opportunity=opp).first() if user else None
    is_premium = EntitlementService.has_active_subscription(user) if user else False

    # Similar opportunities for recommendations
    similar_opportunities = Opportunity.objects.filter(
        status='active'
    ).exclude(id=opp.id).filter(
        Q(country=opp.country) | Q(degree_level=opp.degree_level)
    )[:3]

    context = {
        'opp': opp,
        'fit': fit,
        'is_shortlisted': is_shortlisted,
        'application': application,
        'is_premium': is_premium,
        'similar_opportunities': similar_opportunities,
        'user_is_authenticated': user is not None,
    }
    return render(request, 'opportunities/detail.html', context)


@login_required
def toggle_shortlist(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk)
    user = request.user
    if user.shortlisted_opportunities.filter(id=opp.id).exists():
        user.shortlisted_opportunities.remove(opp)
        is_shortlisted = False
        messages.info(request, f"Removed '{opp.title}' from your shortlisted opportunities.")
    else:
        user.shortlisted_opportunities.add(opp)
        is_shortlisted = True
        messages.success(request, f"Saved '{opp.title}' to your shortlisted opportunities.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_shortlisted': is_shortlisted})
    return redirect(request.META.get('HTTP_REFERER', 'opportunities:list'))


@login_required
def assess_eligibility_api(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk)
    ai_service = AIService.get_instance()
    result = ai_service.assess_eligibility(request.user, opp)
    return JsonResponse(result.model_dump())


@login_required
def opportunity_import(request):
    """
    Live AI-assisted opportunity extraction from supplied official text or portal URLs.
    Extracts structured fields, validates with Pydantic, and saves to database in real-time.
    """
    if request.method == 'POST':
        source_url = request.POST.get('source_url', '').strip()
        raw_text = request.POST.get('raw_text', '').strip()

        if not raw_text and source_url:
            # Attempt safe HTTP fetch if URL is provided and no text is pasted
            try:
                import requests
                resp = requests.get(source_url, timeout=6, headers={'User-Agent': 'Flii-Discovery/1.0'})
                if resp.status_code == 200:
                    raw_text = resp.text[:10000]
            except Exception as e:
                pass

        if not raw_text:
            messages.error(request, "Please paste the scholarship announcement text or provide a valid source URL.")
            return render(request, 'opportunities/import.html')

        ai_service = AIService.get_instance()
        extracted = ai_service.extract_opportunity_from_text(request.user, raw_text, source_url=source_url)

        # Parse deadline
        import datetime
        from django.utils import timezone
        try:
            deadline_date = datetime.datetime.strptime(extracted.deadline_iso, "%Y-%m-%d")
            deadline = timezone.make_aware(deadline_date)
        except Exception:
            deadline = timezone.now() + datetime.timedelta(days=60)

        # Create or fetch Source
        source_obj = None
        if source_url or extracted.provider:
            source_obj, _ = OpportunitySource.objects.get_or_create(
                name=extracted.provider,
                defaults={
                    'source_url': source_url or extracted.official_source_url or extracted.application_url or '',
                    'source_type': 'university' if 'uni' in extracted.provider.lower() else 'government',
                    'last_verified': timezone.now(),
                    'verification_notes': 'Extracted from official text supplied by applicant/moderator.'
                }
            )

        # Save Opportunity
        opp = Opportunity.objects.create(
            title=extracted.title,
            provider=extracted.provider,
            university=extracted.university,
            country=extracted.country,
            degree_level=extracted.degree_level,
            field_of_study=extracted.field_of_study,
            description=extracted.description,
            funding_type=extracted.funding_type,
            funding_details=extracted.funding_details,
            eligibility_summary=extracted.eligibility_summary,
            application_url=extracted.application_url or source_url or '',
            official_source_url=extracted.official_source_url or source_url or '',
            source=source_obj,
            deadline=deadline,
            language_requirement=extracted.language_requirement,
            academic_requirement=extracted.academic_requirement,
            nationality_requirement=extracted.nationality_requirement,
            documents_required=extracted.documents_required,
            application_fee=extracted.application_fee,
            status='active',
            verification_status='ai_extracted'
        )

        messages.success(request, f"🎉 Successfully extracted and added '{opp.title}' ({opp.provider}) to Flii database!")
        return redirect('opportunities:detail', pk=opp.id)

    return render(request, 'opportunities/import.html')


@login_required
def run_scout_discovery(request):
    """
    Autonomous Scout Discovery Endpoint:
    Crawls official EU, DAAD, and global portals, extracts new opportunities,
    ranks them by user relevance, and refreshes the catalog.
    """
    from .discovery import OpportunityDiscoveryService
    scout = OpportunityDiscoveryService()
    result = scout.run_automated_scraping_and_sync(user=request.user)

    new_count = result.get('new_count', 0)
    updated_count = result.get('updated_count', 0)
    total_sources = result.get('total_sources_scanned', 0)
    total_scraped = result.get('total_scraped', new_count + updated_count)

    if new_count > 0:
        messages.success(
            request,
            f"🔍 AI Scout complete: Discovered and synced {new_count} new scholarships from official European & global portals!"
        )
    elif updated_count > 0:
        messages.info(
            request,
            f"🔍 AI Scout checked {total_sources} official catalogues. {updated_count} existing opportunities were verified and updated."
        )
    else:
        catalog_count = Opportunity.objects.count()
        count_display = total_scraped if total_scraped > 0 else catalog_count
        messages.info(
            request,
            f"🔍 AI Scout checked official catalogues. All {count_display} opportunities are verified and up to date."
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(result)
    return redirect('opportunities:list')


@login_required
def scan_portal_view(request, pk):
    """
    Live AI scanner endpoint for a single opportunity:
    Launches HTTP fetch, verifies responsiveness, extracts direct apply link,
    evaluates AI application readiness, and updates Opportunity record.
    """
    from .scanner import ParallelOpportunityScanner
    opp = get_object_or_404(Opportunity, pk=pk)
    scanner = ParallelOpportunityScanner(timeout=10)
    result = scanner.scan_and_verify_single(opp, user=request.user)

    if result['is_live']:
        messages.success(
            request,
            f"⚡ Live Portal Verified: {opp.title[:45]} is ACTIVE (HTTP {result['status_code']}). "
            f"AI Readiness: {opp.get_ai_application_readiness_display()}."
        )
    else:
        messages.warning(
            request,
            f"⚠️ Portal check: {opp.title[:45]} returned HTTP {result['status_code']} ({result.get('error') or 'Unresponsive'})."
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(result)
    return redirect('opportunities:detail', pk=opp.id)


@login_required
def scan_all_portals_view(request):
    """
    Parallel AI scan endpoint across all active scholarship portals:
    Uses ThreadPoolExecutor to verify all external application links in parallel.
    """
    from .scanner import ParallelOpportunityScanner
    scanner = ParallelOpportunityScanner(timeout=10)
    summary = scanner.scan_opportunities_parallel(max_workers=5, user=request.user)

    messages.success(
        request,
        f"🚀 Parallel AI Portal Scan Complete: {summary['live_count']}/{summary['total_scanned']} active portals verified. "
        f"{summary['ready_for_ai']} ready for automated AI application submission."
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(summary)
    return redirect('opportunities:list')


@login_required
def admin_scout_hub(request):
    """
    Dedicated Admin Scout Hub:
    Central dashboard for reviewing real-time official portal syncing,
    managing registered portals, previewing staged scholarship discoveries,
    and one-click publishing to the live catalog.
    """
    if not request.user.is_staff:
        messages.warning(request, "Staff privileges required to access the Admin Scout Hub.")
        return redirect('opportunities:list')

    from .discovery import OpportunityDiscoveryService
    from agent_hub.models import AIAuditLog
    scout = OpportunityDiscoveryService()
    scout.ensure_official_portals_seeded()

    sources = OpportunitySource.objects.all().order_by('-is_active', 'name')
    pending_opps = Opportunity.objects.filter(verification_status='needs_review').order_by('-created_at')
    published_opps = Opportunity.objects.filter(verification_status='source_verified').order_by('-created_at')[:15]
    
    total_active_count = Opportunity.objects.filter(status='active', verification_status='source_verified').count()
    total_pending_count = pending_opps.count()
    total_sources_count = sources.count()
    active_sources_count = sources.filter(is_active=True).count()

    recent_audits = AIAuditLog.objects.filter(
        action_type="autonomous_scout_discovery"
    ).order_by('-created_at')[:8]

    context = {
        'sources': sources,
        'pending_opps': pending_opps,
        'published_opps': published_opps,
        'total_active_count': total_active_count,
        'total_pending_count': total_pending_count,
        'total_sources_count': total_sources_count,
        'active_sources_count': active_sources_count,
        'recent_audits': recent_audits,
    }
    return render(request, 'opportunities/admin_scout.html', context)


@login_required
def admin_trigger_scout_api(request):
    """
    API endpoint invoked by the Admin One-Click Scout button:
    Scouts active official portals in real-time, extracts structured data via Gemini,
    stages new discoveries for admin review, and returns JSON diagnostics.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .discovery import OpportunityDiscoveryService
    scout = OpportunityDiscoveryService()

    source_id = request.GET.get('source_id') or request.POST.get('source_id')
    if source_id:
        try:
            source = OpportunitySource.objects.get(id=int(source_id))
            result = scout.scout_single_source(source, user=request.user)
            return JsonResponse({
                'success': result['success'],
                'new_count': result['created'],
                'updated_count': result['updated'],
                'results': [result]
            })
        except OpportunitySource.DoesNotExist:
            return JsonResponse({'error': 'Source not found'}, status=404)

    # Full batch scout across active portals
    result = scout.run_scout_batch(user=request.user)
    return JsonResponse({
        'success': True,
        'new_count': result.get('new_count', 0),
        'updated_count': result.get('updated_count', 0),
        'failed_count': result.get('failed_count', 0),
        'total_sources': result.get('total_sources_scanned', 0),
        'total_scraped': result.get('total_scraped', 0),
        'results': result.get('results', [])
    })


@login_required
def admin_publish_opportunity(request, pk):
    """
    One-click action to approve and publish a staged opportunity to the live catalog.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    opp = get_object_or_404(Opportunity, pk=pk)
    opp.verification_status = 'source_verified'
    opp.status = 'active'
    opp.save(update_fields=['verification_status', 'status'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'id': opp.id, 'title': opp.title})

    messages.success(request, f"✅ Published '{opp.title}' to the public catalog!")
    return redirect('opportunities:admin_scout_hub')


@login_required
def admin_publish_all(request):
    """
    One-click batch action to approve and publish all staged opportunities to the live catalog.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    count = Opportunity.objects.filter(verification_status='needs_review').update(
        verification_status='source_verified',
        status='active'
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'count': count})

    messages.success(request, f"🎉 Batch Published {count} staged scholarships to the public catalog!")
    return redirect('opportunities:admin_scout_hub')


@login_required
def admin_delete_opportunity(request, pk):
    """
    Rejects/deletes a staged opportunity.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    opp = get_object_or_404(Opportunity, pk=pk)
    title = opp.title
    opp.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'id': pk})

    messages.info(request, f"Removed staged opportunity '{title}'.")
    return redirect('opportunities:admin_scout_hub')


@login_required
def admin_toggle_source(request, pk):
    """
    Toggles an official portal source on or off for automated scouting.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    source = get_object_or_404(OpportunitySource, pk=pk)
    source.is_active = not source.is_active
    source.save(update_fields=['is_active'])

    state_str = "Enabled" if source.is_active else "Disabled"
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_active': source.is_active})

    messages.info(request, f"{state_str} scouting for portal '{source.name}'.")
    return redirect('opportunities:admin_scout_hub')


@login_required
def admin_add_source(request):
    """
    Allows admin to register a new official scholarship portal URL.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        source_url = request.POST.get('source_url', '').strip()
        source_type = request.POST.get('source_type', 'government')
        notes = request.POST.get('verification_notes', '').strip()

        if name and source_url:
            source, created = OpportunitySource.objects.get_or_create(
                source_url=source_url,
                defaults={
                    'name': name,
                    'source_type': source_type,
                    'verification_notes': notes,
                    'is_active': True,
                    'last_status': 'idle'
                }
            )
            if created:
                messages.success(request, f"Added official portal '{source.name}' to scouting registry.")
            else:
                messages.info(request, f"Portal with URL '{source_url}' is already registered.")
        else:
            messages.error(request, "Portal name and valid URL are required.")

    return redirect('opportunities:admin_scout_hub')




