from fastapi import APIRouter, Depends
from uuid import UUID

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.api.dependencies.require_role_dependency import require_roles
from src.services.category_service import CategoryService
from src.api.schemas.category_schema import CategoryCreate, CategoryOut
from src.redis.redis_service import RedisService


category_route = APIRouter(
    prefix='/api',
    tags=['Category']
)

redis_service = RedisService()


async def get_category_service(session: AsyncSession = Depends(get_session)):
    return CategoryService(session=session, redis_service=redis_service)


@category_route.post("/admin/category/create", response_model=CategoryOut, status_code=201)
async def category_create(
    category: CategoryCreate, 
    user: User = Depends(require_roles(UserRole.ADMIN)),
    category_service: CategoryService = Depends(get_category_service)
):
    return await category_service.create_category(category=category)


@category_route.get("/category/all", response_model=list[CategoryOut], status_code=200)
async def get_categories(
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    category_service: CategoryService = Depends(get_category_service)
):
    return await category_service.get_categories()


@category_route.delete("/admin/category/{category_id}/delete", status_code=200)
async def delete_category(
    category_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    category_service: CategoryService = Depends(get_category_service)
):
    return await category_service.delete_category(category_id=category_id)