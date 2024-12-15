from django.shortcuts import render,  get_object_or_404, redirect
from .models import *
from .serializers import DriverInsuranceSerializers, DriverSerializer, InsuranceSerializer, CustomUserSerializer
from django.db import models, connection
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required
# from django.http import Http404
from .singleton import get_mock_user, get_mock_user_moderator
from rest_framework import  status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView
from .minio import add_pic 
from minio import Minio
from django.conf import settings
import re
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
from .permissions import *
from .redis_client import *
import uuid
from django.http import JsonResponse


# SINGLITON_USER = User(id=1, username='admin')
# SINGLETON_MANAGER = User(id=2, username="manager")
redis_client_connection = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

# def get_current_user():
#     """Получаем текущего пользователя (мокового пользователя)"""
#     mock_user = get_mock_user()

#     if not isinstance(mock_user, get_user_model):
#         raise ValueError("Неверный пользователь")
#     return mock_user


# def get_current_user_moderator():
#     mock_user_moderator = get_mock_user_moderator()
#     if not isinstance( mock_user_moderator, get_user_model):
#         raise ValueError("Неверный пользователь")
#     return mock_user_moderator

@swagger_auto_schema(
                method='get',
                manual_parameters=[
                    openapi.Parameter(
                        'driver_name',
                        openapi.IN_QUERY,
                        description="ФИО водителя",
                        type=openapi.TYPE_STRING,
                        required=False,
                    ),
                ],
                responses={
                    200: DriverSerializer(many=True),
                    400: openapi.Response(
                        description="Ошибка в параметрах запроса",
                        schema=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'error': openapi.Schema(type=openapi.TYPE_STRING, description="Описание ошибки")
                            }
                        )
                    )
                },
                operation_summary="Получить список водителей",
                operation_description="Возвращает список водителей с поиском по ФИО."
    )
@api_view(['GET'])
@permission_classes([AllowAny])
def drivers_list(request):
    # try:
    #     mock_user = get_current_user()  # Используем внешнюю функцию
    # except ValueError as e:
    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = request.COOKIES.get('session_id')
    quantity_of_drivers = 0
    current_insurance_id = None
    
    if session_id:
        user_id = redis_client.get(session_id)

        if user_id:
            # Удаляем вызов decode, так как user_id уже является строкой
            user_id = user_id 
            current_insurance = Insurance.objects.filter(creator_id=user_id, status='draft').first()
            if current_insurance:
                quantity_of_drivers = Driver_Insurance.objects.filter(insurance=current_insurance).aggregate(total_quantity=models.Count("id"))['total_quantity'] or 0 if current_insurance else 0
                current_insurance_id = current_insurance.id

    drivers_list = Driver.objects.exclude(status='deleted')
    driver_name = request.GET.get('driver_name', '')

    if driver_name:
        drivers_list = drivers_list.filter(name__icontains=driver_name)
    
    drivers = DriverSerializer(drivers_list, many=True).data
    response_data = {
            'drivers': drivers,
            'quantity_of_drivers': quantity_of_drivers ,
            'current_insurance_id': current_insurance_id,
    }
    return Response(response_data,  status=status.HTTP_200_OK)   




