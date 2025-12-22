"""
Seller service - refactored to use UserService base class
"""
import logging
from typing import Optional

from fastapi import BackgroundTasks
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.seller import SellerCreate
from app.core.mail import MailClient
from app.database.models import Seller
from app.tasks import add_background_task

from .user import UserService

logger = logging.getLogger(__name__)


class SellerService(UserService):
    """Service for seller operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        mail_client: Optional[MailClient] = None,
        tasks: Optional[BackgroundTasks] = None,
    ):
        super().__init__(Seller, session)
        self.mail_client = mail_client
        self.tasks = tasks

    async def add(self, seller_create: SellerCreate) -> Seller:
        """Create a new seller and send welcome email"""
        seller = await self._add_user(seller_create.model_dump())
        
        # Send welcome email in background (non-blocking)
        if self.mail_client and self.tasks:
            add_background_task(
                self.tasks,
                self._send_welcome_email,
                seller.email,
                seller.name,
            )
        
        return seller
    
    async def _send_welcome_email(self, email: EmailStr, name: str):
        """Send welcome email to new seller (background task)"""
        try:
            await self.mail_client.send_email(
                recipients=[email],
                subject="Welcome to FastShip! 🚀",
                body=f"Hi {name},\n\nWelcome to FastShip! Your seller account has been created successfully.\n\nYou can now start creating shipments and managing your deliveries.\n\nBest regards,\nFastShip Team",
            )
            logger.info(f"Welcome email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")

    async def token(self, email: str, password: str) -> str:
        """Generate JWT token for seller"""
        return await self._generate_token(email, password)
