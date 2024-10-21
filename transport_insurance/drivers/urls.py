from django.urls import path
from .views import *

# app_name = 'drivers'

urlpatterns = [
    path('drivers/',DriversAPIView.as_view(), name='drivers-list'),
    # Получение, обновление и удаление конкретной услуги
    path('drivers/<int:id_driver>/', DriversAPIView.as_view(), name='driver-detail'),
    path('drivers/<int:id_driver>/add-image/', DriversAPIView.as_view(), name='driver-add-image'),
    path('drivers/<int:id_driver>/add-to-draft/', DriversAPIView.as_view(), name='driver-add-to-draft')
  # path('', views.drivers_list, name='drivers_list'), 
  # path('driver/<int:id_driver>/', views.driver_detail, name='driver_detail'),
  # path('insurance/<int:id_insurance>/', views.insurance_detail, name='insurance_detail'),
  # path( 'driver/add_driver/<int:id_driver>', views.add_driver_to_insurance, name='add_driver_to_insurance'),
  # path( 'insurance/update_insurance_status/<int:id_insurance>', views.update_insurance_status, name='update_insurance_status'),
]


