"""
Seller router
"""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr

from app.config import app_settings
from app.database.redis import add_jti_to_blacklist
from app.utils import TEMPLATE_DIR

from ..dependencies import (
    SellerServiceDep,
    get_seller_access_token,
)
from ..schemas.seller import SellerCreate, SellerRead


router = APIRouter(prefix="/seller", tags=["Seller"])

# Jinja2 templates for HTML responses
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


### Register a new seller
@router.post("/signup", response_model=SellerRead)
async def register_seller(
    seller: SellerCreate,
    service: SellerServiceDep,
    tasks: BackgroundTasks,
):
    """Register a new seller"""
    # Inject BackgroundTasks into service for email sending
    service.tasks = tasks
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


### Verify seller email
@router.get("/verify")
async def verify_seller_email(
    token: str,
    service: SellerServiceDep,
):
    """Verify seller email using verification token"""
    await service.verify_email(token)
    return {"detail": "Email verified successfully"}


### Email Password Reset Link
@router.get("/forgot_password")
async def forgot_password(
    email: EmailStr,
    service: SellerServiceDep,
    tasks: BackgroundTasks,
):
    """Request password reset link via email"""
    # Inject BackgroundTasks into service for email sending
    service.tasks = tasks
    await service.send_password_reset_link(email, router.prefix)
    return {"detail": "Check email for password reset link"}


### Password Reset Form
@router.get("/reset_password_form")
async def get_reset_password_form(
    request: Request,
    token: str,
):
    """Display password reset form (HTML response)"""
    return templates.TemplateResponse(
        request=request,
        name="password/reset.html",
        context={
            "reset_url": f"http://{app_settings.APP_DOMAIN}{router.prefix}/reset_password?token={token}"
        }
    )


### Reset Seller Password
@router.post("/reset_password")
async def reset_password(
    request: Request,
    token: str,
    password: Annotated[str, Form()],
    service: SellerServiceDep,
):
    """Process password reset"""
    is_success = await service.reset_password(token, password)
    
    return templates.TemplateResponse(
        request=request,
        name="password/reset_success.html" if is_success else "password/reset_failed.html",
    )


### Logout a seller
@router.get("/logout")
async def logout_seller(
    token_data: Annotated[dict, Depends(get_seller_access_token)],
):
    """Logout and invalidate the current token"""
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}
