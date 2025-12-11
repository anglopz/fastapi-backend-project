from fastapi import APIRouter, HTTPException, status
from typing import List

from api.dependencies import SellerServiceDep, ShipmentServiceDep
from api.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate

router = APIRouter(prefix="/shipments", tags=["shipments"])

@router.get("/", response_model=List[ShipmentRead])
async def get_shipments(service: ShipmentServiceDep):
    """Get all shipments."""
    return await service.get_all()

@router.get("/{id}", response_model=ShipmentRead)
async def get_shipment(id: int, service: ShipmentServiceDep):
    """Get a specific shipment by ID."""
    shipment = await service.get_by_id(id)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    return shipment

@router.post("/", response_model=ShipmentRead, status_code=201)
async def create_shipment(
    shipment: ShipmentCreate,
    service: ShipmentServiceDep,
    seller_service: SellerServiceDep,
):
    """Create a new shipment."""
    seller = await seller_service.get_by_id(shipment.seller_id)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller not found"
        )
    return await service.create(shipment)

@router.patch("/{id}", response_model=ShipmentRead)
async def update_shipment(
    id: int,
    shipment_update: ShipmentUpdate,
    service: ShipmentServiceDep,
):
    """Update an existing shipment."""
    update_data = shipment_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update",
        )
    shipment = await service.update(id, update_data)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    return shipment

@router.delete("/{id}", status_code=204)
async def delete_shipment(id: int, service: ShipmentServiceDep):
    """Delete a shipment."""
    success = await service.delete(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    return None
