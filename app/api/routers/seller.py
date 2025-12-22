"""
Seller router
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database.redis import add_jti_to_blacklist

from ..dependencies import (
    SellerServiceDep,
    get_seller_access_token,
)
from ..schemas.seller import SellerCreate, SellerRead


router = APIRouter(prefix="/seller", tags=["Seller"])


### Register a new seller
@router.post("/signup", response_model=SellerRead)
async def register_seller(
    seller: SellerCreate,
    service: SellerServiceDep,
):
    """Register a new seller"""
    return await service.add(seller)


### Login a seller
@router.post("/token")
async def login_seller(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: SellerServiceDep,
):
    """Login and get access token for seller"""
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "type": "jwt",
    }


### Logout a seller
@router.get("/logout")
async def logout_seller(
    token_data: Annotated[dict, Depends(get_seller_access_token)],
):
    """Logout and invalidate the current token"""
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}
