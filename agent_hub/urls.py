from django.urls import path
from . import views

app_name = 'agent_hub'

urlpatterns = [
    path('actions/', views.action_list, name='action_list'),
    path('actions/<int:pk>/', views.action_detail, name='action_detail'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
]
