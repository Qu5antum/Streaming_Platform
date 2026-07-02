import logging
from sqlalchemy.exc import IntegrityError

from src.database.db import AsyncSession
from src.repositories.category_repository import CategoryRepository
from src.api.schemas.category_schema import CategoryCreate, CategoryOut
from src.exception_handlers.db_exception import DatabaseException

logger = logging.getLogger("category")


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_repo = CategoryRepository(session=self.session)

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

        return new_category
    
    async def get_categories(self) -> list[CategoryOut]:
        categories = await self.category_repo.get_all()

        logger.info("Successful response category")

        return categories
