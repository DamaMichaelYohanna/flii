from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Disallow: /admin/",
        "Allow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('scholarships/', include('opportunities.urls')),
    path('blog/', include('blog.urls')),
    path('assistance/', include('assistance.urls')),
    path('subscriptions/', include('subscriptions.urls')),

    # User Dashboard & Private Workspaces
    path('dashboard/', include('dashboard.urls')),
    path('dashboard/applications/', include('applications.urls')),
    path('dashboard/documents/', include('documents.urls')),
    path('dashboard/stories/', include('stories.urls')),
    path('dashboard/profile/', include('applicants.urls')),
    path('dashboard/agent/', include('agent_hub.urls')),
    path('dashboard/notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
