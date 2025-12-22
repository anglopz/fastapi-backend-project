"""
Seller service - refactored to use UserService base class
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.seller import SellerCreate
from app.database.models import Seller

from .user import UserService


class SellerService(UserService):
    """Service for seller operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Seller, session)

    async def add(self, seller_create: SellerCreate) -> Seller:
        """Create a new seller"""
        return await self._add_user(seller_create.model_dump())

    async def token(self, email: str, password: str) -> str:
        """Generate JWT token for seller"""
        return await self._generate_token(email, password)
