from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('<int:pk>/download/', views.document_download, name='download'),
    path('<int:pk>/delete/', views.document_delete, name='delete'),
]
