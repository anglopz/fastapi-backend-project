"""
Delivery Partner router
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database.redis import add_jti_to_blacklist

from ..dependencies import (
    DeliveryPartnerDep,
    DeliveryPartnerServiceDep,
    get_partner_access_token,
)
from ..schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
)

router = APIRouter(prefix="/partner", tags=["Delivery Partner"])


### Register a new delivery partner
@router.post("/signup", response_model=DeliveryPartnerRead)
async def register_delivery_partner(
    partner: DeliveryPartnerCreate,
    service: DeliveryPartnerServiceDep,
):
    """Register a new delivery partner"""
    return await service.add(partner)


### Login a delivery partner
@router.post("/token")
async def login_delivery_partner(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DeliveryPartnerServiceDep,
):
    """Login and get access token for delivery partner"""
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "type": "jwt",
    }


### Update the logged in delivery partner
@router.post("/", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    """Update the currently logged in delivery partner"""
    # Update data with given fields
    update = partner_update.model_dump(exclude_none=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update",
        )

    # Update partner fields
    for key, value in update.items():
        if hasattr(partner, key):
            setattr(partner, key, value)
    
    return await service.update(partner)


### Logout a delivery partner
@router.get("/logout")
async def logout_delivery_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
):
    """Logout and invalidate the current token"""
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}

