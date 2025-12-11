from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.schemas.seller import SellerCreate
from database.models import Seller
from core.security import create_access_token, hash_password, verify_password
from core.exceptions import AlreadyExistsError, UnauthorizedError

class SellerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        """Get all sellers"""
        result = await self.session.execute(select(Seller))
        return result.scalars().all()

    async def get_by_id(self, seller_id: int) -> Seller | None:
        """Get seller by ID"""
        return await self.session.get(Seller, seller_id)

    async def add(self, credentials: SellerCreate) -> Seller:
        """Create a new seller"""
        try:
            # Verificar si el email ya existe
            stmt = select(Seller).where(Seller.email == credentials.email)
            result = await self.session.execute(stmt)
            existing_seller = result.scalar_one_or_none()
            
            if existing_seller:
                raise AlreadyExistsError(f"Email {credentials.email} already exists")
            
            # Crear el seller usando core.security
            seller = Seller(
                name=credentials.name,
                email=credentials.email,
                password_hash=hash_password(credentials.password),
            )
            
            self.session.add(seller)
            await self.session.commit()
            await self.session.refresh(seller)
            return seller
            
        except IntegrityError as e:
            await self.session.rollback()
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                raise AlreadyExistsError(f"Email {credentials.email} already exists") from e
            raise
            
        except Exception as e:
            await self.session.rollback()
            raise

    async def token(self, username: str, password: str) -> str:
        """Generate JWT token for seller"""
        try:
            # Find seller by email
            stmt = select(Seller).where(Seller.email == username)
            result = await self.session.execute(stmt)
            seller = result.scalar_one_or_none()
            
            if not seller:
                raise UnauthorizedError("Invalid email or password")
            
            # Verificar contraseña usando core.security
            if not verify_password(password, seller.password_hash):
                raise UnauthorizedError("Invalid email or password")
            
            # Generate token
            token = create_access_token({"sub": str(seller.id)})
            return token
            
        except UnauthorizedError:
            raise
        except Exception as e:
            raise
