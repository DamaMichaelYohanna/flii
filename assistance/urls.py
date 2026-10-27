from django.urls import path
from . import views

app_name = 'assistance'

urlpatterns = [
    # Applicant facing
    path('', views.assistance_home, name='home'),
    path('book/', views.book_assistance, name='book'),
    path('book/<slug:package_slug>/', views.book_assistance, name='book_package'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:pk>/payment/', views.booking_payment_submit, name='booking_payment_submit'),

    # Admin / Staff management
    path('admin/', views.admin_bookings_hub, name='admin_hub'),
    path('admin/booking/<int:pk>/', views.admin_booking_detail, name='admin_booking_detail'),
]
