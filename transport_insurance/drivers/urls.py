from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [

  path('', views.drivers_list, name='drivers_list'), 
  path('bio/', views.driver_detail, name='driver_detail'),
  path('request/', views.request_detail, name='request_detail'),
#   path('/<int:product_id>/', views.bug_detail, name='product_detail')

]


