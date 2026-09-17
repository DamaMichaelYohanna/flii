from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_page_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('auth/google/login/', views.google_login_view, name='google_login'),
    path('auth/google/callback/', views.google_callback_view, name='google_callback'),
]
