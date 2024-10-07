from django.urls import path
from . import views

# app_name = 'drivers'

urlpatterns = [
  path('', views.drivers_list, name='drivers_list'), 
  path('driver/<int:id_driver>/', views.driver_detail, name='driver_detail'),
  path('insurance/<int:id_insurance>/', views.insurance_detail, name='insurance_detail'),
  path( 'driver/add_driver/<int:id_driver>', views.add_driver_to_insurance, name='add_driver_to_insurance'),
  path( 'insurance/update_insurance_status/<int:id_insurance>', views.update_insurance_status, name='update_insurance_status'),
]


