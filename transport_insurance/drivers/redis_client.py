import redis
from django.conf import settings
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import get_user_model
from .client_errors import *


redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

class RedisClient():
    def __init__(self, request):
        self.request = request
        self.redis_client = redis_client
        self.session_id = self.request.COOKIES.get('sessionid')
        if not self.session_id:
            raise CustomAPIException(ErrorCodes.SESSION_ID_MISSING)
    
    
    def get_user_id_from_session(self):
        user_id = self.redis_client.get(self.session_id)
        if user_id is None:
            raise CustomAPIException(ErrorCodes.USER_ID_NOT_FOUND_BY_SESSION)
        return user_id.decode('utf-8') if isinstance(user_id, bytes) else user_id
    

    def is_user(self):
        user_id = self.get_user_id_from_session()
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CustomAPIException(ErrorCodes.USER_NOT_FOUND)
        return user
    
    def is_user_staff(self, flag=False):
        """Проверяет, является ли пользователь сотрудником (is_staff)."""
        user = self.get_user()
        if not user.is_staff and not user.is_superuser:
            if not flag:
                raise CustomAPIException(ErrorCodes.USER_NOT_PERMISSION) 
            else:
                return user, False
        return user, True if flag else user
    
    # def is_user_superuser(self):
    #     """Проверяет, является ли пользователь администратором (is_superuser)."""
    #     user = self.get_user()
    #     return user.is_superuser

    # def is_user_manager(self):
    #     """Проверяет, является ли пользователь менеджером (is_staff или is_superuser)."""
    #     user = self.get_user()
    #     return user.is_staff or user.is_superuser
    
    # Инициализация клиента
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Проверка подключения
# if __name__ == "main":
#     try:
#         redis_client.ping()
#         print("Подключение к Redis успешно!")
#     except redis.ConnectionError as e:
#         print(f"Ошибка подключения к Redis: {e}")

#     # Простой тест записи и чтения
#     test_key = "test_key"
#     redis_client.set(test_key, "Hello, Redis!")
#     value = redis_client.get(test_key)
#     # Получаем все ключи

#     # Получение всех ключей
#     keys = redis_client.keys('*')

#     # Вывод ключей и их значений (если требуется)
#     for key in keys:
#         print(f"Key: {key.decode('utf-8')}, Value: {redis_client.get(key).decode('utf-8')}")

#     print(f"Значение по ключу '{test_key}': {value.decode('utf-8') if value else None}")