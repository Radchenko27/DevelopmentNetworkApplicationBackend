from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.models import User
# Create your models here.

class Driver(models.Model):

    STATUS_CHOICES = [
        ('active', 'активный'),
        ('deleted', 'удален'),
    ]
    
    
    name = models.CharField(max_length=255, verbose_name= "ФИО")
    certificate_number = models.CharField(
                            max_length=12, 
                            validators=[RegexValidator(
                                    regex=r'^\d{2} \d{2} \d{6}$',
                                    message="Серия и номер водительского удостоверения вводится в формате '00 00 000000'"
                        )],
                            unique=True,
                            verbose_name='Серия и номер водительского удостоверения'
                    )
    license = models.CharField(
                            max_length=30, 
                            validators=[RegexValidator(
                                    regex=r'^(?!.*(.).*\1)([ABCDE](, [ABCDE]){0,4})$',
                                    message="Строка с категориями прав должна вводится в формате 'A, B, C'"
                         )],
                            verbose_name='Категории'
                    )
    experience = models.IntegerField(verbose_name='Опыт работы')
    image_url = models.URLField(verbose_name='Аватар')
    characteristics = models.TextField(verbose_name='Характеристика')
    status = models.CharField(max_length=10,  choices=STATUS_CHOICES, default='active',verbose_name='Статус')

    class Meta:
        db_table = 'driver'
        verbose_name = 'Водитель'
        verbose_name_plural = 'Водители'
    
    
    @property
    def experience_text(self):
        last_number = self.experience % 10
        last_two_number = self.experience % 100
        
        if 11 <= last_two_number <= 19:
            return f"{self.experience} лет"
    # Проверка на последнюю цифру
        elif last_number == 1:
            return f"{self.experience} год"
        elif 2 <= last_number <= 4:
            return f"{self.experience} года"
        else:
            return f"{self.experience} лет"






class Insurance(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('deleted', 'Удален'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершен'),
        ('rejected', 'Отклонен'),
    ]


    TYPE_CHOICES = [
        ('ОСАГО', 'ОСАГО'),
        ('КАСКО', 'КАСКО'),
    ]

    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='ОСАГО' , verbose_name='Тип')
    certificate_number = models.CharField(
                                max_length=4,
                                validators=[RegexValidator(
                                        regex=r'^\d{4}$',
                                        message="Серия страховки вводится в формате '0000'"
                        )],
                                 verbose_name='Серия',
                    )
    certificate_series = models.CharField(
                                max_length=6,
                                validators=[RegexValidator(
                                        regex=r'^\d{6}$',
                                        message="Номер страховки вводится в формате '000000'",
                        )],
                                verbose_name='Номер',
                    )
    date_creation = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    date_begin = models.DateTimeField(null=True, blank=True, verbose_name='Дата начала действия')
    date_end = models.DateTimeField(null=True, blank=True, verbose_name='Дата конца действия')
    car_brand = models.CharField(max_length=50, verbose_name='Марка')
    car_model = models.CharField(max_length=50, verbose_name='Модель')
    car_number = models.CharField(
                                max_length=6,
                                validators=[RegexValidator(
                                    regex=r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}$',
                                    message="Номер машины вводится в формате 'А000АА'",
                        )],
                                verbose_name='Номер машины',
                    )
    car_region = models.CharField(
                                max_length=3, 
                                validators=[RegexValidator(
                                    regex=r'^\d{2,3}$',
                                    message="Регион номера машины вводится в формате '000' или '00'",
                        )],
                                  
                                verbose_name='Регион'
                    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    # Связь с пользователем, который создал заказ (удаление пользователя приведет к удалению всех его заказов)
    creator = models.ForeignKey(User, related_name='insurance_created', on_delete=models.CASCADE)
    # Связь с пользователем-модератором, который может редактировать или завершать заказ (при удалении модератора связь будет установлена в NULL)
    moderator = models.ForeignKey(User, related_name='insurance_moderated', on_delete=models.SET_NULL, null=True, blank=True)


    class Meta:
        db_table = 'insurance'
        verbose_name = 'Страховка'
        verbose_name_plural = 'Страховки'

    def __str__(self):
        return f"Страховка {self.id} от {self.creator.username}"
    
    
class Drver_Insurance(models.Model):

    driver = models.ForeignKey(Driver,  on_delete=models.CASCADE)
    insurance = models.ForeignKey(Insurance, on_delete=models.CASCADE)
    owner = models.BooleanField(default=False)


    class Meta:
        db_table = 'driver_insurance'
        # Составной уникальный ключ, гарантирующий, что одна услуга не может быть добавлена более одного раза к одному заказу
        unique_together = ('driver', 'insurance')

    def __str__(self):
        return f"Страховка {self.insurance.id} - Водитель {self.driver.name}"