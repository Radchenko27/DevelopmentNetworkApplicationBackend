from django.urls import path
from .views import *

# app_name = 'drivers'

urlpatterns = [
    #Домен водители
    path('drivers/',DriversAPIView.as_view(), name='drivers-list'),
    path('drivers/<int:id_driver>/', DriversAPIView.as_view(), name='driver-detail'),
    path('drivers/<int:id_driver>/add-image/', DriversAPIView.as_view(), name='driver-add-image'),
    path('drivers/<int:id_driver>/add-to-draft/', DriversAPIView.as_view(), name='driver-add-to-draft'),
    
    #Домен страховки
    path('insurances/',insurances_list , name='insurances-list'),
    path('insurances/<int:id_insurance>/', insurance_detail, name='insurance-detail'),
    path('insurances/<int:id_insurance>/delete/', insurance_delete, name='insurance-delete'),
    path('insurances/<int:id_insurance>/update/', insurance_update, name='insurance-update'),
    path('insurances/<int:id_insurance>/submit/', insurance_submit, name='insurance-submit'),
    path('insurances/<int:id_insurance>/finalize/', insurance_finalize, name='insurance-finalize'),
    
    #Домен связь
    path('insurances/<int:id_insurance>/drivers/<int:id_driver>/delete/', delete_driver_from_insurance, name='delete-driver-from-insurance'),
    path('insurances/<int:id_insurance>/drivers/<int:id_driver>/update/', update_driver_owner_in_insurance, name='update_service_quantity_in_order'),

    #Домен пользователи
    path('users/register/', register_user, name='register-user'),
    path('users/login/', login_user, name='login-user'),
    path('users/logout/', logout_user, name='logout-user'),
    path('users/update/<int:pk>/', update_user, name='update-user'),

]
# path('', views.drivers_list, name='drivers_list'), 
  # path('driver/<int:id_driver>/', views.driver_detail, name='driver_detail'),
  # path('insurance/<int:id_insurance>/', views.insurance_detail, name='insurance_detail'),
  # path( 'driver/add_driver/<int:id_driver>', views.add_driver_to_insurance, name='add_driver_to_insurance'),
  # path( 'insurance/update_insurance_status/<int:id_insurance>', views.update_insurance_status, name='update_insurance_status'),

