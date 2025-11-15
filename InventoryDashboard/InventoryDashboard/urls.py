"""
URL configuration for InventoryDashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from InventoryManagementWebApp.views import Endpoints as views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('select-operations/', views.select_operations, name='select_operations'),
    path('create-new-inventory-product/', views.create_new_inventory_product, name='create_new_inventory_product'),
    path('read-inventory-products/', views.read_inventory_products, name='read_inventory_products'),
    path('update-inventory-product-location/', views.update_inventory_product_location, name='update_inventory_product_location'),
    path('update-inventory-product-quantity-on-pallet/', views.update_inventory_product_quantity_on_pallet, name='update_inventory_product_quantity_on_pallet'),
    path('delete-inventory-product/', views.delete_inventory_product, name='delete_inventory_product'),
]
