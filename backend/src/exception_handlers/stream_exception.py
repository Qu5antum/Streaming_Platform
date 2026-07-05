from .base_exception import BaseAppException


class StreamIsLiveExceptoin(BaseAppException):
    """Ошибка если у пользователя есть запущенный стрим"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class StreamNotFoundException(BaseAppException):
    """Ошибка если стрим не найден"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class StreamIsEndedException(BaseAppException):
    """Ошибка если стрим окончен"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)