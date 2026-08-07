from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def home_keyboard(connected: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📚 Commands", callback_data="home:commands")]]
    if connected:
        rows = [
            [InlineKeyboardButton(text="📦 Modules", callback_data="home:modules"), InlineKeyboardButton(text="⚙️ Settings", callback_data="home:settings")],
            [InlineKeyboardButton(text="🤖 AI", callback_data="home:ai"), InlineKeyboardButton(text="📊 Stats", callback_data="home:stats")],
            [InlineKeyboardButton(text="🔌 Disconnect", callback_data="logout:ask")],
        ]
    else:
        rows = [[InlineKeyboardButton(text="🔗 Connect Telegram", callback_data="auth:start")], [InlineKeyboardButton(text="📚 Features", callback_data="home:commands")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="auth:cancel")]])


def qr_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Enter phone code instead", callback_data="auth:phone")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="auth:cancel")],
    ])


def disconnect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Disconnect from service", callback_data="logout:forget")],
        [InlineKeyboardButton(text="End Telegram session", callback_data="logout:terminate")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="home:main")],
    ])
