from django.shortcuts import render,  get_object_or_404, redirect
# from .models import Driver, Insurance, Driver_Insurance
from .models import *
from .serializers import DriverInsuranceSerializers, DriverSerializer, InsuranceSerializer
from django.db import models, connection
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required
from django.http import Http404
from rest_framework import  status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .minio import add_pic 
from minio import Minio
from django.conf import settings

SINGLITON_USER = User(id=1, username='admin')


class DriversAPIView(APIView):

    permission_classes = []
    model_class = Driver
    serializer_class = DriverSerializer


    def get_drivers(self):
        return self.model_class.objects.exclude(status='удалена')
    

    def get(self, request, id_driver=None):
            if id_driver:
                return self.get_driver_detail(request, id_driver)
            else:
                return self.get_drivers_list(request)


    def get_driver_detail(self, request, id_driver):
            # Получаем конкретного водителя по ID
            driver = get_object_or_404(self.get_drivers(), id=id_driver)
            driver_data = self.serializer_class(driver).data
            return Response(driver_data, status=status.HTTP_200_OK,)
    

    def get_drivers_list(self, request):
        
        driver_name = request.GET.get('driver_name', '')
        drivers_list = self.get_drivers()

        if driver_name:
            drivers_list = self.get_drivers().filter(name__icontains=driver_name)

        current_insurance = Insurance.objects.filter(creator=SINGLITON_USER, status='draft').first()

        if current_insurance:
            quantity_of_drivers = Driver_Insurance.objects.filter(insurance=current_insurance).aggregate(total_quantity=models.Count("id"))['total_quantity'] or 0 if current_insurance else 0
            current_insurance_id = current_insurance.id

        else:
            quantity_of_drivers = 0
            current_insurance_id = None

        drivers = self.serializer_class(drivers_list, many=True).data
        response_data = {
             'drivers': drivers,
             'quantity_of_drivers': quantity_of_drivers ,
             'current_insurance_id': current_insurance_id,
        }
        return Response(response_data,  status=status.HTTP_200_OK,)   


    def put(self, request, id_driver):
        # partial = request.method == 'PATCH'
        # print(request.data)
        driver = get_object_or_404(self.get_drivers() , id=id_driver)
        # print(driver)
        driver_serializer = self.serializer_class(driver, data=request.data, partial=True)
        # print(driver_serializer)
        if driver_serializer.is_valid(raise_exception=True):
            driver_serializer.save()
            return Response(driver_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(driver_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, id_driver):
        driver = get_object_or_404(self.get_drivers() , id=id_driver)

        if driver.status == 'deleted':
             return Response({'error': 'Эта услуга уже была удалена.'}, status=status.HTTP_400_BAD_REQUEST)

        if driver.image_url:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            try:
                client.remove_object('drivers', f"{driver.id}.png")
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        driver.status = 'deleted'
        driver.save()
        return Response({'message': 'Услуга успешно удалена'}, status=status.HTTP_200_OK)


    def post(self, request, id_driver=None): 
         
         if request.path.endswith('/add-image/'):  
            return self.post_add_image(request, id_driver)
         
         elif request.path.endswith('/add-to-draft/'):
            return self.post_add_to_draft(request, id_driver)
         
         else:
            return self.post_add_driver(request)
         
    
    def post_add_driver(self, request):
        # Логика для создания нового водителя 
        driver_serializer = self.serializer_class(data=request.data)
        if driver_serializer.is_valid():
            new_driver = driver_serializer.save()
            # Сериализуем и возвращаем данные нового водителя
            response_data = self.serializer_class(new_driver).data  # Сериализуем новую услугу
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(driver_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    
    def post_add_image(self, request, id_driver):
        driver = get_object_or_404(self.get_drivers(), id=id_driver)

        if driver.status == 'deleted':
            return Response({'error': 'Нельзя добавлять изображение к удаленному водителю.'}, status=status.HTTP_400_BAD_REQUEST)

        if 'image' not in request.FILES:
            return Response({'error': 'Изображение не предоставлено'}, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES['image']
        result = add_pic(driver, image)

        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        driver.image_url = result['image_url']
        driver.save()

        driver_serializer = self.serializer_class(driver).data

        return Response({
            'message': 'Изображение успешно добавлено или обновлено',
            'driver': driver_serializer
        }, status=status.HTTP_200_OK)
    

    def post_add_to_draft(self, request, id_driver):
        
        driver = get_object_or_404(self.get_drivers(), id=id_driver)
        current_insurance, created = Insurance.objects.get_or_create(creator=SINGLITON_USER, status='draft')
            # driver_in_insurance, created_driver_in_insurance = Driver_Insurance.object.get_or_create(driver=driver, ) 
        if not Driver_Insurance.objects.filter(driver=driver, insurance=current_insurance).exists():
            created_driver_insurance = Driver_Insurance.objects.create(
                insurance=current_insurance,
                driver=driver,
                owner=False, 
                )            
        else:
            return Response({'error': 'Водитель уже добавлен в данную страховку'}, status=status.HTTP_400_BAD_REQUEST)
        
        current_insurance.save()
        created_driver_insurance.save()

        insurance_serializer = InsuranceSerializer(current_insurance).data

        return Response(
                {
                    'message':'Водитель добавлен в черновик страховки',
                    'current_insurance': insurance_serializer,
                },
                status=status.HTTP_201_CREATED
            )





            



































# def drivers_list(request):
    
#     driver_name = request.GET.get('driver_name', '')
#     drivers_list = Driver.objects.filter(status='active')

#     current_insurance = None

#     if request.user.is_authenticated:
#         current_insurance = Insurance.objects.filter(creator=request.user, status='draft').first()
        
#     if driver_name:
#          drivers_list = drivers_list.filter(name__icontains=driver_name)

#     quantity_of_drivers = Driver_Insurance.objects.filter(insurance=current_insurance).aggregate(total_quantity=models.Count("id"))['total_quantity'] or 0 if current_insurance else 0
    
#     return render(request, 'drivers/drivers_list.html', {
#         'drivers_list': drivers_list,
#         'quantity_of_drivers':quantity_of_drivers,
#         'id_insurance': current_insurance.id if current_insurance else None,
#     })



# def driver_detail(request, id_driver):

#     driver= get_object_or_404(Driver, id=id_driver)

#     return render(request, 'drivers/driver_detail.html', {'driver': driver})



# @login_required
# def add_driver_to_insurance(request, id_driver):
#     # Получаем услугу по её ID или возвращаем 404, если услуга не найдена
#     driver = get_object_or_404(Driver, id=id_driver)

#     # Получаем или создаем черновик заказа для текущего пользователя
#     current_insurance, created_insurance = Insurance.objects.get_or_create(
#         creator=request.user, 
#         status='draft'
#     )

#     # Проверяем, есть ли услуга уже в текущем заказе
#     current_driver_insurance, created_driver_insurance = Driver_Insurance.objects.get_or_create(
#         insurance=current_insurance,
#         driver=driver,
#         owner=False,  # Инициализируем количество как 0, если услуги ещё нет
#     )

#     return redirect('drivers_list')


# @login_required
# def insurance_detail(request, id_insurance):
    
#     selected_insurance = get_object_or_404(Insurance, id=id_insurance, creator=request.user)

#     drivers_insurance = Driver_Insurance.objects.filter(insurance=selected_insurance)

#     if selected_insurance.status == 'deleted' :# или insurance.status == 'deleted'
#         raise Http404("Страховка недоступна")
    

#     elif not drivers_insurance.exists():
#         return render(request, 'drivers/insurance_detail.html', {
#         'insurance':  selected_insurance,
#         'queryset_drivers_in_insurance': None,
#         'drivers_insurance':None,
#         'is_empty_insurance': True,
#         })
    
#     queryset_drivers_in_insurance=[driver_insurance.driver for driver_insurance in drivers_insurance ]
    
#     return render(request, 'drivers/insurance_detail.html', {
#         'insurance':  selected_insurance,
#         'queryset_drivers_in_insurance': queryset_drivers_in_insurance,
#         'drivers_insurance': drivers_insurance,
#         'is_empty_insurance': False,
#     })


# @login_required
# def update_insurance_status(request, id_insurance):
#     # Обрабатываем только POST-запросы
#     if request.method == 'POST':
#         action = request.POST.get('action')  # Получаем действие (например, завершить или удалить заказ)
#         # Получаем заказ по ID и проверяем, что он принадлежит текущему пользователю
#         current_insurance = get_object_or_404(Insurance, id=id_insurance, creator=request.user)

#         # Открываем прямое соединение с базой данных для выполнения SQL-запросов
#         with connection.cursor() as cursor:

#             if action == 'delete':
#                 cursor.execute("""
#                     UPDATE insurance
#                     SET status = 'deleted'
#                     WHERE id = %s
#                 """, [id_insurance])
#                 print(f"Заказ {current_insurance.id} удален.")

                

#                 # Перенаправляем на список услуг после удаления заказа
#                 return redirect('drivers_list')

#     # Если запрос не является POST, возвращаем 404
#     raise Http404("Недопустимый метод запроса")


        