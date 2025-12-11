from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.dependencies import SellerServiceDep
from api.schemas.seller import SellerCreate, SellerRead
from core.exceptions import AlreadyExistsError, UnauthorizedError

router = APIRouter(prefix="/sellers", tags=["sellers"])

@router.get("/", response_model=List[SellerRead])
async def get_sellers(service: SellerServiceDep):
    """Get all sellers."""
    return await service.get_all()

@router.get("/{seller_id}", response_model=SellerRead)
async def get_seller(seller_id: int, service: SellerServiceDep):
    """Get a specific seller by ID."""
    seller = await service.get_by_id(seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller

@router.post("/signup", response_model=SellerRead, status_code=201)
async def create_seller(seller: SellerCreate, service: SellerServiceDep):
    """Create a new seller (signup)."""
    try:
        return await service.add(seller)
    except AlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error creating seller: {str(e)}"
        )

@router.post("/token")
async def login_for_token(
    service: SellerServiceDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Get JWT token for authentication."""
    try:
        token = await service.token(form_data.username, form_data.password)
        return {"access_token": token, "token_type": "bearer"}
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during login: {str(e)}"
        )
