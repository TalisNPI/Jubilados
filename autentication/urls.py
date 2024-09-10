from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('', views.home_view, name='home'),  # Página de inicio
    path('add_reservation/', views.add_reservation, name='add_reservation'),
    path('reservations/', views.all_reservations_view, name='all_reservations'),
    path('reservations/edit/<int:pk>/', views.edit_reservation, name='edit_reservation'),
    path('reservations/delete/<int:pk>/', views.delete_reservation, name='delete_reservation'),
    path('purchases/', include('purchases.urls')),
    path('get_reservations/', views.get_reservations, name='get_reservations'),  
    path('get_reservations_for_date/', views.get_reservations_for_date, name='get_reservations_for_date'),
    path('select_camarero/', views.select_camarero, name='select_camarero'),
]
