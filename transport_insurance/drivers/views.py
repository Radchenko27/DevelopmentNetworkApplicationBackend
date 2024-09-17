from django.shortcuts import render,  get_object_or_404

# Create your views here.
drivers = [
    {
        'id': 1,
        'name': 'Радченко Дмитрий Сергеевич',
        'experience': '1 год',
        'certificate_number': '32 12 344234',
        'license': 'B, M',
        'image': 'http://127.0.0.1:9000/drivers/1.png',
        'characteristics': 'Дмитрий Сергеевич – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
    {
        'id': 2,
        'name': 'Самошников Василий Александрович',
        'experience': '6 лет',
        'certificate_number': '67 34 456377',
        'license': 'B, C, M',
        'image': 'http://127.0.0.1:9000/drivers/2.png',
        'characteristics': 'Василий Александрович – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
    {
        'id': 3,
        'name': 'Кириенко Никита Степанович',
        'experience': '9 лет',
        'certificate_number': '27 76  567887',
        'license': 'A, B, C, M',
        'image': 'http://127.0.0.1:9000/drivers/3.jpg',
        'characteristics': 'Никита Степанович – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
    {
        'id': 4,
        'name': 'Петров Сергей Олегович',
        'experience': '7 год',
        'certificate_number': '67 32 356345',
        'license': 'B, C, D, M',
        'image': 'http://127.0.0.1:9000/drivers/4.jpg',
        'characteristics': 'Сергей Олегович – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
    {
        'id': 5,
        'name': 'Размаринов Владимир Сергеевич',
        'experience': '15 лет',
        'certificate_number': '98 78 305678',
        'license': 'B, M',
        'image': 'http://127.0.0.1:9000/drivers/5.jpg',
        'characteristics': 'Владимир Сергеевич – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
    {
        'id': 6,
        'name': 'Козлов Андрей Сергеевич',
        'experience': '10 лет',
        'certificate_number': '33 78 567898',
        'license': 'A, B, C, D, M',
        'image': 'http://127.0.0.1:9000/drivers/6.jpg',
        'characteristics': 'Андрей Сергеевич – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
    {
        'id': 1,
        'name': 'Радченко Дмитрий Сергеевич',
        'experience': '1 год',
        'certificate_number': '32 12 344234',
        'license': 'B, M',
        'image': 'http://127.0.0.1:9000/drivers/1.png',
        'characteristics': 'Дмитрий Сергеевич – опытный водитель, работающий в различных областях автотранспортной индустрии.'
    },
]

requests =  {
        'id':1,
        'type': "ОСАГО",
         'certificate_number':1234,
         'certificate_series': 567890,
         'date_begin': '01.01.2024',
         'date_end': '01.01.2025',
         'car_brand':  'Toyota' ,
         'car_model': 'Camry',
         'car_number':'А001МР',
         'car_region': 77,


    }

request_to_drivers = {
    1: [1, 2, 3],
    # другие привязки
}


def drivers_list(request):
    # features = FeatureRequest.objects.all()
    drivers_list = drivers
    search = request.GET.get('search', "")
    if search:
        drivers_list = [driver for driver in drivers_list if search.lower() in driver['name'].lower()]
    
    id_request = 1
    quantity_of_drivers = len(request_to_drivers[id_request])
    return render(request, 'drivers/drivers_list.html', {
        'drivers_list': drivers_list,
        'quantity_of_drivers':quantity_of_drivers,
        'id_request': id_request,
    })




def driver_detail(request, id_driver):

    driver = next((dr for dr in drivers if dr['id'] == id_driver ), None)

    if not driver:
        return get_object_or_404(driver)
    # bug = get_object_or_404(BugReport, id=bug_id)
    return render(request, 'drivers/driver_detail.html', {'driver': driver})


def request_detail(request, id_request):
    # bug = get_object_or_404(BugReport, id=bug_id)
    # drivers_ids = request_to_drivers.get(id_request, [])

    drivers_list = drivers
    drivers_request = [driver for driver in drivers_list ]
    return render(request, 'drivers/request_detail.html', {
        'drivers_request': drivers_request,
        'requests': requests,
    })