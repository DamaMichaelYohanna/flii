from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('', views.application_list, name='list'),
    path('tasks/', views.application_tasks, name='tasks'),
    path('tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),
    path('start/<int:opportunity_id>/', views.create_from_opportunity, name='create_from_opportunity'),
    path('<int:pk>/', views.application_detail, name='detail'),
    path('<int:pk>/auto-assemble/', views.auto_assemble_view, name='auto_assemble'),
    path('<int:pk>/dossier/', views.application_dossier_view, name='dossier'),
    path('api/ai-draft/', views.ajax_ai_draft, name='ajax_ai_draft'),
]

