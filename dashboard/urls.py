from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('admin/', views.admin_system_dashboard, name='admin_system_dashboard'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/users/export/', views.admin_users_export_csv, name='admin_users_export'),
    path('admin/users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('admin/users/<int:user_id>/toggle-staff/', views.admin_toggle_user_staff, name='admin_toggle_user_staff'),
    path('admin/users/<int:user_id>/toggle-active/', views.admin_toggle_user_active, name='admin_toggle_user_active'),
    path('admin/users/<int:user_id>/toggle-verified/', views.admin_toggle_user_verified, name='admin_toggle_user_verified'),
    path('admin/users/<int:user_id>/notify/', views.admin_send_user_notification, name='admin_send_user_notification'),
    path('admin/applications/', views.admin_applications_view, name='admin_applications'),
]
