from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [

  path('', views.drivers_list, name='drivers_list'), 
#   path('/<int:product_id>/', views.bug_detail, name='product_detail')


]

