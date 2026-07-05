from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, Any
from uuid import UUID

from .base_repository import BaseRepository
from src.database.models import User, Stream, Status, UserRole


class UserRepository(BaseRepository):
    model = User

    async def get_user_with_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(self.model).where(self.model.username == username)
        )

        return result.scalar_one_or_none()
    
    async def search_user_by_username(self, username: str, user: User) -> list[dict[Any, User]]:
        query = select(self.model).where(
            self.model.username.ilike(f'%{username}%'),
        )

        if user.role == UserRole.USER:
            query = query.where(self.model.role == UserRole.USER, self.model.is_active == True)
        
        result = await self.session.execute(query)

        return result.scalars().all()
    
    async def get_user_stream(self, user_id: UUID):
        result = await self.session.execute(
            select(self.model)
            .join(self.model.streams)
            .options(selectinload(self.model.streams))
            .where(
                self.model.id == user_id,
                Stream.status == Status.LIVE
            )
            .limit(1)
        )

        return result.scalar_one_or_none()