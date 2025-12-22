"""
Shipment service - refactored to use BaseService and partner assignment
"""
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.shipment import ShipmentCreate
from app.database.models import Seller, Shipment, ShipmentStatus

from .base import BaseService
from .delivery_partner import DeliveryPartnerService


class ShipmentService(BaseService):
    """Service for shipment operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        partner_service: DeliveryPartnerService,
    ):
        super().__init__(Shipment, session)
        self.partner_service = partner_service

    async def get(self, id: UUID) -> Shipment | None:
        """Get a shipment by ID"""
        return await self._get(id)

    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        """Create a new shipment and assign a delivery partner"""
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
        )
        # Assign delivery partner to the shipment
        partner = await self.partner_service.assign_shipment(new_shipment)
        # Add the delivery partner foreign key
        new_shipment.delivery_partner_id = partner.id

        return await self._add(new_shipment)

    async def update(self, shipment: Shipment) -> Shipment:
        """Update an existing shipment"""
        return await self._update(shipment)

    async def delete(self, id: UUID) -> None:
        """Delete a shipment"""
        shipment = await self.get(id)
        if shipment:
            await self._delete(shipment)
