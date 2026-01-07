"""
Celery task queue for background task processing.

This module provides Celery tasks for email and SMS sending,
replacing FastAPI BackgroundTasks with a distributed, persistent task queue.
"""
import logging
from asgiref.sync import async_to_sync
from celery import Celery
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from twilio.rest import Client as TwilioClient

from app.config import db_settings, mail_settings, twilio_settings
from app.utils import TEMPLATE_DIR

logger = logging.getLogger(__name__)

# Create FastMail instance for Celery tasks
# Note: Celery tasks must be synchronous, so we use async_to_sync wrapper
_fastmail_instance = None


def get_fastmail():
    """Get or create FastMail instance (singleton)"""
    global _fastmail_instance
    if _fastmail_instance is None:
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
        _fastmail_instance = FastMail(config)
    return _fastmail_instance


# Convert async send_message to sync for Celery
def send_message_sync(message: MessageSchema, template_name: str | None = None):
    """Synchronous wrapper for FastMail send_message"""
    fastmail = get_fastmail()
    send_message = async_to_sync(fastmail.send_message)
    return send_message(message, template_name=template_name)


# Create Twilio client (if configured)
_twilio_client = None


def get_twilio_client():
    """Get or create Twilio client (singleton)"""
    global _twilio_client
    if _twilio_client is None and twilio_settings.TWILIO_SID:
        _twilio_client = TwilioClient(
            twilio_settings.TWILIO_SID,
            twilio_settings.TWILIO_AUTH_TOKEN,
        )
    return _twilio_client


# Create Celery app
celery_app = Celery(
    "fastship_tasks",
    broker=db_settings.REDIS_URL,
    backend=db_settings.REDIS_URL,
    broker_connection_retry_on_startup=True,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_mail_task(
    self,
    recipients: list[str],
    subject: str,
    body: str,
):
    """
    Send plain text email via Celery.
    
    Args:
        recipients: List of email addresses
        subject: Email subject
        body: Plain text email body
        
    Returns:
        str: Success message
    """
    try:
        send_message_sync(
            message=MessageSchema(
                recipients=recipients,
                subject=subject,
                body=body,
                subtype=MessageType.plain,
            ),
        )
        logger.info(f"Email sent successfully to {recipients}")
        return "Message sent successfully"
    except Exception as exc:
        logger.error(f"Failed to send email to {recipients}: {exc}", exc_info=True)
        # Retry on failure (up to max_retries)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_with_template_task(
    self,
    recipients: list[str],
    subject: str,
    context: dict,
    template_name: str,
):
    """
    Send HTML email with template via Celery.
    
    Args:
        recipients: List of email addresses
        subject: Email subject
        context: Template context variables
        template_name: Name of the template file (e.g., "mail_placed.html")
        
    Returns:
        str: Success message
    """
    try:
        send_message_sync(
            message=MessageSchema(
                recipients=recipients,
                subject=subject,
                template_body=context,
                subtype=MessageType.html,
            ),
            template_name=template_name,
        )
        logger.info(f"Template email sent successfully to {recipients} using {template_name}")
        return "Email sent successfully"
    except Exception as exc:
        logger.error(
            f"Failed to send template email to {recipients} using {template_name}: {exc}",
            exc_info=True,
        )
        # Retry on failure (up to max_retries)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(
    self,
    to: str,
    body: str,
):
    """
    Send SMS via Celery using Twilio.
    
    Args:
        to: Phone number to send SMS to
        body: SMS message body
        
    Returns:
        str: Success message or error message if Twilio not configured
    """
    twilio_client = get_twilio_client()
    if not twilio_client:
        logger.warning("Twilio not configured, skipping SMS")
        return "Twilio not configured"
    
    try:
        message = twilio_client.messages.create(
            from_=twilio_settings.TWILIO_NUMBER,
            to=to,
            body=body,
        )
        logger.info(f"SMS sent successfully to {to}: {message.sid}")
        return f"SMS sent successfully: {message.sid}"
    except Exception as exc:
        logger.error(f"Failed to send SMS to {to}: {exc}", exc_info=True)
        # Retry on failure (up to max_retries)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

