from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from blog.models import PostCategory, Post

class BlogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin_author',
            email='admin_author@example.com',
            password='Password123!'
        )
        self.category = PostCategory.objects.create(
            name='Visa & Migration',
            slug='visa-migration',
            badge_color='bg-rose-50 text-rose-700 border-rose-200'
        )
        self.published_post = Post.objects.create(
            title="Portugal Migration Report 2025",
            author=self.user,
            category=self.category,
            summary="Key changes for students in Portugal under Law 62/2026.",
            content="This is the full report on Portugal migration policies with multiple words to test reading time calculation properly.",
            status='published',
            is_breaking_news=True,
            tags="Portugal, Visa, Students"
        )
        self.draft_post = Post.objects.create(
            title="Upcoming Draft Guide",
            author=self.user,
            category=self.category,
            summary="Draft content not yet published.",
            content="Work in progress.",
            status='draft'
        )

    def test_post_creation_and_slug_auto_generation(self):
        self.assertTrue(self.published_post.slug.startswith("portugal-migration-report-2025"))
        self.assertEqual(self.published_post.reading_time, 1)
        self.assertEqual(self.published_post.tag_list, ["Portugal", "Visa", "Students"])
        self.assertEqual(self.published_post.author_display_name, "Admin")

    def test_published_post_author_display_uses_admin_not_email(self):
        detail_url = reverse('blog:detail', kwargs={'slug': self.published_post.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin")
        self.assertNotContains(response, self.user.email)

        list_url = reverse('blog:list')
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Admin")
        self.assertNotContains(list_response, self.user.email)

    def test_blog_list_view_renders_published_posts(self):
        response = self.client.get(reverse('blog:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portugal Migration Report 2025")
        self.assertContains(response, "Breaking News")
        # Draft should NOT be in the response
        self.assertNotContains(response, "Upcoming Draft Guide")

    def test_category_filtering(self):
        response = self.client.get(reverse('blog:list') + '?category=visa-migration')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portugal Migration Report 2025")

    def test_search_filtering(self):
        response = self.client.get(reverse('blog:list') + '?q=Portugal')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portugal Migration Report 2025")

        # Irrelevant search
        empty_response = self.client.get(reverse('blog:list') + '?q=NonExistentSubjectXYZ')
        self.assertEqual(empty_response.status_code, 200)
        self.assertContains(empty_response, "No articles found")

    def test_blog_detail_view_increments_views(self):
        detail_url = reverse('blog:detail', kwargs={'slug': self.published_post.slug})
        initial_views = self.published_post.views_count
        
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portugal Migration Report 2025")
        self.assertNotContains(response, "Executive Briefing")
        
        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.views_count, initial_views + 1)

    def test_draft_post_returns_404_for_anonymous_user(self):
        draft_url = reverse('blog:detail', kwargs={'slug': self.draft_post.slug})
        response = self.client.get(draft_url)
        self.assertEqual(response.status_code, 404)

    def test_wysiwyg_html_content_rendering(self):
        html_post = Post.objects.create(
            title="Fulbright Scholarship 2026 Strategy",
            author=self.user,
            category=self.category,
            summary="Essential insights for the Fulbright Foreign Student Program.",
            content="<h2>Application Pillars</h2><p>Focus on your <strong>Study Objective</strong> statement.</p><ul><li>Leadership</li><li>Cultural Exchange</li></ul>",
            status='published'
        )
        self.assertTrue(html_post.has_html_content)
        self.assertEqual(html_post.reading_time, 1)

        detail_url = reverse('blog:detail', kwargs={'slug': html_post.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        # Verify HTML tags are rendered as active HTML elements, not escaped entities
        self.assertContains(response, "<h2>Application Pillars</h2>")
        self.assertContains(response, "<strong>Study Objective</strong>")
        self.assertNotContains(response, "&lt;h2&gt;Application Pillars&lt;/h2&gt;")

    def test_escaped_html_content_auto_unescaped(self):
        # Even if content was accidentally saved with escaped HTML tags (e.g. from plain pasting)
        escaped_post = Post.objects.create(
            title="Poland NAWA Document Verification Guide",
            author=self.user,
            category=self.category,
            summary="New NAWA rules for students in Poland.",
            content="<p>&lt;h2&gt;Overview: Major Reforms in Poland&lt;/h2&gt;&lt;p&gt;If you are planning to study in Poland...&lt;/p&gt;</p>",
            status='published'
        )
        self.assertTrue(escaped_post.has_html_content)
        self.assertIn("<h2>Overview: Major Reforms in Poland</h2>", escaped_post.rendered_content)

        detail_url = reverse('blog:detail', kwargs={'slug': escaped_post.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Overview: Major Reforms in Poland</h2>")
        self.assertNotContains(response, "&lt;h2&gt;")
