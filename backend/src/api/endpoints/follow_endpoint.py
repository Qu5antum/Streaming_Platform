from fastapi import APIRouter, Depends
from uuid import UUID

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.api.dependencies.require_role_dependency import require_roles
from src.services.follower_service import FollowerService
from src.api.schemas.follow_schema import FollowResponse


follow_route = APIRouter(
    prefix="/api",
    tags=["Follower"]
)

async def get_follow_service(session: AsyncSession = Depends(get_session)):
    return FollowerService(session=session)


@follow_route.post("/user/{user_id}/follow", response_model=FollowResponse, status_code=201)
async def follow_streamer(
    user_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    follow_service: FollowerService = Depends(get_follow_service)
):
    return await follow_service.follow_user(streamer_id=user_id, user=user)


@follow_route.delete("/user/{user_id}/unfollow", status_code=200)
async def unfollow_streamer(
    user_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    follow_service: FollowerService = Depends(get_follow_service)
):
    return await follow_service.unfollow_user(streamer_id=user_id, user=user)


@follow_route.get("/user/followers", response_model=list[FollowResponse], status_code=200)
async def get_my_followers(
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    follow_service: FollowerService = Depends(get_follow_service)
):
    return await follow_service.get_my_followers(user=user)


@follow_route.get("/user/{user_id}/followers_amount", status_code=200)
async def get_followers_amount(
    streamer_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    follow_service: FollowerService = Depends(get_follow_service)
):
    return await follow_service.get_followers_amount(streamer_id=streamer_id)