import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from applicants.models import (
    ApplicantProfile, Education, Employment, Skill, Project,
    Achievement, Certification, ResearchExperience, StudyGoal, LanguageProficiency
)
from stories.models import Story
from documents.models import Document
from opportunities.models import Opportunity, OpportunitySource
from applications.models import Application, ApplicationRequirement, ApplicationTask

class Command(BaseCommand):
    help = "Seeds realistic ScholarFlow scholarships and sample applicant Yohanna Adebayo"

    def handle(self, *args, **options):
        self.stdout.write("Seeding ScholarFlow demo and production-sample data...")

        # 1. Create or get demo user
        user, created = User.objects.get_or_create(
            email="yohanna.adebayo@example.com",
            defaults={
                "username": "yohanna",
                "first_name": "Yohanna",
                "last_name": "Adebayo",
                "is_email_verified": True,
                "onboarding_completed": True
            }
        )
        if created:
            user.set_password("ScholarFlow2026!")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user: {user.email} (Password: ScholarFlow2026!)"))
        else:
            self.stdout.write(f"User {user.email} already exists.")

        # 2. Build structured applicant profile
        profile, _ = ApplicantProfile.objects.get_or_create(
            user=user,
            defaults={
                "middle_name": "Emeka",
                "phone": "+234 803 123 4567",
                "country_of_origin": "Nigeria",
                "nationality": "Nigerian",
                "date_of_birth": datetime.date(2001, 5, 14),
                "gender": "male",
                "current_location": "Lagos, Nigeria",
                "headline": "First-Class Computer Science Graduate | AI & Distributed Systems Researcher",
                "bio_summary": "Aspiring AI researcher focused on high-performance machine learning models for low-resource environments. Published undergraduate researcher with 2+ years of professional backend software engineering experience."
            }
        )

        # 3. Educations
        Education.objects.get_or_create(
            profile=profile,
            institution="University of Lagos (UNILAG)",
            defaults={
                "country": "Nigeria",
                "degree_level": "bachelors",
                "field_of_study": "Computer Science",
                "start_date": datetime.date(2019, 10, 1),
                "end_date": datetime.date(2024, 7, 15),
                "graduation_year": 2024,
                "grade_classification": "First Class Honours",
                "cgpa": 4.86,
                "max_cgpa": 5.00,
                "relevant_coursework": "Data Structures & Algorithms, Distributed Systems, Machine Learning, Artificial Intelligence, Database Management, Operating Systems, Linear Algebra"
            }
        )

        # 4. Employment
        Employment.objects.get_or_create(
            profile=profile,
            organization="Helios Pay & Fintech Labs",
            job_title="Associate Software Engineer",
            defaults={
                "location": "Lagos, Nigeria (Hybrid)",
                "start_date": datetime.date(2024, 8, 1),
                "is_current": True,
                "responsibilities": "Architecting resilient microservices handling 250k+ daily transactions. Optimizing database indexing and message queue throughput.",
                "achievements": "Reduced API latency by 42% and spearheaded the automated transaction reconciliations engine."
            }
        )
        Employment.objects.get_or_create(
            profile=profile,
            organization="Data Science Nigeria (DSN)",
            job_title="AI Research Intern",
            defaults={
                "location": "Lagos, Nigeria",
                "start_date": datetime.date(2023, 2, 1),
                "end_date": datetime.date(2023, 8, 30),
                "is_current": False,
                "responsibilities": "Assisted in computer vision research for crop disease detection in West African agriculture.",
                "achievements": "Co-authored technical paper presented at regional academic workshop."
            }
        )

        # 5. Skills
        skills_data = [
            ("Python (PyTorch, NumPy, Django)", "technical"),
            ("Distributed Systems & Docker", "technical"),
            ("PostgreSQL & Redis", "technical"),
            ("Machine Learning & NLP", "research"),
            ("Experimental Design & Statistics", "research"),
            ("Team Leadership & Mentorship", "soft"),
            ("Technical Writing & Scientific Papers", "soft"),
        ]
        for s_name, s_cat in skills_data:
            Skill.objects.get_or_create(profile=profile, name=s_name, defaults={"category": s_cat, "proficiency": "Advanced"})

        # 6. Projects
        Project.objects.get_or_create(
            profile=profile,
            title="AgriVision-Africa: Deep Learning Edge Model for Cassava Blight",
            defaults={
                "role": "Lead Researcher & Developer",
                "technologies": "PyTorch, MobileNetV3, ONNX Runtime, FastAPI",
                "description": "Designed a lightweight computer vision model capable of running offline on budget Android devices to diagnose crop diseases in real time.",
                "outcome": "Achieved 96.2% validation accuracy with sub-80ms inference latency on low-end hardware.",
                "date": datetime.date(2024, 6, 1),
                "project_url": "https://github.com/scholarflow-demo/agrivision"
            }
        )

        # 7. Achievements
        Achievement.objects.get_or_create(
            profile=profile,
            title="Best Graduating Student in Computer Science (Valedictorian Nominee)",
            defaults={
                "organization": "Faculty of Science, University of Lagos",
                "description": "Awarded for exceptional academic excellence, graduating top of class with 4.86/5.00 CGPA.",
                "date_awarded": datetime.date(2024, 7, 20)
            }
        )

        # 8. Research Profile
        ResearchExperience.objects.get_or_create(
            profile=profile,
            defaults={
                "research_interests": "Applied Machine Learning, Efficient Deep Learning on Edge Devices, Natural Language Processing for Low-Resource African Languages, Distributed AI",
                "summary_experience": "Two years of investigative research bridging deep neural network optimization and practical healthcare/agricultural challenges in Sub-Saharan Africa.",
                "publications": "Adebayo, Y., et al. (2024). 'Lightweight Edge Vision Architectures for Real-Time Crop Disease Classification in Resource-Constrained Environments.' Journal of African Computing Technologies, 12(3), 45-58."
            }
        )

        # 9. Study Goals
        StudyGoal.objects.get_or_create(
            profile=profile,
            defaults={
                "target_degree": "Master's (MSc)",
                "target_fields": "Computer Science, Artificial Intelligence, Data Science, Software Engineering",
                "target_countries": "Germany, United Kingdom, France, Sweden, Switzerland",
                "preferred_universities": "Technical University of Munich (TUM), University of Oxford, ETH Zurich, University of Edinburgh, Sorbonne University",
                "funding_preference": "fully_funded",
                "intake_year": 2026,
                "career_goals": "Pursue high-impact postgraduate research in Artificial Intelligence, leading towards research scientist roles and founding an applied AI research institute in West Africa.",
                "long_term_goals": "Lead national AI policy frameworks and build indigenous technology solutions solving agricultural, health, and economic bottlenecks across the African continent."
            }
        )

        # 10. Language
        LanguageProficiency.objects.get_or_create(
            profile=profile,
            language="English",
            defaults={
                "proficiency_level": "Native / Bilingual",
                "test_type": "ielts",
                "overall_score": "8.5",
                "test_date": datetime.date(2025, 4, 10),
                "notes": "IELTS Academic (Listening: 9.0, Reading: 8.5, Writing: 7.5, Speaking: 8.5). Official Degree English Medium Certificate also available."
            }
        )

        # 11. Story Bank
        Story.objects.get_or_create(
            user=user,
            title="Pioneering the UNILAG AI Student Mentorship Guild",
            defaults={
                "category": "leadership",
                "situation": "As an undergraduate in 2023, noticed a significant barrier for junior students transitioning into machine learning due to a lack of structured mentorship and GPU resources.",
                "challenge": "Over 120 aspiring students were struggling with mathematical foundations and practical coding environments without institutional funding.",
                "action": "Organized a 12-week peer-led cohort, negotiated cloud compute credits with local tech hubs, and authored an open-source syllabus covering Python, linear algebra, and PyTorch.",
                "result": "Mentored 85 students to completion. 14 participants secured competitive tech internships, and 3 won national hackathons.",
                "lesson_learned": "True leadership is about removing friction for others and creating self-sustaining learning communities.",
                "skills_demonstrated": "Curriculum Design, Resource Negotiation, Community Building, Empathetic Mentorship",
                "date_occurred": datetime.date(2023, 9, 15),
                "supporting_evidence": "GitHub repository with 400+ stars and university department commendation letter."
            }
        )
        Story.objects.get_or_create(
            user=user,
            title="Optimizing Edge Vision under Zero-Budget Hardware Constraints",
            defaults={
                "category": "problem_solving",
                "situation": "Field testing the cassava blight detection model in rural Ogun State revealed that existing heavy deep neural networks crashed on $40 Android devices used by local extension workers.",
                "challenge": "Needed to reduce model footprint by 70% and memory usage by 60% without sacrificing classification precision on subtle leaf lesions.",
                "action": "Applied post-training 8-bit integer quantization (INT8) and depthwise separable convolutions, pruning redundant weight matrices and testing against raw farm photos.",
                "result": "Reduced binary model size from 142MB down to 18.4MB, while maintaining 96.2% classification accuracy and running at 14 FPS locally without internet connectivity.",
                "lesson_learned": "Engineering elegance in developing economies requires designing for severe physical and connectivity constraints from day one.",
                "skills_demonstrated": "Model Quantization, PyTorch Optimization, Edge Computing, Experimental Verification",
                "date_occurred": datetime.date(2024, 4, 10),
                "supporting_evidence": "Undergraduate thesis honors distinction and published paper."
            }
        )

        # 12. Document Vault Seed Items
        Document.objects.get_or_create(
            user=user,
            title="Yohanna_Adebayo_Academic_CV_2026.pdf",
            defaults={
                "document_type": "cv",
                "file_size_bytes": 142800,
                "file_format": "pdf",
                "verification_status": "verified",
                "notes": "Up-to-date academic curriculum vitae highlighting UNILAG First Class, publications, and Helios Pay experience."
            }
        )
        Document.objects.get_or_create(
            user=user,
            title="UNILAG_Official_Transcript_Undergraduate.pdf",
            defaults={
                "document_type": "transcript",
                "file_size_bytes": 890400,
                "file_format": "pdf",
                "verification_status": "verified",
                "notes": "Complete 5-year official transcript issued by Academic Affairs, CGPA 4.86/5.00."
            }
        )
        Document.objects.get_or_create(
            user=user,
            title="Federal_Republic_of_Nigeria_Passport_DataPage.pdf",
            defaults={
                "document_type": "passport",
                "file_size_bytes": 450100,
                "file_format": "pdf",
                "expiration_date": datetime.date(2032, 8, 14),
                "verification_status": "verified",
                "notes": "Valid Nigerian e-Passport."
            }
        )

        # 13. Sources & 10 Realistic Opportunities
        sources_data = [
            ("European Commission (EACEA)", "https://www.eacea.ec.europa.eu/erasmus-plus_en", "erasmus"),
            ("DAAD German Academic Exchange Service", "https://www.daad.de/en/", "government"),
            ("British Council & FCDO (Chevening)", "https://www.chevening.org/", "government"),
            ("Commonwealth Scholarship Commission (CSC)", "https://cscuk.fcdo.gov.uk/", "government"),
            ("Campus France (Eiffel Excellence)", "https://www.campusfrance.org/en/eiffel-scholarship-program-of-excellence", "government"),
            ("Mastercard Foundation", "https://mastercardfdn.org/all/scholars/", "foundation"),
            ("ETH Zurich Financial Aid Office", "https://ethz.ch/en/studies/financial/scholarships/excellence.html", "university"),
            ("Gates Cambridge Trust", "https://www.gatescambridge.org/", "foundation"),
            ("Swedish Institute (SISGP)", "https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/", "government"),
            ("Swiss State Secretariat for Education (SERI)", "https://www.sbfi.admin.ch/sbfi/en/home/education/scholarships-and-grants/swiss-government-excellence-scholarships.html", "government"),
        ]
        source_objs = {}
        for s_name, s_url, s_type in sources_data:
            src, _ = OpportunitySource.objects.get_or_create(
                name=s_name,
                defaults={
                    "source_url": s_url,
                    "source_type": s_type,
                    "last_verified": timezone.now(),
                    "verification_notes": "Official government/agency portal verified by ScholarFlow compliance team."
                }
            )
            source_objs[s_name] = src

        now = timezone.now()
        opportunities_data = [
            {
                "title": "Erasmus Mundus Joint Master Degree in Artificial Intelligence (EMAI)",
                "provider": "European Commission & EMAI Consortium",
                "university": "Consortium: Universitat Pompeu Fabra (Spain), Sapienza (Italy), Radboud (Netherlands), Univ. of Ljubljana (Slovenia)",
                "country": "European Union (Multi-Country)",
                "degree_level": "masters",
                "field_of_study": "Artificial Intelligence, Data Science, Machine Learning, Robotics",
                "description": "A prestigious 2-year joint Master's programme in Artificial Intelligence offered across 4 top European research universities. Students study in at least two different European countries.",
                "funding_type": "fully_funded",
                "funding_details": "100% full tuition waiver + €1,400 monthly living allowance (€33,600 total) + €3,000 annual travel grant + comprehensive worldwide health insurance.",
                "eligibility_summary": "• Bachelor's in Computer Science, Mathematics, or related STEM field.\n• Minimum 2:1 or First Class equivalent.\n• Strong background in programming, calculus, and linear algebra.\n• Open to all international applicants globally.",
                "application_url": "https://www.emai-master.eu/apply",
                "official_source_url": "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
                "source": source_objs["European Commission (EACEA)"],
                "deadline": now + datetime.timedelta(days=45),
                "language_requirement": "IELTS 6.5+ (minimum 6.0 each band) or TOEFL 90+. Official Medium of Instruction certificate accepted upon appeal.",
                "academic_requirement": "Bachelor of Science in Computer Science, Software Engineering, Applied Math, or Electrical Engineering with First Class or 2:1 honours.",
                "work_experience_requirement": "No minimum work experience required; undergraduate research and project portfolios strongly weighted.",
                "nationality_requirement": "Open to all nationalities worldwide (Special Partner Country quotas for Sub-Saharan Africa).",
                "documents_required": "CV, Degree Transcript, Bachelor's Certificate, Motivation Letter (max 1000 words), 2 Academic Letters of Recommendation, Passport Copy.",
                "application_fee": "Free / €0",
            },
            {
                "title": "DAAD Helmut-Schmidt-Programme (Master's Scholarships in Public Policy & Good Governance)",
                "provider": "German Academic Exchange Service (DAAD)",
                "university": "Selected German Universities (Passau, Erfurt, Duisburg-Essen, Osnabrück)",
                "country": "Germany",
                "degree_level": "masters",
                "field_of_study": "Public Policy, Digital Governance, Development Economics, Social Sciences",
                "description": "Designed for future leaders from developing countries who wish to promote democracy and social justice in their home countries through postgraduate study in Germany.",
                "funding_type": "fully_funded",
                "funding_details": "€934 monthly living stipend + travel allowance + 6-month preparatory German language course + health insurance + study/research allowance.",
                "eligibility_summary": "• Citizen of a developing/emerging country (DAC list, including Nigeria).\n• Bachelor's degree obtained within the last 6 years with above-average grades.\n• Proven social or political commitment.",
                "application_url": "https://www.daad.de/helmut-schmidt",
                "official_source_url": "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/?status=3&origin=144&id=50026397",
                "source": source_objs["DAAD German Academic Exchange Service"],
                "deadline": now + datetime.timedelta(days=70),
                "language_requirement": "English proficiency (B2/C1, IELTS 6.5+ or TOEFL 80+) or German for select modules.",
                "academic_requirement": "Bachelor's degree with well-above-average grades (minimum 2:1 or First Class).",
                "work_experience_requirement": "Relevant practical experience or volunteering/leadership in civic or public initiatives preferred.",
                "nationality_requirement": "Nationals of DAC-listed developing countries (Nigeria eligible).",
                "documents_required": "DAAD Application Form, Hand-signed CV (Europass), Letter of Motivation, University Transcripts, Recommendation Letters, Work/Volunteer Certificates.",
                "application_fee": "Free",
            },
            {
                "title": "UK Chevening Scholarship (Fully Funded Master's in the United Kingdom)",
                "provider": "Foreign, Commonwealth & Development Office (FCDO)",
                "university": "Any UK University (Oxford, Cambridge, Imperial, UCL, Edinburgh, Manchester, etc.)",
                "country": "United Kingdom",
                "degree_level": "masters",
                "field_of_study": "All Master's disciplines (Computer Science, AI, Climate Policy, Global Health, Engineering, etc.)",
                "description": "The UK government's premier global scholarship programme. Fully funds a one-year Master's degree at any accredited UK university for individuals with demonstrable leadership potential.",
                "funding_type": "fully_funded",
                "funding_details": "Full university tuition fees (including MBA caps) + monthly living stipend + return economy flights to UK + arrival allowance + visa fee reimbursement.",
                "eligibility_summary": "• Citizen of a Chevening-eligible country (Nigeria is eligible).\n• Return to country of citizenship for minimum 2 years post-award.\n• Hold an undergraduate degree equivalent to UK 2:1 upper second-class.\n• Minimum 2 years (2,800 hours) work/internship experience.",
                "application_url": "https://www.chevening.org/apply/",
                "official_source_url": "https://www.chevening.org/scholarship/nigeria/",
                "source": source_objs["British Council & FCDO (Chevening)"],
                "deadline": now + datetime.timedelta(days=22),
                "language_requirement": "English requirement determined by chosen UK university unconditional offer.",
                "academic_requirement": "Undergraduate degree with minimum UK 2:1 equivalent (minimum 3.50/5.00 CGPA in Nigeria).",
                "work_experience_requirement": "Mandatory 2 years (2,800 hours) of work experience (full-time, part-time, internships, or volunteering).",
                "nationality_requirement": "Citizen of Nigeria / Chevening eligible country.",
                "documents_required": "Four 500-word Chevening Essays (Leadership, Networking, Study in the UK, Career Plan), 2 References, Degree Certificates & Transcripts.",
                "application_fee": "Free",
            },
            {
                "title": "Commonwealth Shared Scholarship Scheme",
                "provider": "Commonwealth Scholarship Commission (CSC UK)",
                "university": "Partnering UK Universities (e.g. Cranfield, Bristol, Leeds, Sheffield, Nottingham)",
                "country": "United Kingdom",
                "degree_level": "masters",
                "field_of_study": "Science & Technology for Development, Strengthening Health Systems, Global Prosperity, Climate Resilience",
                "description": "Jointly funded by the UK FCDO and participating UK universities for talented candidates from least developed and middle-income Commonwealth countries.",
                "funding_type": "fully_funded",
                "funding_details": "Approved airfare from home country to UK + 100% full tuition fees + monthly stipend of £1,347 (£1,652 in London) + warm clothing allowance.",
                "eligibility_summary": "• Citizen of or granted refugee status by a Commonwealth country (Nigeria).\n• Permanently resident in a developing Commonwealth country.\n• Hold first degree of at least upper second-class (2:1) standard.\n• Unable to afford study in the UK without scholarship.",
                "application_url": "https://cscuk.fcdo.gov.uk/apply/shared-scholarships/",
                "official_source_url": "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-shared-scholarships/",
                "source": source_objs["Commonwealth Scholarship Commission (CSC)"],
                "deadline": now + datetime.timedelta(days=55),
                "language_requirement": "Standard UK university admissions English proficiency.",
                "academic_requirement": "Minimum Second Class Upper (2:1) or First Class honours.",
                "work_experience_requirement": "No mandatory minimum, but developmental impact background weighted.",
                "nationality_requirement": "Commonwealth developing nations (including Nigeria, Ghana, Kenya).",
                "documents_required": "CSC Online Application, Academic Transcripts, Certified Degree Certificate, 2 Reference Letters, University Admission Letter.",
                "application_fee": "Free",
            },
            {
                "title": "France Eiffel Excellence Scholarship Programme",
                "provider": "French Ministry for Europe and Foreign Affairs",
                "university": "Participating French Higher Education Institutions (École Polytechnique, Sorbonne, PSL, Télécom Paris)",
                "country": "France",
                "degree_level": "masters",
                "field_of_study": "Computer Science & Artificial Intelligence, Engineering, Economics & Management, Law & Political Science",
                "description": "A prestigious French government grant to enable French higher education institutions to attract top foreign students for Master's and PhD programmes.",
                "funding_type": "fully_funded",
                "funding_details": "Monthly allowance of €1,181 + return international airfare + local transportation + health insurance + cultural activities and housing support.",
                "eligibility_summary": "• Foreign nationality (French dual nationals ineligible).\n• Maximum age of 25 years old at the date of committee evaluation.\n• Applied through a French university that nominates the candidate.",
                "application_url": "https://www.campusfrance.org/en/eiffel",
                "official_source_url": "https://www.campusfrance.org/en/the-eiffel-scholarship-program-of-excellence",
                "source": source_objs["Campus France (Eiffel Excellence)"],
                "deadline": now + datetime.timedelta(days=62),
                "language_requirement": "Programs taught in English require IELTS 6.5+ / TOEFL 90+; French programs require B2/C1 DELF/DALF.",
                "academic_requirement": "Outstanding academic record (Top 5-10% of graduating class / First Class Honours).",
                "work_experience_requirement": "None mandatory.",
                "nationality_requirement": "Non-French nationality (all developing nations eligible).",
                "documents_required": "CV (1-2 pages), Statement of Purpose, Official Transcripts, Academic Ranking/Grade Certificate, Letters of Recommendation.",
                "application_fee": "Free",
            },
            {
                "title": "Mastercard Foundation Scholars Program at Cambridge University",
                "provider": "Mastercard Foundation & University of Cambridge",
                "university": "University of Cambridge",
                "country": "United Kingdom",
                "degree_level": "masters",
                "field_of_study": "All one-year taught postgraduate Master's courses (MPhil in Machine Learning, Advanced Computer Science, etc.)",
                "description": "Provides full-cost scholarships to postgraduate students from Africa with outstanding academic ability who are committed to contributing to the transformation of Africa.",
                "funding_type": "fully_funded",
                "funding_details": "100% Cambridge University tuition fees + annual living stipend + return airfare to the UK + visa fees + laptop and settling-in grant.",
                "eligibility_summary": "• Citizen of an African country.\n• Ordinarily resident in Africa.\n• Applying for a one-year Master's course at Cambridge.\n• Demonstrable commitment to give back to Africa.",
                "application_url": "https://www.postgraduate.study.cam.ac.uk/funding/mastercard-foundation-scholars-program",
                "official_source_url": "https://www.mastercardfdn.cam.ac.uk/",
                "source": source_objs["Mastercard Foundation"],
                "deadline": now + datetime.timedelta(days=35),
                "language_requirement": "Cambridge postgraduate English language requirement (IELTS 7.5 overall with 7.0 minimum).",
                "academic_requirement": "First Class Honours degree (minimum 4.50/5.00 CGPA in Nigerian system).",
                "work_experience_requirement": "Leadership track record and social impact orientation.",
                "nationality_requirement": "African country citizenship and residence (Nigeria eligible).",
                "documents_required": "Cambridge Application, Transcripts, CV, 2 Academic References, Research/Personal Statement, Mastercard Foundation Supplemental Statement.",
                "application_fee": "Fee waiver available for African applicants via applicant portal.",
            },
            {
                "title": "ETH Zurich Excellence Scholarship & Opportunity Programme (ESOP)",
                "provider": "ETH Zurich Foundation",
                "university": "ETH Zurich (Swiss Federal Institute of Technology)",
                "country": "Switzerland",
                "degree_level": "masters",
                "field_of_study": "Computer Science, Data Science, Cyber Security, Robotics, Electrical Engineering, Physics",
                "description": "Supports outstanding students wishing to pursue their Master's degree at ETH Zurich. Covers the full cost of study and living expenses in Zurich.",
                "funding_type": "fully_funded",
                "funding_details": "Grant for study and living costs of CHF 12,000 per semester (CHF 24,000 / ~€25,000 per year) + full tuition fee waiver + personal mentoring.",
                "eligibility_summary": "• Very good result in Bachelor's (top 10% of bachelor program = Grade A).\n• Applying for an ETH Zurich Master's degree program.\n• Comprehensive pre-proposal for Master's thesis.",
                "application_url": "https://ethz.ch/en/studies/financial/scholarships/excellence.html",
                "official_source_url": "https://ethz.ch/students/en/studies/financial/scholarships/excellence.html",
                "source": source_objs["ETH Zurich Financial Aid Office"],
                "deadline": now + datetime.timedelta(days=78),
                "language_requirement": "C1 level English (IELTS 7.0+ or TOEFL 100+).",
                "academic_requirement": "Bachelor's degree with Grade A / First Class Honours (Top 10% class ranking certificate required).",
                "work_experience_requirement": "Research portfolio and rigorous quantitative background.",
                "nationality_requirement": "Open to all national and international applicants.",
                "documents_required": "ETH Online Master Application, ESOP Letter of Motivation, Master Thesis Pre-Proposal (max 3 pages), 2 Reference Letters, Official Transcripts.",
                "application_fee": "CHF 150",
            },
            {
                "title": "Gates Cambridge Scholarship",
                "provider": "Bill & Melinda Gates Foundation & University of Cambridge",
                "university": "University of Cambridge",
                "country": "United Kingdom",
                "degree_level": "masters",
                "field_of_study": "All full-time postgraduate degrees (MPhil, MSc, PhD) offered at Cambridge",
                "description": "One of the most prestigious international scholarships in the world. Awarded to outstanding applicants from countries outside the UK to pursue a full-time postgraduate degree in any subject available at Cambridge.",
                "funding_type": "fully_funded",
                "funding_details": "University Composition Fee + maintenance allowance of £20,000 per annum + single economy airfare + visa and healthcare surcharge + discretionary academic development funding.",
                "eligibility_summary": "• Citizen of any country outside the United Kingdom.\n• Applying to pursue a full-time Master's or PhD at Cambridge.\n• Outstanding intellectual ability, leadership potential, and commitment to improving the lives of others.",
                "application_url": "https://www.gatescambridge.org/apply/how-apply/",
                "official_source_url": "https://www.gatescambridge.org/about/",
                "source": source_objs["Gates Cambridge Trust"],
                "deadline": now + datetime.timedelta(days=29),
                "language_requirement": "IELTS Academic 7.5 or TOEFL 107+.",
                "academic_requirement": "First Class degree or equivalent (CGPA 4.75+/5.00).",
                "work_experience_requirement": "Demonstrated social impact and commitment to improving global human well-being.",
                "nationality_requirement": "All non-UK citizens (Nigerians eligible).",
                "documents_required": "Cambridge Application Form, Gates Cambridge Reference, 500-word Statement of Intent, Research Proposal, Academic Transcripts.",
                "application_fee": "Fee waiver provided for eligible international applicants.",
            },
            {
                "title": "Swedish Institute Scholarships for Global Professionals (SISGP)",
                "provider": "Swedish Institute (SI)",
                "university": "All Swedish Universities (KTH Royal Institute of Technology, Lund, Uppsala, Chalmers)",
                "country": "Sweden",
                "degree_level": "masters",
                "field_of_study": "Computer Science, Sustainable Tech, Global Health, Engineering, Environmental Science",
                "description": "A funded scholarship programme for global professionals from selected countries to pursue a full-time 1 or 2-year Master's degree in Sweden.",
                "funding_type": "fully_funded",
                "funding_details": "Full tuition fee payment directly to Swedish university + monthly living allowance of SEK 12,000 (~€1,050) + SEK 15,000 travel grant + insurance + membership in SI Network for Future Global Leaders.",
                "eligibility_summary": "• Citizen of an SI-eligible country (Nigeria is eligible).\n• Have minimum 3,000 hours of documented work/leadership experience.\n• Admitted to an eligible Master's programme in Sweden.",
                "application_url": "https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/",
                "official_source_url": "https://si.se/en/apply/scholarships/",
                "source": source_objs["Swedish Institute (SISGP)"],
                "deadline": now + datetime.timedelta(days=90),
                "language_requirement": "English 6 / IELTS 6.5+ determined by Swedish University Admissions.",
                "academic_requirement": "Bachelor's degree equivalent to Swedish Kandidatexamen (Second Class Upper or First Class).",
                "work_experience_requirement": "Mandatory 3,000 hours of certified work experience (employment, freelance, or long-term volunteering).",
                "nationality_requirement": "Citizens of eligible SI countries (including Nigeria).",
                "documents_required": "SI Europass CV, 2 Letters of Reference, Proof of Work and Leadership Experience Form, Copy of Valid Passport.",
                "application_fee": "University Admissions Sweden fee (SEK 900) - scholarship itself is free.",
            },
            {
                "title": "Swiss Government Excellence Scholarships for Foreign Scholars",
                "provider": "Federal Commission for Scholarships for Foreign Students (FCS)",
                "university": "All Swiss Cantonal Universities and Federal Institutes (EPFL, ETH, Basel, Zurich, Geneva)",
                "country": "Switzerland",
                "degree_level": "fellowship",
                "field_of_study": "All academic fields (Research Master's, PhD, Postdoc, Research Fellowships)",
                "description": "Aimed at young researchers from abroad who have completed a Master's or Bachelor's degree with distinction, to enable academic research stays in Switzerland.",
                "funding_type": "fully_funded",
                "funding_details": "Monthly scholarship of CHF 1,920 + mandatory Swiss health insurance + return airfare + housing allowance of CHF 300.",
                "eligibility_summary": "• Bachelor's/Master's degree achieved before start date with distinction.\n• Mandatory letter of acceptance from a Swiss academic professor willing to supervise research.\n• Comprehensive research proposal with timeline.",
                "application_url": "https://www.sbfi.admin.ch/scholarships_eng",
                "official_source_url": "https://www.sbfi.admin.ch/sbfi/en/home/education/scholarships-and-grants/swiss-government-excellence-scholarships.html",
                "source": source_objs["Swiss State Secretariat for Education (SERI)"],
                "deadline": now + datetime.timedelta(days=110),
                "language_requirement": "Language skills necessary for the research (English / German / French).",
                "academic_requirement": "First Class Honours with recognized research thesis.",
                "work_experience_requirement": "Prior research experience or publication record.",
                "nationality_requirement": "Open to over 180 countries (Nigeria eligible through Swiss Embassy Abuja).",
                "documents_required": "FCS Application Form, Research Proposal, Professor's Letter of Support, 2 Confidential Recommendation Letters, Certified Transcripts.",
                "application_fee": "Free",
            }
        ]

        created_opps = []
        for opp_data in opportunities_data:
            opp, _ = Opportunity.objects.get_or_create(
                title=opp_data["title"],
                provider=opp_data["provider"],
                defaults=opp_data
            )
            created_opps.append(opp)

        # 14. Create sample Application Workspace for Yohanna on EMAI
        emai_opp = created_opps[0]
        app, app_created = Application.objects.get_or_create(
            user=user,
            opportunity=emai_opp,
            defaults={
                "status": "in_progress",
                "personal_notes": "Prioritize Sapienza (Italy) & UPF (Spain) mobility tracks. Finalize recommendation letters with Dr. Okonjo and Prof. Balogun.",
                "target_submission_date": (now + datetime.timedelta(days=30)).date()
            }
        )
        if app_created:
            # Requirements
            cv_doc = user.documents.filter(document_type='cv').first()
            transcript_doc = user.documents.filter(document_type='transcript').first()
            passport_doc = user.documents.filter(document_type='passport').first()

            ApplicationRequirement.objects.create(
                application=app,
                name="Academic Curriculum Vitae (CV)",
                description="Tailored 2-page academic CV with research focus.",
                is_mandatory=True,
                status="complete",
                attached_document=cv_doc,
                order=1
            )
            ApplicationRequirement.objects.create(
                application=app,
                name="Official Undergraduate Transcript",
                description="UNILAG Certified Transcript (CGPA 4.86/5.00).",
                is_mandatory=True,
                status="complete",
                attached_document=transcript_doc,
                order=2
            )
            ApplicationRequirement.objects.create(
                application=app,
                name="Motivation Letter / Statement of Purpose (AI & Edge Systems)",
                description="Max 1000 words statement articulating research interests and European mobility track choices.",
                is_mandatory=True,
                status="needs_review",
                draft_response=(
                    "My ambition to pursue the Erasmus Mundus Joint Master Degree in Artificial Intelligence (EMAI) "
                    "arises from my dedicated research in machine learning efficiency and my conviction that cutting-edge AI architectures "
                    "must be democratized for resource-constrained environments.\n\n"
                    "Graduating with First-Class Honours in Computer Science from the University of Lagos (CGPA 4.86/5.00), "
                    "I focused my undergraduate thesis on developing lightweight edge vision networks for agricultural disease detection ('AgriVision-Africa'). "
                    "By implementing post-training quantization and depthwise convolutions, my team reduced neural network footprints by 87% "
                    "while retaining 96.2% diagnostic accuracy on low-cost mobile hardware.\n\n"
                    "The EMAI curriculum offers the exact dual mobility structure I need to expand this work: diving into fundamental mathematical "
                    "foundations and deep probabilistic modelling at Universitat Pompeu Fabra, followed by advanced robotics and neural reasoning "
                    "at Sapienza University of Rome. Under the mentorship of European faculty, I intend to bridge theoretical deep learning with resilient "
                    "distributed architectures, equipping me to lead transformative applied research across Sub-Saharan Africa upon completion."
                ),
                ai_grounding_notes="Grounding verified against: UNILAG First Class Degree (4.86 CGPA), AgriVision Thesis Project, Helios Pay Experience, and Mentorship Guild Story.",
                order=3
            )
            ApplicationRequirement.objects.create(
                application=app,
                name="Academic Reference Letter (Prof. Balogun - UNILAG)",
                description="Letter from undergraduate Department Head verifying research merit.",
                is_mandatory=True,
                status="in_progress",
                order=4
            )
            ApplicationRequirement.objects.create(
                application=app,
                name="Valid International Passport Data Page",
                description="High-resolution scan of Nigerian passport bio page.",
                is_mandatory=True,
                status="complete",
                attached_document=passport_doc,
                order=5
            )

            # Tasks
            ApplicationTask.objects.create(
                application=app,
                title="Follow up with Prof. Balogun regarding recommendation upload",
                description="Send reminder regarding the EMAI portal reference form deadline.",
                is_completed=False,
                due_date=(now + datetime.timedelta(days=7)).date(),
                created_by_ai=True
            )
            ApplicationTask.objects.create(
                application=app,
                title="Final review of Motivation Statement draft with AI Assistant",
                description="Verify that the Sapienza laboratory track details are customized.",
                is_completed=False,
                due_date=(now + datetime.timedelta(days=10)).date(),
                created_by_ai=True
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(created_opps)} opportunities, Yohanna Adebayo's profile, Story Bank, and Application Workspace!"))
