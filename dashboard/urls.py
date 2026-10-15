from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('admin/', views.admin_system_dashboard, name='admin_system_dashboard'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/users/<int:user_id>/toggle-staff/', views.admin_toggle_user_staff, name='admin_toggle_user_staff'),
    path('admin/applications/', views.admin_applications_view, name='admin_applications'),
]
