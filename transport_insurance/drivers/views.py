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
    
]

insurances = [
    {
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
        #  'items':[1, 2, 3],
        #  'owner': 1,
         'items': [
                        {
                            'id_driver':1,
                            'owner':1,
                        }, 
                        {
                            'id_driver':2,
                            'owner':0,
                        }, 
                        {
                            'id_driver':3,
                            'owner':0,
                        },
                ],
    }
]

# insurance_to_drivers = {
#     1: [1, 2, 3],
#     # другие привязки
# }


def drivers_list(request):
    # features = FeatureRequest.objects.all()
    drivers_list = drivers
    search = request.GET.get('driver_name', "")
    if search:
        drivers_list = [driver for driver in drivers_list if search.lower() in driver['name'].lower()]
    
    id_insurance = 1
    # quantity_of_drivers = len(insurance_to_drivers[id_insurance])
    quantity_of_drivers = next((len(insurance['items']) for insurance in insurances  if insurance['id'] == id_insurance and insurance.get('items', 0) ), 0)
    return render(request, 'drivers/drivers_list.html', {
        'drivers_list': drivers_list,
        'quantity_of_drivers':quantity_of_drivers,
        'id_insurance': id_insurance,
    })




def driver_detail(request, id_driver):

    driver = next((dr for dr in drivers if dr['id'] == id_driver ), None)
    if not driver:
        return get_object_or_404(driver)
    # bug = get_object_or_404(BugReport, id=bug_id)
    return render(request, 'drivers/driver_detail.html', {'driver': driver})


def insurance_detail(request, id_insurance):
   
    insurance= next((insurance for insurance in insurances if insurance['id'] == id_insurance), None)
    # ids_of_drivers = insurance.get('items', [])
    items_of_drivers = insurance.get('items', [])
    ids_of_drivers = [item['id_driver'] for item in items_of_drivers]
    insurance_drivers = [driver for driver in drivers if driver['id'] in ids_of_drivers]
    # insurance_drivers = [driver for driver in drivers if driver['id'] in ids_of_drivers]
    return render(request, 'drivers/insurance_detail.html', {
        'insurance_drivers': insurance_drivers,
        'insurance':  insurance,
        'items_of_drivers': items_of_drivers,
    })