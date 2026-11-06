from django import forms
from blog.models import Post, PostCategory
from opportunities.models import Opportunity
from assistance.models import AssistanceBooking


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'category', 'summary', 'content',
            'featured_image_url', 'is_breaking_news', 'is_pinned',
            'status', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-semibold text-slate-800 placeholder-slate-400',
                'placeholder': 'e.g. Complete Guide to Winning Chevening Scholarship 2026/2027'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500',
                'placeholder': 'Leave blank to auto-generate from title'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800'
            }),
            'summary': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
                'placeholder': 'A captivating 2-3 sentence overview for previews, SEO description, and card listings...'
            }),
            'content': forms.Textarea(attrs={
                'rows': 16,
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400 leading-relaxed',
                'placeholder': 'Write the full article body here. Markdown headers (##, ###), bullet points, bold (**text**), and paragraphs are supported...'
            }),
            'featured_image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
                'placeholder': 'https://images.unsplash.com/photo-...'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
                'placeholder': 'Scholarships, UK, Visa, DAAD, Postgraduate (comma-separated)'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800'
            }),
            'is_breaking_news': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500'
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500'
            }),
        }


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            'title', 'slug', 'provider', 'university', 'country',
            'degree_level', 'funding_type', 'field_of_study',
            'funding_details', 'eligibility_summary', 'description',
            'opening_date', 'deadline', 'deadline_timezone', 'cycle_name', 'start_date', 'duration',
            'application_url', 'official_source_url', 'portal_type',
            'image_url', 'image', 'is_featured',
            'academic_requirement', 'language_requirement', 'work_experience_requirement',
            'nationality_requirement', 'documents_required', 'how_to_apply',
            'application_fee', 'status', 'verification_status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'e.g. DAAD Helmut Schmidt Masters Scholarship 2026'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-600 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'Leave blank to auto-generate from title'
            }),
            'provider': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'e.g. German Academic Exchange Service (DAAD) / Chevening'
            }),
            'university': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'e.g. Participating Universities in Germany / Oxford'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'e.g. Germany, United Kingdom, France, European Union'
            }),
            'degree_level': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'funding_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'field_of_study': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'e.g. Public Policy, Computer Science, Engineering, All Disciplines'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none leading-relaxed',
                'placeholder': 'Comprehensive description of the scholarship, objectives, and university environment...'
            }),
            'funding_details': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none leading-relaxed',
                'placeholder': 'Breakdown of coverage: 100% Tuition waiver, monthly stipend of €934, travel allowance, health insurance...'
            }),
            'eligibility_summary': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none leading-relaxed',
                'placeholder': 'Clear bullet points on target applicants, nationality restrictions, degree level requirements...'
            }),
            'opening_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'deadline_timezone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'UTC, CET, GMT'
            }),
            'cycle_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': '2026/2027 Academic Year'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': '24 Months (2 Years)'
            }),
            'application_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'https://portal.provider.org/apply'
            }),
            'official_source_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'https://www.provider.org/scholarship-details'
            }),
            'portal_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'https://images.unsplash.com/...'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500'
            }),
            'academic_requirement': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': "Minimum Bachelor degree with Second Class Upper (2:1) or First Class honours"
            }),
            'language_requirement': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': "IELTS 6.5+, TOEFL 90+, or official English Medium of Instruction accepted"
            }),
            'work_experience_requirement': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': "Minimum 2 years professional work experience, or fresh graduates accepted"
            }),
            'nationality_requirement': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': "Developing countries (including Nigeria, Ghana, Kenya, India) or open globally"
            }),
            'documents_required': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': "CV / Resume, Statement of Purpose, Official Academic Transcripts, 2 Recommendation Letters, Passport"
            }),
            'how_to_apply': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': "1. Register portal account, 2. Complete eligibility form, 3. Upload dossier..."
            }),
            'application_fee': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none',
                'placeholder': 'Free / No Application Fee'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
            'verification_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none'
            }),
        }
