"""
Shipment schemas
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.database.models import ShipmentStatus


class BaseShipment(BaseModel):
    content: str
    weight: float = Field(le=25, description="Weight in kilograms")
    destination: int = Field(description="Destination zipcode")


class ShipmentRead(BaseShipment):
    id: UUID
    status: ShipmentStatus
    estimated_delivery: datetime
    client_contact_email: str
    client_contact_phone: str | None = None


class ShipmentCreate(BaseShipment):
    # Phase 2: client_contact_email is now required
    client_contact_email: EmailStr = Field(description="Client contact email (required)")
    client_contact_phone: str | None = Field(default=None, description="Client contact phone number")


class ShipmentUpdate(BaseModel):
    status: ShipmentStatus | None = Field(default=None)
    location: int | None = Field(default=None, description="Location zipcode where event occurred")
    description: str | None = Field(default=None, description="Event description")
    verification_code: str | None = Field(default=None, description="Verification code required when status is 'delivered'")
    estimated_delivery: datetime | None = Field(default=None)
