from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_purchase, name='add_purchase'),
    path('', views.all_purchases_view, name='all_purchases'),
    path('edit/<int:purchase_id>/', views.edit_purchase, name='edit_purchase'),
    path('delete/<int:purchase_id>/', views.delete_purchase, name='delete_purchase'),
    path('add-ajuste/', views.add_ajuste_pedido, name='add_ajuste_pedido'),
    path('generate_qr_code/', views.generate_qr_code, name='generate_qr_code'),
]
