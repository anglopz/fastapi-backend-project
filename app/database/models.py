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


class User(SQLModel):
    """Base user model (non-table)"""
    name: str
    email: str  # EmailStr validated at schema level, stored as str
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
