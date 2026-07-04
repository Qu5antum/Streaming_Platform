from uuid import UUID
from sqlalchemy import select

from .base_repository import BaseRepository
from src.database.models import Category


class CategoryRepository(BaseRepository):
    model = Category

    async def get_categories_with_ids(self, category_ids: list[UUID]):
        result = await self.session.execute(
            select(self.model).where(self.model.id.in_(category_ids))
        )

        return result.scalars().all()