from django.db import models
from django.core.validators import RegexValidator

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
                        verbose_name='Категории')
    experience = models.IntegerField(verbose_name='Опыт работы')
    status = models.CharField(
                        max_length=10, 
                        STATUS_CHOICES=STATUS_CHOICES, 
                        default='active',
                        verbose_name='Статус',
                    )
    image_url = models.ImageField(verbose_name='Аватар')
    characteristics = models.TextField(verbose_name='Характеристика')


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
        
