

from .base_repository import BaseRepository
from src.database.models import Category


class CategoryRepository(BaseRepository):
    model = Category