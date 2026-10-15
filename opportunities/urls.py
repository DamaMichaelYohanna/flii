
from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('', views.opportunity_list, name='list'),
    path('import/', views.opportunity_import, name='import'),
    path('scout/run/', views.run_scout_discovery, name='run_scout'),
    path('scan-all/', views.scan_all_portals_view, name='scan_all_portals'),
    path('admin/scout/', views.admin_scout_hub, name='admin_scout_hub'),
    path('admin/scout/trigger/', views.admin_trigger_scout_api, name='admin_trigger_scout'),
    path('admin/scout/publish-all/', views.admin_publish_all, name='admin_publish_all'),
    path('admin/scout/<int:pk>/publish/', views.admin_publish_opportunity, name='admin_publish'),
    path('admin/scout/<int:pk>/delete/', views.admin_delete_opportunity, name='admin_delete'),
    path('admin/scout/sources/<int:pk>/toggle/', views.admin_toggle_source, name='admin_toggle_source'),
    path('admin/scout/sources/add/', views.admin_add_source, name='admin_add_source'),
    path('<int:pk>/', views.opportunity_detail, name='detail'),
    path('<int:pk>/scan/', views.scan_portal_view, name='scan_portal'),
    path('<int:pk>/shortlist/', views.toggle_shortlist, name='toggle_shortlist'),
    path('<int:pk>/eligibility-check/', views.assess_eligibility_api, name='eligibility_api'),
]
