"""
Shipment router
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..dependencies import DeliveryPartnerDep, SellerDep, ShipmentServiceDep
from ..schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate


router = APIRouter(prefix="/shipment", tags=["Shipment"])


### Read a shipment by id
@router.get("/", response_model=ShipmentRead)
async def get_shipment(id: UUID, service: ShipmentServiceDep):
    """Get a shipment by ID"""
    # Check for shipment with given id
    shipment = await service.get(id)

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!",
        )

    return shipment


### Create a new shipment
@router.post("/", response_model=ShipmentRead)
async def submit_shipment(
    seller: SellerDep,
    shipment: ShipmentCreate,
    service: ShipmentServiceDep,
):
    """Create a new shipment (authenticated seller required)"""
    return await service.add(shipment, seller)


### Update fields of a shipment
@router.patch("/", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    shipment_update: ShipmentUpdate,
    partner: DeliveryPartnerDep,
    service: ShipmentServiceDep,
):
    """Update a shipment (only the assigned delivery partner can update)"""
    # Update data with given fields
    update = shipment_update.model_dump(exclude_none=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update",
        )
    
    # Validate logged in partner with assigned partner
    # on the shipment with given id
    shipment = await service.get(id)

    if shipment.delivery_partner_id != partner.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
        )

    # Update shipment fields
    for key, value in update.items():
        if hasattr(shipment, key):
            setattr(shipment, key, value)
    
    return await service.update(shipment)


### Delete a shipment by id
@router.delete("/")
async def delete_shipment(id: UUID, service: ShipmentServiceDep) -> dict[str, str]:
    """Delete a shipment by ID"""
    # Remove from database
    await service.delete(id)

    return {"detail": f"Shipment with id #{id} is deleted!"}
