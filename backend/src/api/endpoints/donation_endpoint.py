from fastapi import APIRouter, Depends
from uuid import UUID

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.api.schemas.donation_schema import DonationResponse, DonationRequest
from src.services.donation_service import DonationService
from src.api.dependencies.require_role_dependency import require_roles


donation_route = APIRouter(
    prefix="/api",
    tags=["Donation"]
)

async def get_donation_service(session: AsyncSession = Depends(get_session)):
    return DonationService(session=session)


@donation_route.post("/stream/{stream_id}/donate", response_model=DonationResponse, status_code=201)
async def donate(
    stream_id: UUID,
    donation: DonationRequest,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    donation_service: DonationService = Depends(get_donation_service)
):
    return await donation_service.donate_by_stream_id(stream_id=stream_id, user=user, donation_request=donation)


@donation_route.get("/stream/{stream_id}/donations", response_model=list[DonationResponse], status_code=200)
async def get_donations(
    stream_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    donation_service: DonationService = Depends(get_donation_service)
):
    return await donation_service.get_donation_by_stream_id(stream_id=stream_id, user=user)