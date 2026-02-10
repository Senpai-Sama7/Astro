"""
Channel integrations for ASTRO.

Currently supports Telegram. WhatsApp support can be added.
"""

from .telegram_bot import TelegramBot

__all__ = ['TelegramBot']
