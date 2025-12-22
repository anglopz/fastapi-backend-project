"""
User service base class providing common user operations
"""
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.utils import generate_access_token

from .base import BaseService

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class UserService(BaseService):
    """Base service for user-related operations"""
    
    def __init__(self, model: type[User], session: AsyncSession):
        super().__init__(model, session)
        self.model = model

    async def _add_user(self, data: dict) -> User:
        """Add a new user with password hashing"""
        user = self.model(
            **data,
            password_hash=password_context.hash(data["password"]),
        )
        return await self._add(user)

    async def _get_by_email(self, email: str) -> User | None:
        """Get a user by email"""
        return await self.session.scalar(
            select(self.model).where(self.model.email == email)
        )

    async def _generate_token(self, email: str, password: str) -> str:
        """Generate JWT token for user authentication"""
        # Validate the credentials
        user = await self._get_by_email(email)

        if user is None or not password_context.verify(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or password is incorrect",
            )

        return generate_access_token(
            data={
                "user": {
                    "name": user.name,
                    "id": str(user.id),
                },
            }
        )

