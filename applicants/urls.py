from django.urls import path
from . import views

app_name = 'applicants'

urlpatterns = [
    path('', views.profile_view, name='profile_view'),
]
