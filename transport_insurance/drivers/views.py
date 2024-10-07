from django.shortcuts import render,  get_object_or_404, redirect
from .models import Driver, Insurance, Driver_Insurance
from django.db import models, connection
from django.contrib.auth.decorators import login_required
from django.http import Http404

# Create your views here



def drivers_list(request):
    # features = FeatureRequest.objects.all()
    # drivers_list = drivers
    
    driver_name = request.GET.get('driver_name', '')
    drivers_list = Driver.objects.filter(status='active')

    current_insurance = None

    if request.user.is_authenticated:
        
        current_insurance = Insurance.objects.filter(creator=request.user, status='draft').first()
         # Если черновика нет, создаем новый
        # if current_insurance is None:
        #     current_insurance = Insurance.objects.create(creator=request.user, status='draft')
        #     print("Создан новый черновик:", current_insurance.id)
        
    if driver_name:
         drivers_list = drivers_list.filter(name__icontains=driver_name)

    quantity_of_drivers = Driver_Insurance.objects.filter(insurance=current_insurance).aggregate(total_quantity=models.Count("id"))['total_quantity'] or 0 if current_insurance else 0
    
    return render(request, 'drivers/drivers_list.html', {
        'drivers_list': drivers_list,
        'quantity_of_drivers':quantity_of_drivers,
        'id_insurance': current_insurance.id if current_insurance else None,
    })



def driver_detail(request, id_driver):

    driver= get_object_or_404(Driver, id=id_driver)

    return render(request, 'drivers/driver_detail.html', {'driver': driver})



@login_required
def add_driver_to_insurance(request, id_driver):
    # Получаем услугу по её ID или возвращаем 404, если услуга не найдена
    driver = get_object_or_404(Driver, id=id_driver)

    # Получаем или создаем черновик заказа для текущего пользователя
    current_insurance, created_insurance = Insurance.objects.get_or_create(
        creator=request.user, 
        status='draft'
    )

    # Проверяем, есть ли услуга уже в текущем заказе
    current_driver_insurance, created_driver_insurance = Driver_Insurance.objects.get_or_create(
        insurance=current_insurance,
        driver=driver,
        owner=False,  # Инициализируем количество как 0, если услуги ещё нет
    )


    return redirect('drivers_list')


@login_required
def insurance_detail(request, id_insurance):
    
    selected_insurance = get_object_or_404(Insurance, id=id_insurance, creator=request.user)

    drivers_insurance = Driver_Insurance.objects.filter(insurance=selected_insurance)

    if selected_insurance.status == 'deleted' :# или insurance.status == 'deleted'
        raise Http404("Страховка недоступна")
    

    elif not drivers_insurance.exists():
        return render(request, 'drivers/insurance_detail.html', {
        'insurance':  selected_insurance,
        'queryset_drivers_in_insurance': None,
        'drivers_insurance':None,
        'is_empty_insurance': True,
        })
    
    queryset_drivers_in_insurance=[driver_insurance.driver for driver_insurance in drivers_insurance ]
    
    return render(request, 'drivers/insurance_detail.html', {
        'insurance':  selected_insurance,
        'queryset_drivers_in_insurance': queryset_drivers_in_insurance,
        'drivers_insurance': drivers_insurance,
        'is_empty_insurance': False,
    })


@login_required
def update_insurance_status(request, id_insurance):
    # Обрабатываем только POST-запросы
    if request.method == 'POST':
        action = request.POST.get('action')  # Получаем действие (например, завершить или удалить заказ)
        # Получаем заказ по ID и проверяем, что он принадлежит текущему пользователю
        current_insurance = get_object_or_404(Insurance, id=id_insurance, creator=request.user)

        # Открываем прямое соединение с базой данных для выполнения SQL-запросов
        with connection.cursor() as cursor:

            if action == 'delete':
                cursor.execute("""
                    UPDATE insurance
                    SET status = 'deleted'
                    WHERE id = %s
                """, [id_insurance])
                print(f"Заказ {current_insurance.id} удален.")

                # Здесь не создаем новый черновик, это будет сделано в add_service_to_order_datacenter

                # Перенаправляем на список услуг после удаления заказа
                return redirect('drivers_list')

    # Если запрос не является POST, возвращаем 404
    raise Http404("Недопустимый метод запроса")


        