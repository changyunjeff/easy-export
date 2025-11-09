from __future__ import annotations

from .client import EmailClient, send_email, get_email_client
from .connection import init_email, close_email, is_email_enabled, EmailClient as SMTPClient

__all__ = [
    'EmailClient',
    'SMTPClient',
    'send_email',
    'get_email_client',
    'init_email',
    'close_email',
    'is_email_enabled',
]

