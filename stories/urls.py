from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    path('', views.story_list, name='list'),
    path('<int:pk>/delete/', views.story_delete, name='delete'),
]
