from .base_exception import BaseAppException


class ValidationException(BaseAppException):
    """Вызывается при сбое проверки входных данных."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)