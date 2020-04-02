from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('product/<slug>/', views.ItemDetailView.as_view(), name='product'),
    path('order-summary/', views.OrderSummaryView.as_view(), name='order-summary'),
    path('add-single-to-cart/<item_id>/', views.add_single_to_cart, name='add-single-to-cart'),
    path('remove-single-from-cart/<item_id>/', views.remove_single_from_cart, name='remove-single-from-cart'),
    path('remove-from-cart/<item_id>/', views.remove_from_cart, name='remove-from-cart'),

    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/', views.PaymentView.as_view(), name='payment'),
]
