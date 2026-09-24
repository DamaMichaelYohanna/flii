from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from .models import Opportunity, OpportunitySource
from matching.engine import MatchingEngine
from ai_core.service import AIService

@login_required
def opportunity_list(request):
    user = request.user
    query = request.GET.get('q', '').strip()
    country = request.GET.get('country', '').strip()
    degree_level = request.GET.get('degree_level', '').strip()
    funding_type = request.GET.get('funding_type', '').strip()
    sort_by = request.GET.get('sort', 'deadline')
    only_shortlisted = request.GET.get('shortlisted', '') == '1'

    qs = Opportunity.objects.filter(status='active')

    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(provider__icontains=query) |
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

    if only_shortlisted:
        qs = qs.filter(shortlisted_by=user)

    if sort_by == 'deadline':
        qs = qs.order_by('deadline')
    elif sort_by == 'created':
        qs = qs.order_by('-created_at')

    # Matching engine fit calculations
    matching_engine = MatchingEngine(user)
    opportunity_items = []
    for opp in qs:
        fit = matching_engine.calculate_deterministic_fit(opp)
        is_shortlisted = user.shortlisted_opportunities.filter(id=opp.id).exists()
        is_applied = user.applications.filter(opportunity_id=opp.id).exists()
        opportunity_items.append({
            'opportunity': opp,
            'fit': fit,
            'is_shortlisted': is_shortlisted,
            'is_applied': is_applied
        })

    paginator = Paginator(opportunity_items, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Filter dropdown choices
    countries = Opportunity.objects.values_list('country', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_country': country,
        'selected_degree': degree_level,
        'selected_funding': funding_type,
        'sort_by': sort_by,
        'only_shortlisted': only_shortlisted,
        'countries': countries,
        'total_count': len(opportunity_items)
    }
    return render(request, 'opportunities/list.html', context)


@login_required
def opportunity_detail(request, pk):
    user = request.user
    opp = get_object_or_404(Opportunity, pk=pk)
    matching_engine = MatchingEngine(user)
    
    # Calculate fit and quick breakdown
    fit = matching_engine.calculate_deterministic_fit(opp)
    is_shortlisted = user.shortlisted_opportunities.filter(id=opp.id).exists()
    application = user.applications.filter(opportunity=opp).first()

    context = {
        'opp': opp,
        'fit': fit,
        'is_shortlisted': is_shortlisted,
        'application': application,
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
                    'source_url': source_url or extracted.official_source_url or 'https://flii.app/sources',
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
            application_url=extracted.application_url or source_url or 'https://flii.app',
            official_source_url=extracted.official_source_url or source_url or 'https://flii.app',
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

    if result['new_count'] > 0:
        messages.success(
            request,
            f"🔍 AI Scout complete: Discovered and synced {result['new_count']} new scholarships from official European & global portals!"
        )
    else:
        messages.info(
            request,
            f"🔍 AI Scout checked official catalogues. All {result['total_scraped']} opportunities are verified and up to date."
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(result)
    return redirect('opportunities:list')