@swagger_auto_schema(
    method='get',
    responses={200: DriverSerializer},
    operation_summary="Получить водителя",
    operation_description="Получает все данные о водителе по id."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def driver_detail(request, id_driver):
        # Получаем конкретного водителя по ID
    driver = get_object_or_404(Driver.objects.exclude(status='deleted'), id=id_driver)
    driver_data = DriverSerializer(driver).data
    return Response(driver_data, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='put',
    request_body=DriverSerializer,
    responses={200: DriverSerializer, 404: "Водитель не найден.", 400: "Ошибка в запросе. Обновление невозможно."},
    operation_summary="Обновить водителя",
    operation_description="Обновляет данные о водителе по id."
)
@api_view(['PUT'])
def driver_update(request, id_driver):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user_staff()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    
    driver = get_object_or_404(Driver.objects.exclude(status='deleted'), id=id_driver)
    driver_serializer = DriverSerializer(driver, data=request.data, partial=True)
    
    if driver_serializer.is_valid(raise_exception=True):
        driver_serializer.save()
        return Response(driver_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(driver_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(
    method='delete',
    responses={204: "Водитель удалён", 404: "Водитель не найден", 400: "Ошибка в запросе. Невозможно удалить"},
    operation_summary="Удалить водителя",
    operation_description="Помечает водителя как удалённый."
)
@api_view(['DELETE']) 
def driver_delete(request, id_driver):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user_staff()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    
    driver = get_object_or_404(Driver, id=id_driver)

    if driver.status == 'deleted':
            return Response({'error': 'Этот водитель уже был удален.'}, status=status.HTTP_400_BAD_REQUEST)

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
    return Response({'message': 'Водитель успешно удален'}, status=status.HTTP_204_NO_CONTENT)



@swagger_auto_schema(
    method='post',
    request_body=DriverSerializer,
    responses={201: DriverSerializer,  400: "Ошибка в запросе. Невозможно добавить водителя"},
    operation_summary="Добавить водителя",
    operation_description="Добавляет активного водителя."
)
@api_view(['POST'])    
def driver_add(request):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user_staff()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    # Логика для создания нового водителя 
    driver_serializer = DriverSerializer(data=request.data)
    if driver_serializer.is_valid():
        new_driver = driver_serializer.save()
        # Сериализуем и возвращаем данные нового водителя
        response_data = DriverSerializer(new_driver).data  # Сериализуем новую услугу
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        return Response(driver_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'image': openapi.Schema(type=openapi.TYPE_FILE, description='Изображение для добавления')
        }
    ),
    responses={200: DriverSerializer, 400: "Ошибка в запросе. Невозможно добавить картинку водителю.", 404: "Водитель не найден."},
    operation_summary="Добавить аватар водителю",
    operation_description="Добавляет аватар активному водителю."
)
@api_view(['POST'])
def driver_add_image(request, id_driver):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user_staff()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    driver = get_object_or_404(Driver.objects.exclude(status='deleted'), id=id_driver)

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

    driver_serializer = DriverSerializer(driver).data

    return Response({
        'message': 'Изображение успешно добавлено или обновлено',
        'driver': driver_serializer
    }, status=status.HTTP_200_OK)
    


@swagger_auto_schema(
    method='post',
    # request_body=DriverSerializer,
    responses={200: InsuranceSerializer, 400: "Ошибка в запросе. Невозможно добавить водителя.", 404: "Водитель не найден."},
    operation_summary="Добавить водителя в страховку",
    operation_description="Добавляет активного водителя в страховку."
)
@api_view(['POST'])
def driver_add_to_draft(request, id_driver):
   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user, is_staff = redis_client.is_user_staff(flag=True)
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    else:
        if is_staff:
            return Response({'error': 'Администратор не имеет право добавлять водителя в страховку.'}, status=status.HTTP_403_FORBIDDEN)
   
    driver = get_object_or_404(Driver.objects.exclude(status='deleted'), id=id_driver)
    current_insurance, created = Insurance.objects.get_or_create(creator=user, status='draft')
   
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


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('insurance_status', openapi.IN_QUERY, description="Фильтр по статусу страховки", type=openapi.TYPE_STRING),
        openapi.Parameter('start_date', openapi.IN_QUERY, description="Начальная дата", type=openapi.TYPE_STRING),
        openapi.Parameter('end_date', openapi.IN_QUERY, description="Конечная дата", type=openapi.TYPE_STRING)
    ],
    responses={200: InsuranceSerializer(many=True), 400: "Ошибка в запросе"},
    operation_summary="Получить список страховок",
    operation_description="Возвращает список страховок с фильтрацией по статусу и дате создания."
)
@api_view(['GET'])
def insurances_list(request):

    insurances = Insurance.objects.exclude(status__in=['draft', 'deleted'])
    
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user, is_staff = redis_client.is_user_staff(flag=True)
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    else:
        if not is_staff:
            insurances = insurances.filter(creator_id=user.id)

    insurance_status = request.GET.get('insurance_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if insurance_status:
        insurances = insurances.filter(status=insurance_status)
    
    if start_date and end_date:
        try:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')
            insurances =  insurances.filter(date_creation__range=[start_date, end_date])
        except ValueError:
            return Response({'error': 'Неверный формат даты. Используйте YYYY-MM-DD.'},status=status.HTTP_400_BAD_REQUEST)

    insurance_serializer = InsuranceSerializer(insurances, many=True, exclude_fields=['drivers']).data
    return Response({'insurances':insurance_serializer}, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='get',
    responses={200: InsuranceSerializer(), 404: "Страховка не найдена"},
    operation_summary="Получить страховку",
    operation_description="Возвращает информацию о конкретной страховке по её ID."
)
@api_view(['GET'])
def insurance_detail(request, id_insurance):
    user = None  
    is_staff = None 
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user, is_staff = redis_client.is_user_staff(flag=True)
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    

    insurance = get_object_or_404(Insurance, id=id_insurance)

    if insurance.status == 'deleted' :
        return Response({'error': 'Страховка не найдена'}, status=status.HTTP_404_NOT_FOUND)

    if not is_staff:
        if str(insurance.creator.id) != str(user.id):
            return Response({'error': 'У вас нет прав на просмотр этой страховки.'}, status=status.HTTP_403_FORBIDDEN)
    
    insurance_serializer = InsuranceSerializer(insurance).data
    return Response(insurance_serializer, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='delete',
    responses={204: "Страховка удалена", 404: "Страховка не найдена", 400: "Невозможно удалить страховку"},
    operation_summary="Удалить страховку",
    operation_description="Помечает страховку как удалённую."
)
@api_view(['DELETE'])
def insurance_delete(request, id_insurance):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user, is_staff = redis_client.is_user_staff(flag=True)
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    else:
        if is_staff:
            return Response({'error': 'Администратор не имеет право удалять страховку.'}, status=status.HTTP_403_FORBIDDEN)
    
    insurance = get_object_or_404(Insurance, id=id_insurance)

    if str(insurance.creator.id) != str(user.id):
        return Response({'error': 'У вас нет прав на удаление этой страховки.'}, status=status.HTTP_403_FORBIDDEN)
    if insurance.status == 'deleted':
        return Response({'error': 'Страховка уже удалена'}, status=status.HTTP_404_NOT_FOUND)
    
    insurance.status = 'deleted'
    insurance.date_formation = timezone.now()
    insurance.save()
    return Response({'message': 'Страховка успешна удалена'}, status=status.HTTP_204_NO_CONTENT)



@swagger_auto_schema(
    method='put',
    request_body=InsuranceSerializer,
    responses={
        200: "Страховка обновлена",
        404: "Страховка не найдена",
        400: "Ошибка обновления страховки"
    },
    operation_summary="Изменить страховку",
    operation_description="Обновляет данные страховки по его ID."
)
@api_view(['PUT'])
def insurance_update(request, id_insurance):

    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user, is_staff = redis_client.is_user_staff(flag=True)
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    else:
        if is_staff:
            return Response({'error': 'Администратор не имеет право формировать страховку.'}, status=status.HTTP_403_FORBIDDEN)
    
    insurance = get_object_or_404(Insurance, id=id_insurance)

    if str(insurance.creator.id) != str(user.id):
        return Response({'error': 'У вас нет прав на обновление этой страховки.'}, status=status.HTTP_403_FORBIDDEN)
    
    if insurance.status == 'deleted':
        return Response({'error': 'Обновление удалённых страховок невозможно.'}, status=status.HTTP_400_BAD_REQUEST)
   
    insurance_serializer = InsuranceSerializer(insurance, data=request.data, partial=True)

    if insurance_serializer.is_valid():
       insurance_serializer.save()
       return Response({'message': 'Страховка обновлёна успешно', 'insurance': insurance_serializer.data}, status=status.HTTP_200_OK)

    print(insurance_serializer.errors)  
    return Response(insurance_serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@swagger_auto_schema(
    method='put',
    responses={200: "Страховка подтверждена", 404: "Страховка не найдена", 400: "Ошибка подтверждения страховки"},
    operation_summary="Подтвердить страховку",
    operation_description="Подтверждает страховку по его ID."
)
@api_view(['PUT'])
def insurance_submit(request, id_insurance):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user, is_staff = redis_client.is_user_staff(flag=True)
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    else:
        if is_staff:
            return Response({'error': 'Администратор не имеет право формировать страховку.'}, status=status.HTTP_403_FORBIDDEN)
    
    insurance = get_object_or_404(Insurance, id=id_insurance)

    if str(insurance.creator.id) != str(user.id):
        return Response({'error': 'У вас нет прав на формирование этой страховки.'}, status=status.HTTP_403_FORBIDDEN)

    if insurance.status != 'draft':
        return Response({'error': 'Страховка не в статусе черновика. Проверьте статус.'}, status=status.HTTP_400_BAD_REQUEST)

    empty_fields = []
    fields = ['certificate_number', 'certificate_series', 'date_begin', 'date_end', 'car_model', 'car_region', 'type',]
    for field in fields:
        if not getattr(insurance, field, None):
            empty_fields.append(field)
    if empty_fields:
        empty_fields_str = ', '.join(empty_fields)
        return Response({'error': f'Не все поля страховки заполнены. Пустыми остались:{empty_fields_str}'}, status=status.HTTP_400_BAD_REQUEST)
    
    insurance.status = 'formed'
    insurance.date_formation = timezone.now()
    insurance.save()

    insurance_serializer = InsuranceSerializer(insurance).data
    return Response({'message': 'Страховка подтверждён успешно', 'insurance': insurance_serializer}, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, description="Действие: completed или rejected")
        },
        required=['action']
    ),
    responses={200: "Страховка завершена", 400: "Ошибка завершения", 403: "Нет пользовательских прав на завершении страховки"},
    operation_summary="Завершить или отклонить страховку",
    operation_description="Завершает или отклоняет страховку по его ID."
)
@api_view(['PUT']) #нужен модератор
def insurance_finalize(request, id_insurance):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user_staff()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    
    insurance = get_object_or_404(Insurance,id=id_insurance)

    if insurance.status == 'deleted':
        return Response({'error': 'Страховка удалена и не может быть завершена'}, status=status.HTTP_400_BAD_REQUEST)
    
    action = request.data.get('action')

    if not action or action not in ['completed', 'rejected']:
        return Response({'error': 'Некорректное действие. Параметр запроса пуст.'}, status=status.HTTP_400_BAD_REQUEST)

    if action == 'completed':
        insurance.status = 'completed'
        insurance.completion_date = timezone.now()
    elif action == 'rejected':
        insurance.status = 'rejected'
        insurance.completion_date = timezone.now()

    insurance.moderator = user[0]
    insurance.date_completion = timezone.now()
    insurance.save()
    insurance_serializer = InsuranceSerializer(insurance).data
    return Response({'message': f'Стаховка успешно {action}.','insurance':insurance_serializer}, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='delete',
    operation_summary="Удалить водителя из страховки",
    operation_description="Удаление водителя из страховки.",
    responses={
        204: 'Водитель удален из страховки.',
        400: 'Страховка удалена, нельзя удалить водителя.',
        404: 'Водитель не найден в страховке.',
    }
)
@api_view(['DELETE'])
def delete_driver_from_insurance(request, id_insurance, id_driver):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    
    insurance = get_object_or_404(Insurance, id=id_insurance)
            
    if insurance.status != 'draft':
        return Response({'error': 'Страховка не может быть изменена, так как она не в статусе draft.'}, status=status.HTTP_400_BAD_REQUEST)

    # Проверяем, является ли пользователь создателем страховка
    if str(insurance.creator.id) != str(user.id):
        return Response({'error': 'У вас нет прав на удаление водителей в этой страховке.'}, status=status.HTTP_403_FORBIDDEN)
    
    if insurance.status == 'deleted':
        return Response({'error': 'Страховка удалена, нельзя удалить водителя'}, status=status.HTTP_400_BAD_REQUEST)

    driver = get_object_or_404(Driver, id=id_driver)
    driver_to_insurance = Driver_Insurance.objects.filter(driver=driver, insurance=insurance).first()

    if driver_to_insurance:
        driver_to_insurance.delete()
        return Response({'message': 'Водитель удален из страховки'}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({'error': 'Водитель не найден в страховке'}, status=status.HTTP_404_NOT_FOUND)
    


@swagger_auto_schema(
    method='put',
    operation_summary="Изменить владельца страховки",
    operation_description="Изменение владельца страховки",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'owner': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Новый владелец')
        },
        required=['owner']
    ),
    responses={
        200: 'Владелец страховки успешно обновлён.',
        400: 'Ошибка в запросе.',
        404: 'Страховка или водитель не найдены.',
    }
)
@api_view(['PUT'])
def update_driver_owner_in_insurance(request, id_insurance, id_driver):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code)
    
    insurance = get_object_or_404(Insurance, id=id_insurance)

    if insurance.status != 'draft':
        return Response({'error': 'Страховка не может быть изменена, так как она не в статусе draft.'}, status=status.HTTP_400_BAD_REQUEST)
    # Проверяем, является ли пользователь создателем страховка
    if str(insurance.creator.id) != str(user.id):
        return Response({'error': 'У вас нет прав на изменение владельца страховки.'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_object_or_404(Driver, id=id_driver)
    driver_to_insurance = get_object_or_404(Driver_Insurance, driver=driver, insurance=insurance)
    
    if driver_to_insurance:
        data = request.data
        owner = bool(data.get('owner'))

        if owner:
            current_driver_to_insurance_owner = Driver_Insurance.objects.filter(owner=owner, insurance=insurance).first()
            if current_driver_to_insurance_owner:
                current_driver_to_insurance_owner.owner=False
                current_driver_to_insurance_owner.save()
                driver_to_insurance.owner = owner
                driver_to_insurance.save()
                return Response({'message': 'В страховке ранее был указан владелец. Была произведена замена.'}, status=status.HTTP_200_OK)
            
            driver_to_insurance.owner = owner
            driver_to_insurance.save()
            return Response({'message': 'Владелец в текущую страховку успешно добавлен.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Добавьте значение передаваемого параметра owner. Водитель по умолчанию уже не являелся владельцом.'}, status=status.HTTP_400_BAD_REQUEST)
        




logger = logging.getLogger(__name__)



@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email пользователя'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль пользователя'),
        },
        required=['email', 'password']
    ),
    responses={
        200: openapi.Response('Успешный вход',  schema=openapi.Schema(type=openapi.TYPE_OBJECT, 
                                                    properties={
                                                        'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='Идентификатор сессии пользователя, сохранённый в Redis'),
                                                    })), 
        401: 'Неверный email или пароль.'
    },
    operation_summary="Вход пользователя",
    operation_description="Аутентификация пользователя по email и паролю."
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Для входа без ограничений
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    logger.info(f"Попытка входа пользователя с email: {request.data.get('email')}")

    user = authenticate(request, email=email, password=password)
    
    if user is not None:
       
        login(request, user)

        session_id = str(uuid.uuid4())
        
        if session_id:  
            redis_client_connection.set(session_id, user.id, ex=3600)  # Сохраняем ID пользователя с TTL 1 час
            
            logger.info(f"Сессия сохранена в Redis для пользователя с email: {email}, session_id: {session_id}")

            # return Response({'session_id': session_id}, status=status.HTTP_200_OK).set_cookie("session_id", session_id, path="/", httponly=True, secure=True)
            response = Response({'session_id': session_id}, status=status.HTTP_200_OK)
            response.set_cookie("session_id", session_id, samesite="Lax")
            return response
        else:
            logger.error("Не удалось получить session_id.")
            return Response({'detail': 'Ошибка создания сессии.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.warning(f"Неверная попытка входа для email: {email}")
    return Response({'detail': 'Неверный email или пароль.'}, status=status.HTTP_401_UNAUTHORIZED)



@swagger_auto_schema(
    method='post',
    request_body=CustomUserSerializer,
    responses={
        201: openapi.Response('Пользователь успешно зарегистрирован', 
                              schema=openapi.Schema(type=openapi.TYPE_OBJECT, 
                                                    properties={
                                                        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email пользователя'),
                                                    })),
        400: 'Ошибка валидации данных'
    },
    operation_summary="Регистрация пользователя",
    operation_description="Создает нового пользователя с указанными данными."
)
@csrf_exempt
@api_view(['POST'])
def register_user(request):
    serializer = CustomUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({'message': 'Пользователь успешно зарегистрирован.', "email": user.email}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

@swagger_auto_schema(
    method='put',
    request_body=CustomUserSerializer,
    responses={
        200: 'Информация о пользователе успешно обновлена',
        404: 'Пользователь не найден.',
        400: 'Ошибка валидации данных'
    },
    operation_summary="Обновление информации о пользователе",
    operation_description="Частично обновляет данные пользователя."
)
@csrf_exempt
@api_view(['PUT'])
def update_user(request, id_user):
    user = None   
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code) 
    
    if str(user.id) != str(id_user):
        logger.warning("Пользователь пытается обновить данные о другом пользователя.")
        return Response({'detail': 'Вы можете обновить только свои собственные данные.'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CustomUserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Информация о пользователе успешно обновлена'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@swagger_auto_schema(
    method='post',
    responses={
        200: 'Успешный выход из системы',
        401: 'Отсутствует идентификатор сессии.'
    },
    operation_summary="Выход пользователя",
    operation_description="Разлогинивает пользователя."
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_user(request):
    try:
        redis_client = RedisClient(request)
        # Проверяем, является ли пользователь сотрудником и получаем объект пользователя
        user = redis_client.is_user()
    except CustomAPIException as e:
        return Response({"error": str(e)}, status=e.status_code) 
    
    redis_client_connection.delete(redis_client.session_id)
    logout(request)
    return Response({'message': 'Пользователь успешно вышел из системы'}, status=status.HTTP_200_OK)



# @csrf_exempt
# @api_view(['POST'])
# def login_user(request):
#     data = request.data
#     username = data.get('username')
#     password = data.get('password')

#     user = authenticate(request, username=username, password=password)
#     if user is not None:
#         login(request, user)
#         return Response({'message': 'Пользователь успешно вошел в систему'}, status=status.HTTP_200_OK)
#     return Response({'error': 'Неверное имя пользователя или пароль'}, status=status.HTTP_401_UNAUTHORIZED)


        