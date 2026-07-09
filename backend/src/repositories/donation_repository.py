

from .base_repository import BaseRepository
from src.database.models import Donation


class DonationRepository(BaseRepository):
    model = Donation