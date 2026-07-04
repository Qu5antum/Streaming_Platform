from .base_exception import BaseAppException


class SomeCategoryNotFound(BaseAppException):
    """Ошибка если какие то категорий отсутсвуют"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class CategoryNotFoundException(BaseAppException):
    """Ошибка если категория не найдена"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)