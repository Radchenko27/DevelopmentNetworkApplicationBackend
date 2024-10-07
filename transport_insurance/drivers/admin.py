from django.contrib import admin
from drivers.models import Driver, Insurance, Driver_Insurance
# Register your models here.
admin.site.register(Driver)  # Регистрация модели DatacenterService без кастомизации
admin.site.register(Insurance)  # Регистрация DatacenterOrder с кастомным админ-классом
admin.site.register(Driver_Insurance) 