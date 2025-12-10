from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.shipment import ShipmentCreate
from database.models import Shipment, ShipmentStatus


class ShipmentService:
    def __init__(self, session: AsyncSession):
        # Get database session to perform database operations
        self.session = session

    # Get a shipment by id
    async def get(self, id: int) -> Shipment | None:
        return await self.session.get(Shipment, id)

    # Add a new shipment
    async def add(self, shipment_create: ShipmentCreate) -> Shipment:
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
        )
        self.session.add(new_shipment)
        await self.session.commit()
        await self.session.refresh(new_shipment)

        return new_shipment

    # Update an existing shipment
    async def update(self, id: int, shipment_update: dict) -> Shipment:
        shipment = await self.get(id)
        if shipment is None:
            # Caller should handle not-found cases; raise an error to make
            # the failure explicit during runtime.
            raise LookupError(f"Shipment with id {id} not found")

        # Apply provided fields to the SQLModel instance
        for key, value in shipment_update.items():
            setattr(shipment, key, value)

        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)

        return shipment

    # Delete a shipment
    async def delete(self, id: int) -> None:
        await self.session.delete(await self.get(id))
        await self.session.commit()
