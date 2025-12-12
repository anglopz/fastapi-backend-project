from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_token
from database.redis import is_blacklisted
from database.session import get_session
from services.seller import SellerService
from services.shipment import ShipmentService


# Asynchronous database session dep annotation
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Shipment service dep
def get_shipment_service(session: SessionDep):
    return ShipmentService(session)


# Seller service dep
def get_seller_service(session: SessionDep):
    return SellerService(session)


# Shipment service dep annotation
ShipmentServiceDep = Annotated[
    ShipmentService,
    Depends(get_shipment_service),
]

# Seller service dep annotation
SellerServiceDep = Annotated[
    SellerService,
    Depends(get_seller_service),
]

# -------------------------------------------------------------------
# Dependencias de autenticación con verificación de blacklist
# -------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="sellers/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """Obtiene el usuario actual verificando token y blacklist"""
    # Verificar token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si el token está en blacklist
    jti = payload.get("jti")
    if jti and await is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload
