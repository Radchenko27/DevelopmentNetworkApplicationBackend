from django.urls import path
from . import views

# app_name = 'drivers'

urlpatterns = [
  path('', views.drivers_list, name='drivers_list'), 
  path('driver/<int:id_driver>/', views.driver_detail, name='driver_detail'),
  path('insurance/<int:id_insurance>/', views.insurance_detail, name='insurance_detail'),
#   path('/<int:product_id>/', views.bug_detail, name='product_detail')
]


