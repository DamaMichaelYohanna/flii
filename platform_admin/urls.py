from django.urls import path
from . import views

app_name = 'platform_admin'

urlpatterns = [
    # Command Center
    path('', views.dashboard_view, name='dashboard'),

    # Blog Management ("POST BLOGS")
    path('blogs/', views.blog_list, name='blog_list'),
    path('blogs/create/', views.blog_create, name='blog_create'),
    path('blogs/<int:pk>/edit/', views.blog_edit, name='blog_edit'),
    path('blogs/<int:pk>/delete/', views.blog_delete, name='blog_delete'),
    path('blogs/<int:pk>/toggle-status/', views.blog_toggle_status, name='blog_toggle_status'),
    path('blogs/categories/', views.blog_category_list, name='blog_category_list'),
    path('blogs/categories/quick-create/', views.blog_category_quick_create, name='blog_category_quick_create'),
    path('blogs/categories/<int:pk>/delete/', views.blog_category_delete, name='blog_category_delete'),

    # Scholarship Opportunities ("UPLOAD SCHOLARSHIP OPPORTUNITIES")
    path('opportunities/', views.opportunity_list, name='opportunity_list'),
    path('opportunities/create/', views.opportunity_create, name='opportunity_create'),
    path('opportunities/<int:pk>/edit/', views.opportunity_edit, name='opportunity_edit'),
    path('opportunities/<int:pk>/delete/', views.opportunity_delete, name='opportunity_delete'),
    path('opportunities/<int:pk>/toggle-featured/', views.opportunity_toggle_featured, name='opportunity_toggle_featured'),

    # Registered Users ("SEE REGISTERED USERS")
    path('users/', views.user_list, name='user_list'),
    path('users/export/', views.user_export_csv, name='user_export'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:user_id>/toggle-verified/', views.user_toggle_verified, name='user_toggle_verified'),
    path('users/<int:user_id>/notify/', views.user_send_notification, name='user_send_notification'),

    # Paid Requests & Financials ("SEE PAID REQUEST")
    path('paid-requests/', views.paid_requests_hub, name='paid_requests'),
    path('paid-requests/<int:pk>/', views.paid_request_detail, name='paid_request_detail'),

    # Application Dossiers Pipeline
    path('applications/', views.applications_pipeline, name='applications_pipeline'),

    # System Health & Telemetry
    path('system/', views.system_health, name='system_health'),
]
