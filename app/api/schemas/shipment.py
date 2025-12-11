from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from database.models import ShipmentStatus


class BaseShipment(BaseModel):
    content: str
    weight: float = Field(
        le=25, description="Weight in kilograms"
    )  # This should match weight_kg in model
    seller_id: int = Field(
        description="Seller ID"
    )  # Changed from 'destination' to 'seller_id'


class ShipmentRead(BaseShipment):
    id: int
    status: ShipmentStatus
    estimated_delivery: datetime


class ShipmentCreate(BaseShipment):
    pass


class ShipmentUpdate(BaseModel):
    status: Optional[ShipmentStatus] = Field(default=None)
    estimated_delivery: Optional[datetime] = Field(default=None)
    content: Optional[str] = Field(default=None)
    weight: Optional[float] = Field(default=None, le=25)
