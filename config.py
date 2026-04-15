"""
MailBot Configuration
Loads settings from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # SMTP Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

    # IMAP Settings
    IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

    # Email Credentials
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Auto-Reply
    AUTO_REPLY_ENABLED = os.getenv("AUTO_REPLY_ENABLED", "false").lower() == "true"
    AUTO_REPLY_MESSAGE = os.getenv(
        "AUTO_REPLY_MESSAGE",
        "Thank you for your email. I will get back to you soon."
    )

    @classmethod
    def validate(cls):
        """Validate that required configuration is set."""
        errors = []
        if not cls.EMAIL_ADDRESS:
            errors.append("EMAIL_ADDRESS is not set")
        if not cls.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD is not set")
        if errors:
            raise ValueError(
                "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        return True
