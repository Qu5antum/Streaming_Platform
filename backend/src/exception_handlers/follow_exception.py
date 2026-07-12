from .base_exception import BaseAppException


class FollowNotFoundException(BaseAppException):
    """If follow id not founded"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)
