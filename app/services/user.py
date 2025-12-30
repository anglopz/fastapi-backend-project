"""
User service base class providing common user operations
"""
from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.utils import decode_url_safe_token, generate_access_token, generate_url_safe_token

from .base import BaseService

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class UserService(BaseService):
    """Base service for user-related operations"""
    
    def __init__(
        self,
        model: type[User],
        session: AsyncSession,
        mail_client: Optional = None,
        tasks: Optional[BackgroundTasks] = None,
    ):
        super().__init__(model, session)
        self.model = model
        self.mail_client = mail_client
        self.tasks = tasks

    async def _add_user(self, data: dict, router_prefix: str = "seller") -> User:
        """
        Add a new user with password hashing and send verification email
        
        Args:
            data: User data dictionary
            router_prefix: Router prefix for verification URL (e.g., "seller" or "partner")
        """
        user = self.model(
            **data,
            password_hash=password_context.hash(data["password"]),
            email_verified=False,  # New users start unverified
        )
        user = await self._add(user)
        
        # Send verification email if mail client available
        if self.mail_client and self.tasks:
            await self._send_verification_email(user, router_prefix)
        
        return user

    async def _send_verification_email(self, user: User, router_prefix: str):
        """Send email verification link (background task)"""
        from app.config import app_settings
        from app.tasks import add_background_task
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Generate verification token
            token = generate_url_safe_token({"id": str(user.id)})
            verification_url = f"http://{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}"
            
            # Send email in background
            add_background_task(
                self.tasks,
                self.mail_client.send_email_with_template,
                recipients=[user.email],
                subject="Verify Your Account With FastShip",
                template_name="mail_email_verify.html",
                context={
                    "username": user.name,
                    "verification_url": verification_url,
                },
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")

    async def verify_email(self, token: str) -> None:
        """
        Verify user email using verification token
        
        Args:
            token: URL-safe verification token
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Decode token
        token_data = decode_url_safe_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )
        
        # Get user by ID from token
        user_id = UUID(token_data["id"])
        user = await self._get(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Mark email as verified
        user.email_verified = True
        await self._update(user)

    async def _get_by_email(self, email: str) -> User | None:
        """Get a user by email"""
        return await self.session.scalar(
            select(self.model).where(self.model.email == email)
        )

    async def _generate_token(self, email: str, password: str, require_verification: bool = False) -> str:
        """
        Generate JWT token for user authentication
        
        Args:
            email: User email
            password: User password
            require_verification: If True, requires email_verified=True (Phase 2)
            
        Returns:
            JWT access token string
        """
        # Validate the credentials
        user = await self._get_by_email(email)

        if user is None or not password_context.verify(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or password is incorrect",
            )

        # Phase 2: Check email verification (disabled in Phase 1)
        if require_verification and not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified. Please check your email for verification link.",
            )

        return generate_access_token(
            data={
                "user": {
                    "name": user.name,
                    "id": str(user.id),
                },
            }
        )

    async def send_password_reset_link(self, email: str, router_prefix: str) -> None:
        """
        Send password reset link via email.
        
        Security: Does not reveal if email exists to prevent email enumeration.
        
        Args:
            email: User email address
            router_prefix: Router prefix for reset URL (e.g., "seller" or "partner")
        """
        from app.config import app_settings
        from app.tasks import add_background_task
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get user by email (don't reveal if user exists for security)
        user = await self._get_by_email(email)
        if not user:
            # Don't reveal if email exists (security best practice)
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return
        
        try:
            # Generate password reset token with salt
            token = generate_url_safe_token({"id": str(user.id)}, salt="password-reset")
            reset_url = f"http://{app_settings.APP_DOMAIN}/{router_prefix}/reset_password_form?token={token}"
            
            # Send email in background
            if self.mail_client and self.tasks:
                add_background_task(
                    self.tasks,
                    self.mail_client.send_email_with_template,
                    recipients=[user.email],
                    subject="FastShip Account Password Reset",
                    template_name="mail_password_reset.html",
                    context={
                        "username": user.name,
                        "reset_url": reset_url,
                    },
                )
                logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")

    async def reset_password(self, token: str, password: str) -> bool:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token (with salt="password-reset")
            password: New password to set
            
        Returns:
            True if password reset successful, False if token invalid/expired
        """
        # Decode token with salt and 24-hour expiration
        token_data = decode_url_safe_token(
            token,
            salt="password-reset",
            expiry=timedelta(days=1)
        )
        
        if not token_data:
            return False
        
        # Get user by ID from token
        try:
            user_id = UUID(token_data["id"])
        except (ValueError, KeyError):
            return False
        
        user = await self._get(user_id)
        if user is None:
            return False
        
        # Update password hash
        user.password_hash = password_context.hash(password)
        await self._update(user)
        
        return True

