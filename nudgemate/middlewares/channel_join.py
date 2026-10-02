import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject, InlineKeyboardMarkup, InlineKeyboardButton

from nudgemate.config import settings

logger = logging.getLogger(__name__)


class ChannelJoinMiddleware(BaseMiddleware):
    """
    Middleware to enforce mandatory channel membership before using the bot.
    Can be configured via REQUIRED_CHANNEL and CHANNEL_INVITE_LINK in .env.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # If no channel is configured, bypass check
        if not settings.REQUIRED_CHANNEL:
            return await handler(event, data)

        bot: Bot = data.get("bot")
        user = getattr(event, "from_user", None)
        if not user or not bot:
            return await handler(event, data)

        # Admin bypasses force join
        if settings.ADMIN_CHAT_ID and user.id == settings.ADMIN_CHAT_ID:
            return await handler(event, data)

        # Allow the verification callback to pass through
        if isinstance(event, CallbackQuery) and event.data == "check_channel_join":
            return await handler(event, data)

        # Check membership in the required channel
        try:
            member = await bot.get_chat_member(
                chat_id=settings.REQUIRED_CHANNEL,
                user_id=user.id,
            )
            # Allowed statuses
            if member.status in ("creator", "administrator", "member", "restricted"):
                return await handler(event, data)
        except Exception as e:
            logger.warning(f"Could not check channel membership for user {user.id}: {e}")
            # If bot is not admin in channel or channel not found, don't block user
            return await handler(event, data)

        # User is not a member -> Prompt to join
        channel_ref = settings.REQUIRED_CHANNEL.replace("@", "")
        invite_url = settings.CHANNEL_INVITE_LINK or f"https://t.me/{channel_ref}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📢 عضویت در کانال", url=invite_url),
                ],
                [
                    InlineKeyboardButton(text="🔄 بررسی مجدد عضویت", callback_data="check_channel_join"),
                ],
            ]
        )

        join_msg = (
            f"👋 **سلام {user.first_name} عزیز!**\n\n"
            f"برای استفاده از ربات هوشمند NudgeMate و فعال‌سازی قابلیت‌های صوتی و یادآور، "
            f"لطفاً ابتدا در کانال رسمی ما عضو شوید و سپس دکمه **بررسی مجدد عضویت** را لمس کنید 👇"
        )

        if isinstance(event, Message):
            await event.answer(join_msg, reply_markup=keyboard, parse_mode="Markdown")
        elif isinstance(event, CallbackQuery):
            await event.message.answer(join_msg, reply_markup=keyboard, parse_mode="Markdown")
            await event.answer()

        return None
