from fastapi import APIRouter, Depends
from uuid import UUID

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.api.schemas.user_schema import UserOut, UserUpdate
from src.services.user_service import UserService
from src.api.dependencies.require_role_dependency import require_roles


user_route = APIRouter(
    prefix="/api",
    tags=["User"]
)


async def get_user_service(session: AsyncSession = Depends(get_session)):
    return UserService(session=session)

@user_route.get("/user/profile/me", response_model=UserOut, status_code=200)
async def get_user_profile(
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_user_profile(user=user)


@user_route.get("/user/all", status_code=200)
async def get_all_users(
    user: User = Depends(require_roles(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_users()


@user_route.put("/user/profile/me/update", status_code=200)
async def profile_update(
    user_update: UserUpdate,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.update_profile(user=user, user_update=user_update)


@user_route.delete("/user/{user_id}/delete", status_code=200)
async def delete_user(
    user_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.delete_user(user_id=user_id)