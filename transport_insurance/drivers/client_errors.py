from enum import Enum
from rest_framework.exceptions import APIException
from rest_framework import status


class ErrorCodes(Enum):
    SESSION_ID_MISSING = (401, 'session_id не предоставлен.', status.HTTP_401_UNAUTHORIZED)
    USER_ID_NOT_FOUND_BY_SESSION = (401, 'Неверный sessionid или сессия истекла. Попробуйте заново авторизоваться.', status.HTTP_401_UNAUTHORIZED)
    USER_NOT_PERMISSION = (403,  'Доступ запрещен. Необходимы права администратора.', status.HTTP_403_FORBIDDEN)
    USER_NOT_FOUND = (404, 'Пользователь не найден.', status.HTTP_404_NOT_FOUND)
    def __init__(self, status_code, default_detail, default_code):
        self.status_code = status_code
        self.default_detail = default_detail
        self.default_code = default_code

class CustomAPIException(APIException):
    def __init__(self, error_code: ErrorCodes):
        self.status_code = error_code.status_code
        self.detail = error_code.default_detail
        self.default_code = error_code.default_code