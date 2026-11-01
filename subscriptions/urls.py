from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.pricing_plans_view, name='pricing'),
    path('checkout/<int:plan_id>/', views.checkout_initialize_view, name='checkout'),
    path('callback/', views.paystack_callback_view, name='callback'),
    path('webhook/', views.paystack_webhook_view, name='webhook'),
    path('sandbox/<str:reference>/', views.test_sandbox_checkout_view, name='sandbox_checkout'),
    path('manage/', views.manage_subscription_view, name='manage'),
    path('cancel/', views.cancel_subscription_view, name='cancel'),
]
