from django.contrib import admin
from .models import PostCategory, Post

@admin.register(PostCategory)
class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'badge_color', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_breaking_news', 'is_pinned', 'author', 'published_at', 'views_count')
    list_filter = ('status', 'is_breaking_news', 'is_pinned', 'category', 'published_at')
    search_fields = ('title', 'summary', 'content', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'published_at'
    actions = ['make_published', 'make_breaking', 'clear_breaking']

    def make_published(self, request, queryset):
        rows_updated = queryset.update(status='published')
        self.message_user(request, f"{rows_updated} posts marked as Published.")
    make_published.short_description = "Publish selected posts"

    def make_breaking(self, request, queryset):
        rows_updated = queryset.update(is_breaking_news=True)
        self.message_user(request, f"{rows_updated} posts marked as Breaking News.")
    make_breaking.short_description = "Mark as Breaking News"

    def clear_breaking(self, request, queryset):
        rows_updated = queryset.update(is_breaking_news=False)
        self.message_user(request, f"{rows_updated} posts cleared from Breaking News.")
    clear_breaking.short_description = "Clear Breaking News flag"
