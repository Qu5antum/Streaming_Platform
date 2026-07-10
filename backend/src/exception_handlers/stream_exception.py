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


class StreamIsOfflineException(BaseAppException):
    """Ошибка если стрим офлайн"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class StreamNotBelongToUser(BaseAppException):
    """Ошибка если стрим не принадлежит ползователю"""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)


class InvalidStreamStateException(BaseAppException):
    """Ошибка если статус стрима неверный"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class StreamMetricNotFoundException(BaseAppException):
    """Ошибка если метрикик стрима не найдены"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)