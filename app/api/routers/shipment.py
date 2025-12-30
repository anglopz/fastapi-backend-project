"""
Shipment router
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from typing import Annotated

from app.config import app_settings
from app.utils import TEMPLATE_DIR
from ..dependencies import DeliveryPartnerDep, SellerDep, ShipmentServiceDep
from ..schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.database.models import ShipmentEvent


router = APIRouter(prefix="/shipment", tags=["Shipment"])

# Jinja2 templates for HTML responses
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


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
    tasks: BackgroundTasks,
):
    """Create a new shipment (authenticated seller required)"""
    # Inject BackgroundTasks into service for email sending
    service.tasks = tasks
    service.event_service.tasks = tasks
    return await service.add(shipment, seller)


### Update fields of a shipment
@router.patch("/", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    shipment_update: ShipmentUpdate,
    partner: DeliveryPartnerDep,
    service: ShipmentServiceDep,
    tasks: BackgroundTasks,
):
    """Update a shipment (only the assigned delivery partner can update)"""
    # Update data with given fields
    update = shipment_update.model_dump(exclude_none=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update",
        )
    
    # Get shipment for update
    shipment = await service.get(id)
    
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    # Inject BackgroundTasks into service for email sending
    service.tasks = tasks
    service.event_service.tasks = tasks
    
    # Update shipment with event creation (partner passed for authorization check)
    return await service.update(shipment, shipment_update, partner=partner)


### Get shipment timeline
@router.get("/timeline", response_model=list[ShipmentEvent])
async def get_shipment_timeline(
    id: UUID,
    service: ShipmentServiceDep,
):
    """Get timeline of events for a shipment"""
    shipment = await service.get(id)
    
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    
    # Refresh to load events
    await service.session.refresh(shipment, ["events"])
    return shipment.timeline


### Cancel a shipment
@router.post("/cancel", response_model=ShipmentRead)
async def cancel_shipment(
    id: UUID,
    seller: SellerDep,
    service: ShipmentServiceDep,
    tasks: BackgroundTasks,
):
    """Cancel a shipment (only the seller who created it can cancel)"""
    # Inject BackgroundTasks into service for email sending
    service.tasks = tasks
    service.event_service.tasks = tasks
    
    return await service.cancel(id, seller)


### Track shipment (HTML response)
@router.get("/track", include_in_schema=False)
async def get_tracking(
    request: Request,
    id: UUID,
    service: ShipmentServiceDep,
):
    """Get shipment tracking page (HTML response)"""
    # Check for shipment with given id
    shipment = await service.get(id)
    
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    
    # Refresh to load relationships
    await service.session.refresh(shipment, ["delivery_partner", "events"])
    
    # Prepare context for template
    # Pass shipment object directly so template can access id.hex
    context = {
        "request": request,
        "id": shipment.id,  # UUID object for .hex access
        "content": shipment.content,
        "weight": shipment.weight,
        "destination": shipment.destination,
        "status": shipment.status,
        "estimated_delivery": shipment.estimated_delivery,
        "created_at": shipment.created_at,
        "partner": shipment.delivery_partner.name,
        "timeline": shipment.timeline,  # Already reversed (newest first)
    }
    
    return templates.TemplateResponse(
        request=request,
        name="track.html",
        context=context,
    )


### Delete a shipment by id
@router.delete("/")
async def delete_shipment(id: UUID, service: ShipmentServiceDep) -> dict[str, str]:
    """Delete a shipment by ID"""
    # Remove from database
    await service.delete(id)

    return {"detail": f"Shipment with id #{id} is deleted!"}


### Submit a review for a shipment (HTML form)
@router.get("/review", include_in_schema=False)
async def get_review_form(
    request: Request,
    token: str,
):
    """Display review submission form"""
    return templates.TemplateResponse(
        request=request,
        name="review.html",
        context={
            "review_url": f"http://{app_settings.APP_DOMAIN}/shipment/review?token={token}",
        },
    )


### Submit a review for a shipment
@router.post("/review", include_in_schema=False)
async def submit_review(
    token: str,
    service: ShipmentServiceDep,
    rating: Annotated[int, Form(ge=1, le=5)],
    comment: Annotated[str | None, Form()] = None,
):
    """Submit a review for a shipment"""
    await service.rate(token, rating, comment)
    return {"detail": "Review submitted successfully"}
