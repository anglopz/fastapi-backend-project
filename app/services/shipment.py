"""
Shipment service - refactored to use BaseService and partner assignment
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.core.mail import MailClient
from app.database.models import Seller, Shipment, ShipmentStatus

from .base import BaseService
from .delivery_partner import DeliveryPartnerService
from .event import ShipmentEventService

logger = logging.getLogger(__name__)


class ShipmentService(BaseService):
    """Service for shipment operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        partner_service: DeliveryPartnerService,
        event_service: ShipmentEventService,
        mail_client: Optional[MailClient] = None,
        tasks: Optional[BackgroundTasks] = None,
    ):
        super().__init__(Shipment, session)
        self.partner_service = partner_service
        self.event_service = event_service
        self.mail_client = mail_client
        self.tasks = tasks

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

        shipment = await self._add(new_shipment)
        
        # Create initial placed event (this will also send email notification)
        await self.event_service.create_event(
            shipment=shipment,
            status=ShipmentStatus.placed,
            location=seller.zip_code if hasattr(seller, 'zip_code') else shipment.destination,
            description=f"assigned to {partner.name}",
        )
        
        # Refresh shipment to load events
        await self.session.refresh(shipment, ["events"])
        
        return shipment

    async def update(self, shipment: Shipment, shipment_update: ShipmentUpdate) -> Shipment:
        """Update an existing shipment and create event if status/location changed"""
        old_status = shipment.status
        
        # Update shipment fields
        update_data = shipment_update.model_dump(exclude_none=True)
        
        # Update estimated_delivery if provided
        if shipment_update.estimated_delivery:
            shipment.estimated_delivery = shipment_update.estimated_delivery
        
        # Update status if provided
        if shipment_update.status:
            shipment.status = shipment_update.status
        
        # Save changes
        updated_shipment = await self._update(shipment)
        
        # Create event if status or location changed
        if shipment_update.status or shipment_update.location:
            await self.event_service.create_event(
                shipment=updated_shipment,
                status=shipment_update.status or old_status,
                location=shipment_update.location,
                description=shipment_update.description,
            )
            # Refresh to load new event
            await self.session.refresh(updated_shipment, ["events"])
        
        return updated_shipment

    async def cancel(self, id: UUID, seller: Seller) -> Shipment:
        """
        Cancel a shipment (only the seller who created it can cancel)
        
        Args:
            id: UUID of the shipment to cancel
            seller: The seller attempting to cancel (must be the owner)
            
        Returns:
            Updated Shipment with cancelled status
            
        Raises:
            HTTPException: If shipment not found or seller not authorized
        """
        shipment = await self.get(id)
        
        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found",
            )
        
        # Validate seller owns this shipment
        if shipment.seller_id != seller.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to cancel this shipment",
            )
        
        # Update status to cancelled
        shipment.status = ShipmentStatus.cancelled
        
        # Save changes
        updated_shipment = await self._update(shipment)
        
        # Create cancellation event (this will also send email notification)
        await self.event_service.create_event(
            shipment=updated_shipment,
            status=ShipmentStatus.cancelled,
            description="cancelled by seller",
        )
        
        # Refresh to load new event
        await self.session.refresh(updated_shipment, ["events"])
        
        return updated_shipment

    async def delete(self, id: UUID) -> None:
        """Delete a shipment"""
        shipment = await self.get(id)
        if shipment:
            await self._delete(shipment)
