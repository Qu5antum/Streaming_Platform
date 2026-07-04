from fastapi import APIRouter, Depends
from uuid import UUID

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.services.stream_service import StreamService
from src.api.schemas.stream_schema import StreamOut, StreamCreate
from src.api.dependencies.require_role_dependency import require_roles


stream_route = APIRouter(
    prefix="/api",
    tags=["Stream"]
)


async def get_stream_service(session: AsyncSession = Depends(get_session)):
    return StreamService(session=session)
    

@stream_route.post("/stream/create", response_model=StreamOut, status_code=201)
async def create_stream(
    stream: StreamCreate,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    stream_service: StreamService = Depends(get_stream_service)
):
    return await stream_service.create_stream(user=user, stream=stream)


@stream_route.get("/category/{category_id}/stream", status_code=200)
async def get_stream_by_category(
    category_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    stream_service: StreamService = Depends(get_stream_service)
):
    return await stream_service.find_stream_by_category(category_id=category_id)