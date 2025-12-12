from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.dependencies import SellerServiceDep, get_current_user
from api.schemas.seller import SellerCreate, SellerRead
from core.exceptions import AlreadyExistsError, UnauthorizedError
from api.dependencies import oauth2_scheme  # Para autenticación en endpoint logout

router = APIRouter(prefix="/sellers", tags=["sellers"])

@router.get("/", response_model=List[SellerRead])
async def get_sellers(
    service: SellerServiceDep,
    current_user: dict = Depends(get_current_user)  # Ahora verifica blacklist
):
    """Get all sellers."""
    return await service.get_all()

@router.get("/{seller_id}", response_model=SellerRead)
async def get_seller(
    seller_id: int,
    service: SellerServiceDep,
    current_user: dict = Depends(get_current_user)  # Ahora verifica blacklist
):
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

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
):
    """Logout - invalida el token actual añadiéndolo a blacklist"""
    from core.security import verify_token
    from database.redis import add_to_blacklist, is_blacklisted
    
    # Verificar token
    payload = verify_token(token)
    if not payload or "jti" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    jti = payload["jti"]
    
    # Verificar si el token ya está en blacklist
    if await is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already revoked"
        )
    
    # Añadir a blacklist (expira en 24 horas por defecto)
    await add_to_blacklist(jti)
    
    return {"message": "Successfully logged out", "jti": jti}
