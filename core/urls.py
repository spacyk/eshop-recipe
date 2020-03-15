from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('product/<slug>/', views.ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<item_id>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<item_id>/', views.remove_from_cart, name='remove-from-cart'),

    path('checkout/', views.OrderDetailView.as_view(), name='checkout'),

]
