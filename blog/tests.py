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
        self.assertContains(response, "Executive Briefing")
        
        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.views_count, initial_views + 1)

    def test_draft_post_returns_404_for_anonymous_user(self):
        draft_url = reverse('blog:detail', kwargs={'slug': self.draft_post.slug})
        response = self.client.get(draft_url)
        self.assertEqual(response.status_code, 404)
