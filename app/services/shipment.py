from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.schemas.shipment import ShipmentCreate
from database.models import Shipment, ShipmentStatus


class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        """Get all shipments"""
        result = await self.session.execute(select(Shipment))
        return result.scalars().all()

    async def get_by_id(self, id: int) -> Shipment | None:
        """Get a shipment by id"""
        return await self.session.get(Shipment, id)

    async def create(self, shipment_create: ShipmentCreate) -> Shipment:
        """Create a new shipment"""
        new_shipment = Shipment(
            content=shipment_create.content,
            weight_kg=shipment_create.weight,  # Note: schema uses 'weight' but model uses 'weight_kg'
            seller_id=shipment_create.seller_id,  # Fixed: schema now uses 'seller_id'
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
        )
        self.session.add(new_shipment)
        await self.session.commit()
        await self.session.refresh(new_shipment)
        return new_shipment

    async def update(self, id: int, shipment_update: dict) -> Shipment | None:
        """Update an existing shipment"""
        shipment = await self.get_by_id(id)
        if shipment is None:
            return None

        for key, value in shipment_update.items():
            if hasattr(shipment, key):
                setattr(shipment, key, value)

        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def delete(self, id: int) -> bool:
        """Delete a shipment"""
        shipment = await self.get_by_id(id)
        if shipment:
            await self.session.delete(shipment)
            await self.session.commit()
            return True
        return False
