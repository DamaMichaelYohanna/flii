
from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('', views.opportunity_list, name='list'),
    path('import/', views.opportunity_import, name='import'),
    path('scout/run/', views.run_scout_discovery, name='run_scout'),
    path('<int:pk>/', views.opportunity_detail, name='detail'),
    path('<int:pk>/shortlist/', views.toggle_shortlist, name='toggle_shortlist'),
    path('<int:pk>/eligibility-check/', views.assess_eligibility_api, name='eligibility_api'),
]
