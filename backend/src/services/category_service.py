import logging
from sqlalchemy.exc import IntegrityError
import json

from src.database.db import AsyncSession
from src.repositories.category_repository import CategoryRepository
from src.api.schemas.category_schema import CategoryCreate, CategoryOut
from src.exception_handlers.db_exception import DatabaseException
from src.redis.redis_service import RedisService

logger = logging.getLogger("category")


def serialize_category(category) -> dict:
    if hasattr(CategoryOut, "model_validate"):
        return CategoryOut.model_validate(category).model_dump(mode="json")

    return CategoryOut.model_validate(category).model_dump()


class CategoryService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.category_repo = CategoryRepository(session=self.session)
        self.redis = redis_service  

    async def create_category(self, category: CategoryCreate) -> CategoryOut:
        try:
            new_category = await self.category_repo.create(
                title=category.title,
                description=category.description
            )

        except IntegrityError:
            logger.error(
                "Database insert error",
                exc_info=True,
                extra={"title": category.title}
            )
            raise DatabaseException("DB ERROR!")
        
        logger.info(
            "New Category Created",
            extra={"title": category.title}
        )

        return serialize_category(new_category)
    
    async def get_categories(self) -> list[CategoryOut]:
        cached_data = await self.redis.get("categories:all")

        if cached_data: 
            logger.info("Categories fedched from Redis cache")

            return [
                CategoryOut.model_validate(item)
                for item in json.loads(cached_data)
            ]
        
        categories = await self.category_repo.get_all()

        logger.info("Successful response category")

        serialized = [
            serialize_category(category)
            for category in categories
        ]

        await self.redis.set(
            "categories:all",
            json.dumps(serialized),
            expire_seconds=300
        )

        logger.info("Categories cached in Redis")

        return [
            CategoryOut.model_validate(category)
            for category in categories
        ]