from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from blog.models import PostCategory, Post

class Command(BaseCommand):
    help = "Seed initial blog categories and featured migration reports"

    def handle(self, *args, **options):
        # 1. Categories
        cat_visa, _ = PostCategory.objects.get_or_create(
            slug="visa-migration",
            defaults={
                "name": "Visa & Migration Alerts",
                "description": "Critical immigration policy shifts, student visa requirements, and country residency news.",
                "badge_color": "bg-rose-50 text-rose-700 border-rose-200",
                "icon": "flag"
            }
        )

        cat_scholarship, _ = PostCategory.objects.get_or_create(
            slug="scholarship-updates",
            defaults={
                "name": "Scholarship Calls & Funding",
                "description": "New scholarship announcements, intake openings, and fellowship funding breakdowns.",
                "badge_color": "bg-emerald-50 text-emerald-700 border-emerald-200",
                "icon": "graduation-cap"
            }
        )

        cat_guides, _ = PostCategory.objects.get_or_create(
            slug="application-guides",
            defaults={
                "name": "Application Strategy & Guides",
                "description": "Step-by-step guidance on motivation essays, recommendation letters, and university portals.",
                "badge_color": "bg-blue-50 text-blue-700 border-blue-200",
                "icon": "book-open"
            }
        )

        # 2. Author
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        # -------------------------------------------------------------
        # 3. Post 1: Portugal Official 2025 Migration Report
        # -------------------------------------------------------------
        portugal_content = """AIMA has released the official numbers — and there are major changes for students and international residents.

THE BIG NUMBERS (AT A GLANCE):
• 1,585,854 Foreign residents living in Portugal
• Population growth slowed to 2.7%
• 337,880 New residence titles granted
• 189,331 Renewals processed

GROWTH HAS SLOWED DOWN:
• Portugal's foreign population grew by only 42,157 in 2025, compared to 238,864 in 2024.
• Growth fell sharply from 18.3% to 2.7%.
• Important Context: This does NOT mean only 42,157 people entered Portugal in 2025. Rather, it reflects tighter initial processing, rigorous regularization rules, and a deliberate shift towards formal consular visa channels before arrival.

ATTENTION STUDENTS: RULES HAVE CHANGED:
Portugal has now changed the rules for some student routes:
• Law 62/2026 has removed the rule that allowed some secondary, Level 4/5, and professional-course students to get residency without a consular residence visa.
• The law took effect on 11th September 2026.
• More than 20,000 people had reportedly requested residence through the professional-course route.
• That route has now been formally removed from Article 92 by Law 62/2026.

THE SAFER, RECOMMENDED ROUTE FOR AFFECTED CATEGORIES:
1. Get admission to a recognised institution
2. Apply for the required student visa in your home country
3. Enter Portugal legally with your entry visa stamp
4. Apply for residence under the applicable rules and conclude AIMA biometrics

RENEWALS UPDATE:
• AIMA recorded 189,331 residence renewals in 2025.
• At year-end, 76,907 people had expired titles but had already paid fees — AIMA is still processing them.
• AIMA updated its renewals portal on 15th September 2026.
• EU citizens & their family members now no longer need to enter NIF or NISS for certain residence certificate or card applications.

WORK DOMINATES:
• Work was linked to 95.7% of all new residence grants in 2025.
• Largest nationalities for new grants:
1. Brazil
2. India
3. Nepal
4. Bangladesh
5. Pakistan"""

        portugal_post, _ = Post.objects.update_or_create(
            slug="portugal-official-2025-migration-report-student-visa-changes",
            defaults={
                "title": "🇵🇹 BREAKING: Portugal's Official 2025 Migration Report Is Out 📊",
                "author": admin_user,
                "category": cat_visa,
                "summary": "AIMA has released the numbers — and there are major changes for students under Law 62/2026, population growth deceleration, and updated renewal processing.",
                "content": portugal_content,
                "featured_image_url": "https://images.unsplash.com/photo-1555881400-74d7acaacd81?auto=format&fit=crop&w=1400&q=80",
                "is_breaking_news": True,
                "is_pinned": True,
                "status": "published",
                "published_at": timezone.now(),
                "tags": "Portugal, AIMA, Student Visa, Migration Report, Law 62/2026, European Union",
            }
        )

        # -------------------------------------------------------------
        # 4. Post 2: Latvia New Immigration Law In Force
        # -------------------------------------------------------------
        latvia_content = """Big changes have landed in the Baltic region. Latvia's new Immigration Law officially took effect on 15th September 2026.

If you are planning to travel, study, work or invest in Latvia, here are the critical rules you must know:

1. NEW LANGUAGE RULES — STRICTLY ENFORCED
Latvia has tightened its document rules:
• For New Visas & First-Time Residence Permits: Documents can be submitted in Latvian or English only.
• For Renewals & Permanent Residence: Documents must generally be in Latvian only.

2. INVESTOR ROUTES CLOSED
Latvia has officially removed these Temporary Residence Permit routes:
• Buying Real Estate
• Investing in Subordinated Liabilities of Credit Institutions
This applies to all new applicants from 15th September 2026.

3. RESIDENCE PERMITS — GOOD NEWS
Key improvements for residents:
• Some Temporary Residence Permits can now be valid for 2 years.
• The annual registration requirement has been removed in several cases.
• Processing time is now capped at 4 months.

4. STUDENTS & FAMILIES — PLEASE TAKE NOTE
Family reunification rules just got significantly tighter.
Family members can only join an international student in Latvia if:
• The student is a citizen of a NATO country, OR
• The student is a Doctoral (PhD) student.

For non-NATO Master's or Bachelor's students, dependent family reunification is no longer permitted on student permit grounds.

5. PERMANENT RESIDENCY RULES CHANGED
Want Permanent Residency in Latvia?
You now need to have held a 5-year Temporary Residence permit in Latvia before you qualify."""

        latvia_post, _ = Post.objects.update_or_create(
            slug="latvia-new-immigration-law-in-force-student-family-rules",
            defaults={
                "title": "🇱🇻 BREAKING: Latvia's New Immigration Law Is Now in Force 🚨",
                "author": admin_user,
                "category": cat_visa,
                "summary": "Latvia's new Immigration Law officially took effect on 15th September 2026. Here is what students, workers, and families must know regarding language rules, investor permits, and family reunification limits.",
                "content": latvia_content,
                "featured_image_url": "https://images.unsplash.com/photo-1548625361-195b058a9df8?auto=format&fit=crop&w=1400&q=80",
                "is_breaking_news": True,
                "is_pinned": False,
                "status": "published",
                "published_at": timezone.now(),
                "tags": "Latvia, Immigration Law, Student Visa, PhD, Residence Permit, European Union, NATO",
            }
        )

        # -------------------------------------------------------------
        # 5. Post 3: General Application Guide
        # -------------------------------------------------------------
        guide_content = """Winning a competitive fully funded postgraduate scholarship (such as DAAD, Chevening, or Erasmus Mundus) requires more than just high grades. Selection committees look for evidence of leadership, resilience, and grounded motivation.

Here are the 4 fundamental pillars every competitive candidate needs:

1. Factual Evidence Over Clichés: Never write "I am passionate about AI" without pointing to a tangible project, repository, or undergraduate thesis.
2. The STAR Framework: Frame your personal statement achievements using Situation, Challenge, Action, and Measurable Result.
3. Document Verification Early: Ensure your degree certificate, academic transcripts, and passport are verified and uploaded ahead of peak application deadlines.
4. Alignment with Funding Agency Goals: Understand what the scholarship provider values (e.g. DAAD focuses on development impact; Chevening focuses on diplomatic leadership).

Use your Flii Story Bank to catalogue your experiences now so your essay drafts are grounded in real, verifiable facts."""

        Post.objects.update_or_create(
            slug="how-to-build-a-competitive-scholarship-profile",
            defaults={
                "title": "How to Build a High-Fit Postgraduate Scholarship Profile in 2026",
                "author": admin_user,
                "category": cat_guides,
                "summary": "Discover how top applicants structure their academic evidence, STAR stories, and motivation letters to secure fully funded Master's and PhD offers.",
                "content": guide_content,
                "featured_image_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1400&q=80",
                "is_breaking_news": False,
                "is_pinned": False,
                "status": "published",
                "published_at": timezone.now(),
                "tags": "Scholarship Strategy, STAR Method, Motivation Letter, Postgraduate",
            }
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded separate Portugal and Latvia immigration reports!"))
