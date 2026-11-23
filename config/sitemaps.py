from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Post
from opportunities.models import Opportunity


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return [
            "accounts:landing",
            "accounts:login",
            "accounts:register",
            "accounts:password_reset",
            "opportunities:list",
            "blog:list",
            "assistance:home",
            "subscriptions:pricing",
        ]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.objects.filter(status="published").select_related("category")

    def lastmod(self, obj):
        return obj.updated_at


class OpportunitySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Opportunity.objects.filter(status="active")

    def lastmod(self, obj):
        return obj.updated_at
