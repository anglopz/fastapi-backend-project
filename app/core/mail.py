"""
Mail service with SMTP connection, pooling, and retry logic
"""
import asyncio
import logging
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pydantic import EmailStr

from app.config import mail_settings
from app.utils import TEMPLATE_DIR

logger = logging.getLogger(__name__)


class MailClient:
    """
    Mail client with connection pooling, retry logic, and template rendering.
    
    This service is designed to be injectable into other services like
    SellerService and ShipmentService.
    """
    
    def __init__(self):
        """Initialize mail client with connection pooling"""
        self._fastmail: Optional[FastMail] = None
        self._template_env: Optional[Environment] = None
        self._max_retries = 3
        self._retry_delay = 1.0  # Initial delay in seconds
        
    @property
    def fastmail(self) -> FastMail:
        """Lazy initialization of FastMail client with connection pooling"""
        if self._fastmail is None:
            # FastMail handles connection pooling internally
            config = ConnectionConfig(
                MAIL_USERNAME=mail_settings.MAIL_USERNAME,
                MAIL_PASSWORD=mail_settings.MAIL_PASSWORD,
                MAIL_FROM=mail_settings.MAIL_FROM,
                MAIL_PORT=mail_settings.MAIL_PORT,
                MAIL_SERVER=mail_settings.MAIL_SERVER,
                MAIL_FROM_NAME=mail_settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=mail_settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=mail_settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=mail_settings.USE_CREDENTIALS,
                VALIDATE_CERTS=mail_settings.VALIDATE_CERTS,
                TEMPLATE_FOLDER=str(TEMPLATE_DIR),
            )
            self._fastmail = FastMail(config)
        return self._fastmail
    
    @property
    def template_env(self) -> Environment:
        """Lazy initialization of Jinja2 template environment"""
        if self._template_env is None:
            self._template_env = Environment(
                loader=FileSystemLoader(str(TEMPLATE_DIR)),
                autoescape=True,
            )
        return self._template_env
    
    def render_template(
        self,
        template_name: str,
        context: dict,
    ) -> str:
        """
        Render an email template with the given context.
        
        This is separated from sending logic for testability and reusability.
        
        Args:
            template_name: Name of the template file (e.g., "mail_placed.html")
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateNotFound: If template file doesn't exist
            Exception: If template rendering fails
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    async def send_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        body: str,
        subtype: MessageType = MessageType.plain,
    ) -> bool:
        """
        Send a plain text or HTML email with retry logic.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            subtype: Message type (plain or html)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        message = MessageSchema(
            recipients=recipients,
            subject=subject,
            body=body,
            subtype=subtype,
        )
        
        return await self._send_with_retry(message)
    
    async def send_email_with_template(
        self,
        recipients: list[EmailStr],
        subject: str,
        template_name: str,
        context: dict,
    ) -> bool:
        """
        Send an email using a template with retry logic.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            template_name: Name of the template file
            context: Dictionary of variables for template rendering
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Render template separately from sending
            html_body = self.render_template(template_name, context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return False
        
        message = MessageSchema(
            recipients=recipients,
            subject=subject,
            body=html_body,
            subtype=MessageType.html,
        )
        
        return await self._send_with_retry(message)
    
    async def _send_with_retry(
        self,
        message: MessageSchema,
    ) -> bool:
        """
        Send email with exponential backoff retry logic.
        
        Args:
            message: MessageSchema to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                await self.fastmail.send_message(message)
                logger.info(
                    f"Email sent successfully to {message.recipients} "
                    f"(attempt {attempt + 1})"
                )
                return True
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Email send attempt {attempt + 1} failed: {e}"
                )
                
                # Don't retry on the last attempt
                if attempt < self._max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = self._retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(
            f"Failed to send email after {self._max_retries} attempts: "
            f"{last_exception}"
        )
        return False
    
    async def close(self):
        """Close mail client connections"""
        if self._fastmail:
            # FastMail doesn't expose a close method, but connections
            # are managed internally and will be cleaned up
            self._fastmail = None
            self._template_env = None


# Singleton instance (optional - can also be instantiated per service)
_mail_client: Optional[MailClient] = None


def get_mail_client() -> MailClient:
    """Get or create singleton mail client instance"""
    global _mail_client
    if _mail_client is None:
        _mail_client = MailClient()
    return _mail_client

