from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from nudgemate.utils.i18n import t


def get_task_reminder_keyboard(task_id: int, lang: str = "fa") -> InlineKeyboardMarkup:
    """Keyboard sent with reminder alert containing Done, Snooze, and Cancel."""
    keyboard = [
        [
            InlineKeyboardButton(text=t("btn_done", lang), callback_data=f"done:{task_id}"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data=f"del:{task_id}"),
        ],
        [
            InlineKeyboardButton(text=t("btn_snooze_10", lang), callback_data=f"snooze:{task_id}:10"),
            InlineKeyboardButton(text=t("btn_snooze_30", lang), callback_data=f"snooze:{task_id}:30"),
        ],
        [
            InlineKeyboardButton(text=t("btn_snooze_60", lang), callback_data=f"snooze:{task_id}:60"),
            InlineKeyboardButton(text=t("btn_snooze_day", lang), callback_data=f"snooze:{task_id}:1440"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_single_task_keyboard(task_id: int, lang: str = "fa") -> InlineKeyboardMarkup:
    """Action keyboard for a specific task in /tasks list."""
    keyboard = [
        [
            InlineKeyboardButton(text=t("btn_done", lang), callback_data=f"done:{task_id}"),
            InlineKeyboardButton(text=t("btn_snooze_10", lang), callback_data=f"snooze:{task_id}:10"),
            InlineKeyboardButton(text=t("btn_delete", lang), callback_data=f"del:{task_id}"),
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


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting bot language."""
    keyboard = [
        [
            InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="set_lang:fa"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
