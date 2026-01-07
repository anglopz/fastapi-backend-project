"""
Shipment schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.database.models import ShipmentStatus, TagName


class BaseShipment(BaseModel):
    content: str
    weight: float = Field(le=25, description="Weight in kilograms")
    destination: int = Field(description="Destination zipcode")


class ShipmentRead(BaseShipment):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: ShipmentStatus
    estimated_delivery: datetime
    client_contact_email: str
    client_contact_phone: str | None = None
    tags: Optional[list[TagName]] = Field(default=None, description="List of tags associated with the shipment")
    
    @field_validator('tags', mode='before')
    @classmethod
    def extract_tag_names(cls, v):
        """Extract tag names from Tag objects if needed"""
        if v is None:
            return None
        if isinstance(v, list):
            # If list contains Tag objects, extract names
            # Check if first item has a 'name' attribute (Tag object)
            if v and hasattr(v[0], 'name'):
                return [tag.name for tag in v]
            # If already TagName enum values, return as is
            return v
        return v


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
