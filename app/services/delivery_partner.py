"""
Delivery Partner service
"""
from typing import Optional, Sequence

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, any_

from app.api.schemas.delivery_partner import DeliveryPartnerCreate
from app.core.mail import MailClient
from app.database.models import DeliveryPartner, Shipment

from .user import UserService


class DeliveryPartnerService(UserService):
    """Service for delivery partner operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        mail_client: Optional[MailClient] = None,
        tasks: Optional[BackgroundTasks] = None,
    ):
        super().__init__(DeliveryPartner, session, mail_client=mail_client, tasks=tasks)

    async def add(self, delivery_partner: DeliveryPartnerCreate):
        """Create a new delivery partner and send verification email"""
        # _add_user now handles verification email sending
        return await self._add_user(delivery_partner.model_dump(), router_prefix="partner")

    async def verify_email(self, token: str) -> None:
        """Verify delivery partner email using verification token"""
        await super().verify_email(token)

    async def get_partner_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        """Get delivery partners that service a given zipcode"""
        return (
            await self.session.scalars(
                select(DeliveryPartner).where(
                    zipcode == any_(DeliveryPartner.serviceable_zip_codes)
                )
            )
        ).all()
    
    async def assign_shipment(self, shipment: Shipment):
        """Assign a delivery partner to a shipment based on zipcode and capacity"""
        eligible_partners = await self.get_partner_by_zipcode(shipment.destination)
        
        for partner in eligible_partners:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                return partner

        # If no eligible partners found or partners have reached max handling capacity
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No delivery partner available",
        )

    async def update(self, partner: DeliveryPartner):
        """Update a delivery partner"""
        return await self._update(partner)

    async def token(self, email: str, password: str) -> str:
        """Generate JWT token for delivery partner"""
        # Phase 2: require_verification=True (enforce email verification)
        return await self._generate_token(email, password, require_verification=True)

