from pydantic import BaseModel, ConfigDict
from uuid import UUID
from decimal import Decimal


class DonationRequest(BaseModel):
    message: str | None = None
    amount: Decimal


class DonationResponse(BaseModel):
    sender_id: UUID
    stream_id: UUID
    amount: Decimal
    message: str

    model_config = ConfigDict(from_attributes=True)