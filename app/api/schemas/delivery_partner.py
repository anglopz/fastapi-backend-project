"""
Delivery Partner schemas
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.database.models import Location


class BaseDeliveryPartner(BaseModel):
    name: str
    email: EmailStr
    servicable_locations: list[int] = Field(
        description="List of zip codes for serviceable locations (Phase 3: uses relationship)"
    )
    max_handling_capacity: int


class DeliveryPartnerRead(BaseDeliveryPartner):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    
    @field_validator('servicable_locations', mode='before')
    @classmethod
    def extract_zip_codes(cls, v):
        """Extract zip codes from Location objects if needed"""
        if v is None:
            return None
        if isinstance(v, list):
            # If list contains Location objects, extract zip_code
            if v and hasattr(v[0], 'zip_code'):
                return [location.zip_code for location in v]
            # If already integers, return as is
            return v
        return v


class DeliveryPartnerUpdate(BaseModel):
    servicable_locations: list[int] | None = Field(
        default=None,
        description="List of zip codes for serviceable locations (Phase 3: uses relationship)"
    )
    max_handling_capacity: int | None = Field(default=None)


class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str

