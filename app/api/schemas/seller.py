from pydantic import BaseModel, EmailStr


class BaseSeller(BaseModel):
    name: str
    email: EmailStr


class SellerRead(BaseSeller):
    id: int  # Added id field


class SellerCreate(BaseSeller):
    password: str
