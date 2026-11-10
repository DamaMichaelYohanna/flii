from django import forms
from blog.models import Post, PostCategory
from opportunities.models import Opportunity
from assistance.models import AssistanceBooking


class BlogPostForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=PostCategory.objects.all(),
        required=False,
        empty_label="— No Category (Optional) —",
        widget=forms.Select(attrs={
            'id': 'id_category',
            'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800'
        })
    )
    summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
            'placeholder': 'Optional: Short summary for search engine snippets and social cards...'
        }),
        required=False
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'id_content',
            'rows': 16,
            'class': 'hidden',
        }),
        required=False
    )

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
            'summary': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
                'placeholder': 'A captivating 2-3 sentence overview for previews, SEO description, and card listings...'
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

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        import html, re
        for _ in range(4):
            if '&lt;' in content or '&amp;lt;' in content:
                new_content = html.unescape(content)
                if new_content == content:
                    break
                content = new_content
            else:
                break
        content = re.sub(r'<p>\s*(<(?:h[1-6]|ul|ol|blockquote|div|pre)[^>]*>)', r'\1', content)
        content = re.sub(r'(</(?:h[1-6]|ul|ol|blockquote|div|pre)>)\s*</p>', r'\1', content)

        from django.utils.html import strip_tags
        clean_text = strip_tags(content).strip()
        if not content or (not clean_text and '<img' not in content and '<iframe' not in content):
            raise forms.ValidationError("Article body content cannot be empty.")
        return content


class PostCategoryForm(forms.ModelForm):
    COLOR_CHOICES = [
        ('bg-blue-50 text-blue-700 border-blue-200', 'Blue (Classic / Strategy)'),
        ('bg-emerald-50 text-emerald-700 border-emerald-200', 'Emerald (Scholarships / Funding)'),
        ('bg-rose-50 text-rose-700 border-rose-200', 'Rose (Visa / Migration Alerts)'),
        ('bg-purple-50 text-purple-700 border-purple-200', 'Purple (Admissions / Guides)'),
        ('bg-amber-50 text-amber-700 border-amber-200', 'Amber (Opportunities / Deadlines)'),
        ('bg-sky-50 text-sky-700 border-sky-200', 'Sky (Resources / Updates)'),
    ]

    badge_color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        initial='bg-blue-50 text-blue-700 border-blue-200',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800'
        })
    )

    class Meta:
        model = PostCategory
        fields = ['name', 'slug', 'description', 'badge_color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-semibold text-slate-800 placeholder-slate-400',
                'placeholder': 'e.g. Visa & Migration Alerts'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500',
                'placeholder': 'Leave blank to auto-generate'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
                'placeholder': 'Short description of this category topic...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800 placeholder-slate-400',
                'placeholder': 'e.g. flag, graduation-cap, book-open, file-text'
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
