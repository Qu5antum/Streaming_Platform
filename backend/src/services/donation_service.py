from uuid import UUID
import logging
from sqlalchemy.exc import IntegrityError

from src.database.db import AsyncSession
from src.database.models import User, Status
from src.repositories.donation_repository import DonationRepository
from src.repositories.stream_repository import StreamRepository
from .stream_metric_serivce import StreamMetricService
from src.api.schemas.donation_schema import DonationRequest, DonationResponse
from src.exception_handlers.stream_exception import StreamNotFoundException, InvalidStreamStateException, StreamNotBelongToUser
from src.exception_handlers.db_exception import DatabaseException

logger = logging.getLogger("donation")


class DonationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.donation_repo = DonationRepository(session=self.session)
        self.stream_repo = StreamRepository(session=self.session)
        self.stream_metric_serivce = StreamMetricService(session=self.session)

    async def donate_by_stream_id(self, stream_id: UUID, user: User, donation_request: DonationRequest) -> DonationResponse:
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": str(stream_id)}
            )

            raise StreamNotFoundException("Stream not found")
        
        if stream.status == Status.OFFLINE or stream.status == Status.ENDED:
            logger.warning(
                "Stream is not live",
                extra={"stream_id": stream_id}
            )

            raise InvalidStreamStateException("Invalid stream status, you can't donate")
        
        try:
            new_donation = await self.donation_repo.create(
                message=donation_request.message,
                amount=donation_request.amount,
                sender_id=user.id,
                stream_id=stream_id
            )

        except IntegrityError:
            await self.session.rollback()

            logger.error(
                "Donation not inserted to database, Database error",
                exc_info=True,
                extra={"stream_id": str(stream_id)}
            )

            raise DatabaseException("Database Error")
        
        logger.info(
            "Donation inserted to database",
            extra={"donation_id": new_donation.id}
        )

        await self.stream_metric_serivce.register_donation(
            stream_id=stream_id,
            amount=new_donation.amount
        )

        logger.info(
            "Registered donation to stream metric service",
            extra={"donation_id": new_donation.id}
        )

        return new_donation
    
    async def get_donation_by_stream_id(self, stream_id: UUID, user: User) -> list[DonationResponse]: 
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": str(stream_id)}
            )

            raise StreamNotFoundException("Stream not found")
        
        if stream.streamer_id != user.id:
            logger.warning(
                "Stream not own to this user",
                extra={"user_id": str(user.id)}
            )

            raise StreamNotBelongToUser("Stream owner invalid")
        
        donations = await self.donation_repo.get_all()

        logger.info("Successful donation response")

        return donations


        


    