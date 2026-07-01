from abc import ABC, abstractmethod
from sqlalchemy import select
from uuid import UUID
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):
    @abstractmethod
    async def create(self, data: dict):
        raise NotImplementedError
    
    @abstractmethod
    async def get(self, id: UUID):
        raise NotImplementedError
    
    @abstractmethod
    async def get_all(self):
        raise NotImplementedError


class BaseRepository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs):
        try:
            new_object = self.model(**kwargs)  
            self.session.add(new_object)
            await self.session.commit()
            await self.session.refresh(new_object)

            return new_object
        except:
            await self.session.rollback()
            raise

    async def get(self, id: UUID):
        obj = await self.session.get(self.model, id)

        return obj
    
    """async def get_obj(self, id: UUID):
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )

        return result.scalar_one_or_none()"""
     
    async def get_all(self):
        result = await self.session.execute(select(self.model))

        return result.scalars().all()
    
    async def update(self, id: UUID, data: Dict[str, Any]):
        obj = await self.session.get(self.model, id)
  
        try:
            if obj: 
                for key, value in data.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
            
            await self.session.commit()
            await self.session.refresh(obj)

            return obj

        except Exception:
            await self.session.rollback()
            raise

    async def delete(self, id: UUID):
        obj = await self.session.get(self.model, id)

        await self.session.delete(obj)
        await self.session.commit()

        return obj
