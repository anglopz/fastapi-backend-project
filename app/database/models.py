"""
Database models using SQLModel
"""
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy.dialects import postgresql
from sqlalchemy import ARRAY, INTEGER, JSON
from sqlmodel import Column, Field, Relationship, SQLModel


class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class User(SQLModel):
    """Base user model (non-table)"""
    name: str
    email: str  # EmailStr validated at schema level, stored as str
    email_verified: bool = Field(default=False, description="Email verification status")
    password_hash: str = Field(exclude=True)


class Seller(User, table=True):
    """Seller model inheriting from User"""
    __tablename__ = "seller"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    shipments: list["Shipment"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class DeliveryPartner(User, table=True):
    """Delivery Partner model inheriting from User"""
    __tablename__ = "delivery_partner"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    serviceable_zip_codes: list[int] = Field(
        sa_column=Column(ARRAY(INTEGER)),
    )
    max_handling_capacity: int

    shipments: list["Shipment"] = Relationship(
        back_populates="delivery_partner",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    
    @property
    def active_shipments(self):
        """Get shipments that are not yet delivered"""
        return [
            shipment
            for shipment in self.shipments
            if shipment.status != ShipmentStatus.delivered
        ]
    
    @property
    def current_handling_capacity(self):
        """Calculate remaining handling capacity"""
        return self.max_handling_capacity - len(self.active_shipments)


class ShipmentEvent(SQLModel, table=True):
    """Shipment event model for tracking shipment status changes"""
    __tablename__ = "shipment_event"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    location: int = Field(description="Location zipcode where event occurred")
    status: ShipmentStatus
    description: str | None = Field(default=None, description="Event description")

    shipment_id: UUID = Field(foreign_key="shipment.id")
    shipment: "Shipment" = Relationship(
        back_populates="events",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

class Shipment(SQLModel, table=True):
    """Shipment model"""
    __tablename__ = "shipment"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    # Phase 2: client_contact_email is now required
    client_contact_email: str = Field(description="Client contact email (required)")
    client_contact_phone: str | None = Field(default=None, description="Client contact phone number")

    content: str
    weight: float = Field(le=25, description="Weight in kilograms")
    destination: int = Field(description="Destination zipcode")
    status: ShipmentStatus
    estimated_delivery: datetime

    seller_id: UUID = Field(foreign_key="seller.id")
    seller: Seller = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    delivery_partner_id: UUID = Field(
        foreign_key="delivery_partner.id",
    )
    delivery_partner: DeliveryPartner = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    events: list["ShipmentEvent"] = Relationship(
        back_populates="shipment",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    review: Optional["Review"] = Relationship(
        back_populates="shipment",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )

    @property
    def timeline(self) -> list["ShipmentEvent"]:
        """Return events in reverse chronological order (newest first)"""
        if not self.events:
            return []
        return sorted(self.events, key=lambda e: e.created_at, reverse=True)


class Review(SQLModel, table=True):
    """Review model for shipment ratings"""
    __tablename__ = "review"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(default=None, description="Optional review comment")

    shipment_id: UUID = Field(
        foreign_key="shipment.id",
        unique=True,  # One-to-one relationship: one review per shipment
    )
    shipment: "Shipment" = Relationship(
        back_populates="review",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
