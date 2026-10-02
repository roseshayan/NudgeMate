from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from nudgemate.utils.time_utils import to_persian_digits


def get_task_reminder_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Keyboard sent with reminder alert containing Done, Snooze, and Cancel."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ انجام شد", callback_data=f"done:{task_id}"),
            InlineKeyboardButton(text="❌ لغو", callback_data=f"del:{task_id}"),
        ],
        [
            InlineKeyboardButton(text="⏳ ۱۰ دقیقه بعد", callback_data=f"snooze:{task_id}:10"),
            InlineKeyboardButton(text="⏳ ۳۰ دقیقه بعد", callback_data=f"snooze:{task_id}:30"),
        ],
        [
            InlineKeyboardButton(text="⏳ ۱ ساعت بعد", callback_data=f"snooze:{task_id}:60"),
            InlineKeyboardButton(text="🔁 فردا همین موقع", callback_data=f"snooze:{task_id}:1440"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_single_task_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Action keyboard for a specific task in /tasks list."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ انجام شد", callback_data=f"done:{task_id}"),
            InlineKeyboardButton(text="⏳ ۱۰ دقیقه بعد", callback_data=f"snooze:{task_id}:10"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"del:{task_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_update_notification_keyboard(version: str) -> InlineKeyboardMarkup:
    """Keyboard sent to admin when a new release/update is detected on GitHub."""
    keyboard = [
        [
            InlineKeyboardButton(text=f"🚀 بروزرسانی به {version}", callback_data="run_update"),
        ],
        [
            InlineKeyboardButton(text="❌ بعداً یادآوری کن", callback_data="dismiss_update"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
