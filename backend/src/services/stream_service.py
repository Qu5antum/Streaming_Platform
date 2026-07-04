import logging
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from src.database.db import AsyncSession
from src.database.models import User, Status
from src.repositories.stream_repository import StreamRepository
from src.repositories.user_repository import UserRepository
from src.repositories.category_repository import CategoryRepository
from src.api.schemas.stream_schema import StreamCreate, StreamOut
from src.exception_handlers.stream_exception import StreamIsLiveExceptoin
from src.exception_handlers.category_exception import SomeCategoryNotFound, CategoryNotFoundException
from src.exception_handlers.db_exception import DatabaseException
from src.utils.secret_key import generate_stream_key

logger = logging.getLogger("category")


class StreamService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stream_repo = StreamRepository(session=self.session)
        self.user_repo = UserRepository(session=self.session)
        self.category_repo = CategoryRepository(session=self.session)

    async def create_stream(self, user: User, stream: StreamCreate) -> StreamOut:
        user_stream = await self.user_repo.get_user_stream(user_id=user.id)

        if user_stream:
            logger.warning(
                "User already have live stream",
                extra={"user_id": str(user.id)}
            )

            raise StreamIsLiveExceptoin("You have live stream")

        categories = await self.category_repo.get_categories_with_ids(
            category_ids=stream.category_ids
        )

        if len(categories) != len(stream.category_ids):
            logger.warning("Some categories not found")

            raise SomeCategoryNotFound("Some categories not found")
        try:
            new_stream = await self.stream_repo.create(
                title = stream.title,
                description = stream.description,
                thumbnail_url = stream.thumbnail_url,
                stream_key = generate_stream_key(),
                status = Status.OFFLINE,
                streamer_id = user.id,
                categories = categories
            )

            await self.session.commit()
            await self.session.refresh(new_stream)
        except IntegrityError:
            await self.session.rollback()

            logger.error(
                "Stream not created, Database Error!",
                exc_info=True,
                extra={"stream_title": stream.title}
            )

            raise DatabaseException("Database Error!")
        
        logger.info(
            "New Stream created",
            extra={"stream_id": str(new_stream.id)}
        )
        
        return new_stream
    
    # TODO Implement redis service
    async def find_stream_by_category(self, category_id: UUID):
        category = await self.category_repo.get(id=category_id)

        if not category:
            logger.warning(
                "Category not found",
                extra={"category_id": category_id}
            )

            raise CategoryNotFoundException("Category not found")

        streams = await self.stream_repo.get_stream_with_category_id(category_id=category_id)

        logger.info("Successful response")

        return streams

        


