from .base_exception import BaseAppException


class UserNotFoundException(BaseAppException):
    """Ошибка если пользователь не найден"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class UnauthorizedException(BaseAppException):
    """Вызывается, когда пользователь не авторизован."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class UserAlreadyExists(BaseAppException):
    """Вызывается если пользователь уже есть"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)