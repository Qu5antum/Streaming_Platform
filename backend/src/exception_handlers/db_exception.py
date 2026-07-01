from .base_exception import BaseAppException


class DatabaseException(BaseAppException):
    """Ошибка базы данных"""
    def __init__(self, message, status_code = 500):
        super().__init__(message, status_code)