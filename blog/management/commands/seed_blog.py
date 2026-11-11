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

        # -------------------------------------------------------------
        # 6. Post 4: Poland NAWA Verification Guide (WYSIWYG HTML)
        # -------------------------------------------------------------
        poland_nawa_content = """<h2>Overview: Major Reforms in Poland’s Higher Education System</h2>
<p>If you are planning to study in Poland for upcoming academic intakes, there are major regulatory updates you need to know immediately. In response to tightening visa scrutiny and international student governance across the European Union, Poland’s <strong>Ministry of Science and Higher Education</strong>, in close coordination with the <strong>Ministry of Foreign Affairs (MSZ)</strong>, has overhauled the entry rules for foreign students.</p>

<p>Chief among these updates is the <strong>mandatory academic document verification process managed by NAWA (Narodowa Agencja Wymiany Akademickiej — Polish National Agency for Academic Exchange)</strong>. Without an official NAWA recognition statement confirming the authenticity and academic standing of your prior education, Polish universities cannot finalize your admission, and Polish consulates will refuse your National Type-D Student Visa.</p>

<blockquote>
    <strong>Key Takeaway:</strong> If your previous academic credentials (high school diploma or bachelor’s degree) were issued outside the European Union (EU), European Economic Area (EEA), or OECD member countries, you cannot bypass the NAWA verification process.
</blockquote>

<h2>Why Has Poland Introduced Mandatory NAWA Verification?</h2>
<p>Over the past few years, Polish consulates worldwide observed a surge in fraudulent educational credentials, unregistered preparatory centers, and candidates who used student enrollment purely as a vehicle for entry into the Schengen labour market. In response, the Polish government implemented sweeping reforms:</p>
<ul>
    <li><strong>Authenticity Verification:</strong> Guaranteeing that all foreign certificates and degrees are genuine and grant formal eligibility to pursue higher education in the issuing country.</li>
    <li><strong>Centralized Processing:</strong> Transitioning away from fragmented regional education offices (<em>Kuratorium Oświaty</em>) to a streamlined, digital process via NAWA.</li>
    <li><strong>Mandatory Pre-Visa Requirement:</strong> Ensuring that visa officers only review applicants whose educational backgrounds have already been verified by the state agency.</li>
</ul>

<h2>Who Needs to Complete NAWA Verification?</h2>

<h3>1. Who MUST Apply:</h3>
<ul>
    <li><strong>Undergraduate (First-Cycle / Long-Cycle Master’s) Applicants:</strong> Any prospective student holding a secondary school certificate / high school diploma from non-EU, non-EEA, and non-OECD nations (e.g. Nigeria, Ghana, India, Pakistan, Bangladesh, Zimbabwe, Kenya, Philippines, Central Asian countries, and Latin American nations without bilateral mutual recognition treaties).</li>
    <li><strong>Postgraduate (Second-Cycle Master’s) Applicants:</strong> Graduates holding a Bachelor’s degree from non-EU/OECD universities that is not covered by an automatic recognition treaty.</li>
</ul>

<h3>2. Who is EXEMPT:</h3>
<ul>
    <li>Holders of International Baccalaureate (IB) or European Baccalaureate (EB) diplomas.</li>
    <li>Students with diplomas issued within EU, EEA (Norway, Iceland, Liechtenstein), or OECD member states (e.g., USA, Canada, UK, Australia, Japan, South Korea).</li>
    <li>Holders of diplomas from countries with reciprocal mutual recognition agreements with Poland (e.g., Ukraine, China).</li>
    <li>Applicants who previously received a final recognition decision from a Polish Education Superintendent (<em>Kuratorium Oświaty</em>).</li>
</ul>

<h2>Step-by-Step Guide to the NAWA SYRENA Process</h2>
<p>The entire verification process is digital and executed through NAWA’s online application system known as <strong>SYRENA</strong>. Follow this step-by-step roadmap to avoid application rejections:</p>

<h3>Step 1: Check Your Diploma via the "Kwalifikator" Tool</h3>
<p>Before lodging a formal application, consult NAWA’s free database tool called <strong>Kwalifikator</strong>. This portal provides an instant assessment of how certificates and diplomas from your specific country are evaluated under Polish law.</p>

<h3>Step 2: Obtain an Apostille or Consular Legalization</h3>
<p>Your original educational document cannot simply be scanned raw — it must carry official authentication:</p>
<ul>
    <li><strong>Hague Apostille:</strong> If your home country is a signatory to the 1961 Hague Apostille Convention (e.g. India, South Africa, UK, USA), have your certificate authenticated with an Apostille stamp by the designated ministry in your home country.</li>
    <li><strong>Consular Legalization:</strong> If your country is NOT a member of the Hague Convention (e.g. Nigeria, Ghana, Pakistan), your documents must be authenticated first by your domestic Ministry of Education and Ministry of Foreign Affairs, and subsequently legalized by the <strong>Embassy of the Republic of Poland</strong> in your country.</li>
</ul>

<h3>Step 3: Secure an Official Sworn Polish Translation (<em>Tłumacz Przysięgły</em>)</h3>
<p>All non-Polish documentation must be translated into Polish. For Polish authorities and academic boards, translations must be completed by a <strong>Certified Sworn Translator</strong> registered on the official list of the Polish Ministry of Justice, or verified by a Polish consul. Standard commercial translations are routinely flagged or rejected.</p>

<h3>Step 4: Register on the NAWA SYRENA Portal</h3>
<p>Create an applicant account on the official <strong>NAWA SYRENA</strong> electronic platform. You will be required to submit clear digital scans (PDF or high-res JPG) of:</p>
<ol>
    <li>Your international passport biodata page.</li>
    <li>The original secondary school leaving certificate or Bachelor’s degree diploma.</li>
    <li>The official academic transcript / statement of examination results.</li>
    <li>The Apostille certificate or consular legalization stamps.</li>
    <li>The certified sworn translation into Polish.</li>
    <li>An <em>Eligibility Statement</em> (confirming that your diploma entitles you to apply to university programs in the country where it was issued), if not explicitly stated on the certificate.</li>
</ol>

<h3>Step 5: Receive Your Digital Recognition Statement</h3>
<p>Once NAWA verifies your credentials with the educational authorities of your home country, they issue an official <strong>Recognition Statement (<em>Oświadczenie o uznaniu</em>)</strong>. This digital certificate contains an encrypted qualified electronic signature, is provided free of statutory fees, and can be submitted directly to your university and during your visa appointment.</p>

<h2>Additional New Rules: Language Proficiency & University Quotas</h2>
<p>The NAWA verification requirement is part of a broader package of regulations enacted by Polish authorities:</p>

<h3>1. Stricter B2 Language Requirement</h3>
<p>All international students must prove at least <strong>CEFR Level B2 proficiency</strong> in the language of instruction (English or Polish). Polish universities and consulates now strictly mandate recognized international standardized certificates (such as IELTS, TOEFL, Cambridge, PTE, or state certification in Polish). Generic "English proficiency letters" from local institutions are facing widespread rejection.</p>

<h3>2. The 50% International Student Quota Cap</h3>
<p>Under the new statutory framework, foreign students cannot account for more than <strong>50% of the total student body</strong> at any individual Polish higher education institution. This prevents unaccredited private academies from running unchecked recruitment drives and ensures quality academic integration.</p>

<h2>Summary Checklist for Prospective Applicants</h2>
<ul>
    <li><strong>Start 3–4 months early:</strong> Document legalization and NAWA verification can take several weeks during peak summer admission cycles.</li>
    <li><strong>Do not apply for a visa without NAWA:</strong> Submitting your visa application without the required NAWA verification or recognized language certificate significantly increases your chance of visa denial.</li>
    <li><strong>Double-check your names:</strong> Ensure that your names match character-for-character across your passport, certificate, transcript, and sworn translation.</li>
</ul>

<p>By preparing your documentation through NAWA early, you ensure a smooth, compliant transition into Poland's higher education system and protect your investment in your academic future.</p>"""

        Post.objects.update_or_create(
            slug="poland-nawa-document-verification-guide",
            defaults={
                "title": "🇵🇱 BREAKING: Poland Enforces Mandatory NAWA Document Verification for International Students",
                "author": admin_user,
                "category": cat_visa,
                "summary": "Poland has introduced landmark higher education reforms requiring non-EU/OECD international students to secure official NAWA document verification prior to university admission and visa issuance. Here is the complete breakdown of the SYRENA portal, legalization, apostilles, sworn translations, and B2 language rules.",
                "content": poland_nawa_content,
                "featured_image_url": "https://images.unsplash.com/photo-1519197924294-4ba991a11128?auto=format&fit=crop&w=1600&q=80",
                "is_breaking_news": True,
                "is_pinned": True,
                "status": "published",
                "published_at": timezone.now(),
                "tags": "Poland, NAWA, Student Visa, Document Verification, Study in Poland, Admissions, Europe",
            }
        )

        # -------------------------------------------------------------
        # 6. Post 5: Airtel Africa Tech Fellowship 2026/2027
        # -------------------------------------------------------------
        airtel_tech_content = """<h2>Overview: Empowering the Next Generation of African Tech Leaders</h2>
<p>The <strong>Airtel Africa Foundation</strong>, in strategic partnership with <strong>The Afara Initiative</strong>, has officially opened applications for the <strong>Airtel Africa Tech Fellowship 2026/2027</strong>. This flagship corporate social responsibility initiative is engineered to discover, fund, and nurture high-potential undergraduate students across Africa who are pursuing technology and ICT-related disciplines.</p>

<p>Targeting talented students from low-income and historically disadvantaged backgrounds, the fellowship provides comprehensive financial, academic, and professional backing from matriculation through graduation. Successful fellows are shielded from rising higher education costs while gaining direct access to corporate mentorship, hands-on internships, and leadership accelerator tracks.</p>

<blockquote>
    <strong>Key Takeaway:</strong> The Airtel Africa Tech Fellowship is a <strong>100% fully funded undergraduate scholarship</strong>. It covers your entire tuition fees, provides monthly living stipends, equips you with a brand-new laptop, and fast-tracks your career into top-tier tech roles at Airtel Africa and partner organizations.
</blockquote>

<h2>Comprehensive Fellowship Benefits: What You Receive</h2>
<p>Unlike standard tuition bursaries, the Airtel Africa Tech Fellowship offers an all-inclusive support ecosystem designed to eliminate financial bottlenecks throughout your university journey:</p>

<ul>
    <li><strong>100% Full Tuition Coverage:</strong> All statutory university tuition, registration, examination, and faculty fees are fully paid directly to your institution for the entire duration of your undergraduate degree (from 100-level to final-year graduation).</li>
    <li><strong>Monthly Living & Accommodation Stipends:</strong> Generous annual living allowances distributed across academic semesters to offset campus accommodation, utility bills, books, and feeding costs.</li>
    <li><strong>Digital Hardware & Connectivity:</strong> Every selected fellow receives a high-performance modern laptop pre-configured for programming, software development, and academic research, accompanied by internet connectivity allowances.</li>
    <li><strong>Executive 1-on-1 Mentorship:</strong> Personal pairing with senior engineering leads, data architects, and executive directors at Airtel Africa and global tech partners to guide your technical and career trajectory.</li>
    <li><strong>Priority Internship & Early Career Pipelines:</strong> Exclusive consideration for competitive summer internships, industrial training (IT/SIWES) placements, and direct fast-track evaluation for Airtel Africa's Graduate Management Trainee Programme.</li>
    <li><strong>Leadership & Soft Skills Accelerator:</strong> Year-round masterclasses delivered by The Afara Initiative focusing on emotional intelligence, project management, technical communication, and corporate etiquette.</li>
</ul>

<h2>Eligibility Criteria: Who Can Apply?</h2>
<p>To ensure funds reach the most deserving candidates, the selection committee enforces strict merit-based and need-based standards:</p>

<h3>1. Academic Standing & Enrollment</h3>
<ul>
    <li>You must be a newly admitted or currently enrolled <strong>first-year (100-level) undergraduate student</strong> in an accredited public university for the current academic cycle.</li>
    <li>Demonstrated outstanding academic achievement in secondary school, evidenced by exceptional <strong>O'Level examination results</strong> (WAEC / NECO / WASSCE) with credits in Mathematics, English, Physics, and related subjects in one sitting.</li>
    <li>Strong performance in the Unified Tertiary Matriculation Examination (<strong>UTME</strong>) and Post-UTME screening tests.</li>
</ul>

<h3>2. Proven Financial Need</h3>
<ul>
    <li>Applicants must demonstrate genuine financial constraints or belong to low-income households that would otherwise struggle to sustain continuous university tuition and living costs.</li>
    <li>Willingness to provide verifiable proof of household income, socio-economic background, or parental/guardian circumstances.</li>
</ul>

<h3>3. Eligible Fields of Study (Technology & STEM)</h3>
<p>Applicants must be formally enrolled in an undergraduate degree program within technology, engineering, or computing faculties, including but not limited to:</p>
<ul>
    <li><strong>Computer Science</strong></li>
    <li><strong>Software Engineering</strong></li>
    <li><strong>Information and Communications Technology (ICT) / Information Technology</strong></li>
    <li><strong>Cybersecurity & Digital Forensics</strong></li>
    <li><strong>Systems Engineering / Computer Engineering</strong></li>
    <li><strong>Data Science & Artificial Intelligence</strong></li>
    <li><strong>Telecommunications & Electrical/Electronics Engineering</strong> (with computing focus)</li>
</ul>

<h2>The 12 Eligible Partner Public Universities</h2>
<p>For the 2026/2027 cohort, the Airtel Africa Tech Fellowship is tenable at <strong>12 premier public universities</strong> across geopolitical zones in Nigeria:</p>

<ol>
    <li><strong>University of Lagos (UNILAG)</strong> — South-West</li>
    <li><strong>University of Ibadan (UI)</strong> — South-West</li>
    <li><strong>Obafemi Awolowo University (OAU), Ile-Ife</strong> — South-West</li>
    <li><strong>University of Nigeria, Nsukka (UNN)</strong> — South-East</li>
    <li><strong>Federal University of Technology, Owerri (FUTO)</strong> — South-East</li>
    <li><strong>University of Benin (UNIBEN)</strong> — South-South</li>
    <li><strong>University of Uyo (UNIUYO)</strong> — South-South</li>
    <li><strong>Ahmadu Bello University (ABU), Zaria</strong> — North-West</li>
    <li><strong>University of Ilorin (UNILORIN)</strong> — North-Central</li>
    <li><strong>University of Abuja (UNIABUJA)</strong> — North-Central</li>
    <li><strong>University of Maiduguri (UNIMAID)</strong> — North-East</li>
    <li><strong>Tai Solarin University of Education (TASUED)</strong> — South-West</li>
</ol>

<h2>Required Application Documents Checklist</h2>
<p>Prepare clean, legible digital scans (PDF or high-resolution JPEG under 2MB each) of the following mandatory records before initiating your online submission:</p>

<ul>
    <li><strong>Official JAMB Admission Letter</strong> confirming your admission into an eligible partner university.</li>
    <li><strong>University / Faculty Provisional Admission Letter</strong> or official student bio-data registration slip.</li>
    <li><strong>UTME Result Slip</strong> showing scores and subjects taken.</li>
    <li><strong>Senior Secondary School Certificate Examination (SSCE) Results</strong> (WAEC, NECO, or GCE statement of results).</li>
    <li><strong>Recent Passport-sized Photograph</strong> on a plain light background.</li>
    <li><strong>Valid Government-Issued Identification</strong> (National Identity Number / NIN slip, Voter's Card, or International Passport).</li>
    <li><strong>Proof of State of Origin / Local Government Identification Certificate</strong>.</li>
    <li><strong>Statement of Financial Need / Family Background Form</strong> explaining why financial assistance is critical to completing your university education.</li>
</ul>

<h2>Step-by-Step Guide to Applying Online</h2>
<p>Follow this exact submission workflow to avoid disqualification during initial compliance screening:</p>

<h3>Step 1: Access the Official Application Portal</h3>
<p>Navigate to the designated application portal hosted by the program partners at <a href="https://pulse.theafarainitiative.org/" target="_blank" rel="noopener"><strong>pulse.theafarainitiative.org</strong></a> or verify updates via the <a href="https://airtelafricafoundation.org/" target="_blank" rel="noopener"><strong>Airtel Africa Foundation</strong></a> official website.</p>

<h3>Step 2: Create Your Candidate Account</h3>
<p>Register with your active personal email address and telephone number. Ensure your registered names match letter-for-letter across your JAMB slip, NIN, and university enrollment records.</p>

<h3>Step 3: Complete the Profile & Academic Details</h3>
<p>Input your secondary school grades, UTME composite score, matriculation / registration number (if assigned), department, faculty, and current CGPA (if you have completed your first semester examinations).</p>

<h3>Step 4: Draft Your Personal Statement & Essay Responses</h3>
<p>The online form requires answers to key essay prompts evaluating your drive, problem-solving mindset, and passion for technology. Focus on:</p>
<ul>
    <li>Your motivation for choosing a technology-focused career.</li>
    <li>A practical socio-economic challenge in your community that you envision solving with technology.</li>
    <li>How receiving full funding will alter your life trajectory and empower you to give back.</li>
</ul>

<h3>Step 5: Review and Submit Before the Deadline</h3>
<p>Double-check all uploaded documents for clarity and ensure all fields are filled accurately. Once submitted, download and retain your confirmation slip for reference during interview shortlisting.</p>

<h2>Key Dates & Selection Timeline</h2>
<ul>
    <li><strong>Application Deadline:</strong> Early December 2026 (December 4–7, 2026, depending on the portal intake cycle).</li>
    <li><strong>Initial Screening & Document Verification:</strong> Mid-December 2026.</li>
    <li><strong>Aptitude Assessment & Virtual Interviews:</strong> January 2027.</li>
    <li><strong>Final Induction & Cohort Onboarding:</strong> Late January / Early February 2027.</li>
</ul>

<h2>Pro-Tips for a Winning Fellowship Application</h2>
<ul>
    <li><strong>Be authentic about your financial background:</strong> The committee is explicitly searching for high-achieving candidates who genuinely lack financial options. Clearly articulate your circumstances with honesty and dignity.</li>
    <li><strong>Showcase independent initiative:</strong> Mention any self-taught coding tutorials, online courses (Coursera, freeCodeCamp, edX), tech clubs, or hackathons you have participated in, even at a beginner level.</li>
    <li><strong>Apply well ahead of the deadline:</strong> Application portals frequently experience heavy server traffic and submission bottlenecks during the final 48 hours. Submit early to guarantee your entry.</li>
</ul>"""

        Post.objects.update_or_create(
            slug="airtel-africa-tech-fellowship-undergraduate-scholarship-2026",
            defaults={
                "title": "🚀 Airtel Africa Tech Fellowship 2026/2027 for Undergraduates: Fully Funded Tech Scholarship, Laptops & Mentorship",
                "author": admin_user,
                "category": cat_scholarship,
                "summary": "The Airtel Africa Foundation has launched the 2026/2027 Tech Fellowship for undergraduate students in tech and STEM fields across 12 public universities. Enjoy 100% full tuition coverage, living stipends, digital devices, and direct industry mentorship from Airtel executives. Here is everything you need to apply before the December deadline.",
                "content": airtel_tech_content,
                "featured_image_url": "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=1600&q=80",
                "is_breaking_news": False,
                "is_pinned": True,
                "status": "published",
                "published_at": timezone.now(),
                "tags": "Airtel Africa, Tech Fellowship, Undergraduate Scholarships, Fully Funded, STEM, Coding, Nigeria, Scholarships",
            }
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded blog posts including Poland NAWA guide and Airtel Africa Tech Fellowship!"))
