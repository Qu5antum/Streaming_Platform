from fastapi import Depends

from .current_user import get_current_user
from src.database.models import User
from src.database.models import UserRole
from src.exception_handlers.access_exception import AccessException


def require_roles(*allowed_roles: UserRole):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise AccessException("Доступ запрещен.")
        return user

    return checker




            
            
            
