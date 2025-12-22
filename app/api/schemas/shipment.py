"""
Shipment schemas
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.database.models import ShipmentStatus


class BaseShipment(BaseModel):
    content: str
    weight: float = Field(le=25, description="Weight in kilograms")
    destination: int = Field(description="Destination zipcode")


class ShipmentRead(BaseShipment):
    id: UUID
    status: ShipmentStatus
    estimated_delivery: datetime


class ShipmentCreate(BaseShipment):
    pass


class ShipmentUpdate(BaseModel):
    status: ShipmentStatus | None = Field(default=None)
    location: int | None = Field(default=None, description="Location zipcode where event occurred")
    description: str | None = Field(default=None, description="Event description")
    estimated_delivery: datetime | None = Field(default=None)
