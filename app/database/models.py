from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"


class Shipment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    weight_kg: float = Field(description="Weight in kilograms")  # Fixed: changed from weight to weight_kg
    seller_id: int = Field(foreign_key="seller.id")  # Changed: destination to seller_id
    status: ShipmentStatus
    estimated_delivery: datetime


class Seller(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)  # Fixed: changed from EmailStr to str
    password_hash: str  # Added: missing field from seller service
