"""
Shipment Event Service - handles event creation and timeline management
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mail import MailClient
from app.database.models import Shipment, ShipmentEvent, ShipmentStatus
from app.tasks import add_background_task

from .base import BaseService

logger = logging.getLogger(__name__)


class ShipmentEventService(BaseService):
    """Service for shipment event operations"""
    
    def __init__(
        self,
        session: AsyncSession,
        mail_client: Optional[MailClient] = None,
        tasks: Optional[BackgroundTasks] = None,
    ):
        super().__init__(ShipmentEvent, session)
        self.mail_client = mail_client
        self.tasks = tasks

    async def create_event(
        self,
        shipment: Shipment,
        status: ShipmentStatus,
        location: Optional[int] = None,
        description: Optional[str] = None,
    ) -> ShipmentEvent:
        """
        Create a new shipment event
        
        Args:
            shipment: The shipment to create an event for
            status: The status for this event
            location: Optional location zipcode (uses last event location if not provided)
            description: Optional description (auto-generated if not provided)
            
        Returns:
            Created ShipmentEvent
        """
        # Get last event to inherit location if not provided
        if location is None:
            last_event = await self.get_latest_event(shipment)
            if last_event:
                location = last_event.location
            else:
                # No previous events, use shipment destination
                location = shipment.destination
        
        # Generate description if not provided
        if description is None:
            description = self._generate_description(status, location)
        
        # Create new event
        new_event = ShipmentEvent(
            shipment_id=shipment.id,
            status=status,
            location=location,
            description=description,
        )
        
        # Save event
        event = await self._add(new_event)
        
        # Send notification email (if mail client available and not in_transit)
        if self.mail_client and self.tasks and status != ShipmentStatus.in_transit:
            # Reload shipment with relationships for email
            await self.session.refresh(shipment, ["seller", "delivery_partner"])
            add_background_task(
                self.tasks,
                self._send_status_notification,
                shipment,
                status,
            )
        
        return event

    async def get_latest_event(self, shipment: Shipment) -> Optional[ShipmentEvent]:
        """
        Get the latest event for a shipment (chronologically oldest, first in timeline)
        
        Args:
            shipment: The shipment to get events for
            
        Returns:
            Latest ShipmentEvent or None if no events exist
        """
        if not shipment.events:
            return None
        
        # Timeline is already sorted reverse chronologically (newest first)
        # So the last item is the oldest (first event)
        timeline = shipment.timeline
        if not timeline:
            return None
        
        # Return the oldest event (last in reversed timeline)
        return timeline[-1] if timeline else None

    async def get_shipment_timeline(self, shipment_id: UUID) -> list[ShipmentEvent]:
        """
        Get timeline of events for a shipment
        
        Args:
            shipment_id: UUID of the shipment
            
        Returns:
            List of events in reverse chronological order (newest first)
        """
        shipment = await self.session.get(Shipment, shipment_id)
        if not shipment:
            return []
        
        # Refresh to load events relationship
        await self.session.refresh(shipment, ["events"])
        return shipment.timeline

    def _generate_description(self, status: ShipmentStatus, location: int) -> str:
        """
        Generate automatic description for an event based on status
        
        Args:
            status: The shipment status
            location: The location zipcode
            
        Returns:
            Generated description string
        """
        match status:
            case ShipmentStatus.placed:
                return "assigned delivery partner"
            case ShipmentStatus.out_for_delivery:
                return "shipment out for delivery"
            case ShipmentStatus.delivered:
                return "successfully delivered"
            case ShipmentStatus.cancelled:
                return "cancelled by seller"
            case ShipmentStatus.in_transit:
                return f"scanned at {location}"
            case _:
                return f"status updated to {status.value}"

    async def _send_status_notification(
        self,
        shipment: Shipment,
        status: ShipmentStatus,
    ):
        """
        Send status notification email (background task)
        
        Args:
            shipment: The shipment with loaded relationships
            status: The new status
        """
        try:
            # Get client email if available (for Section 18 integration)
            client_email = getattr(shipment, "client_contact_email", None)
            if not client_email:
                logger.debug(f"No client email for shipment {shipment.id}, skipping notification")
                return
            
            subject: str
            template_name: str
            context: dict = {}
            
            match status:
                case ShipmentStatus.placed:
                    subject = "Your Order is Shipped 🚛"
                    template_name = "mail_placed.html"
                    context = {
                        "seller": shipment.seller.name,
                        "partner": shipment.delivery_partner.name,
                    }
                case ShipmentStatus.out_for_delivery:
                    subject = "Your Order is Arriving Soon 🛵"
                    template_name = "mail_out_for_delivery.html"
                    context = {}
                case ShipmentStatus.delivered:
                    subject = "Your Order is Delivered ✅"
                    template_name = "mail_delivered.html"
                    context = {"seller": shipment.seller.name}
                case ShipmentStatus.cancelled:
                    subject = "Your Order is Cancelled ❌"
                    template_name = "mail_cancelled.html"
                    context = {}
                case _:
                    # Don't send email for in_transit or unknown status
                    return
            
            await self.mail_client.send_email_with_template(
                recipients=[EmailStr(client_email)],
                subject=subject,
                template_name=template_name,
                context=context,
            )
            logger.info(f"Status notification sent to {client_email} for shipment {shipment.id}")
        except Exception as e:
            logger.error(f"Failed to send status notification for shipment {shipment.id}: {e}")

