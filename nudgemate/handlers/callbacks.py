from datetime import timedelta
import logging
from aiogram import Router, F, types
from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.utils.time_utils import get_current_time, format_jalali, to_persian_digits
from nudgemate.utils.i18n import t
from nudgemate.services.updater_service import updater_service

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("set_lang:"))
async def cb_set_language(callback: types.CallbackQuery):
    lang = callback.data.split(":")[1]
    await db.set_user_language(callback.from_user.id, lang)
    await callback.answer()
    await callback.message.edit_text(t("lang_changed", lang), parse_mode="Markdown")


@router.callback_query(F.data.startswith("done:"))
async def cb_task_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(task_id)

    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.first_name)
    lang = user.language or "fa"

    if not task:
        err_msg = "این کار پیدا نشد." if lang == "fa" else "Task not found."
        await callback.answer(err_msg, show_alert=True)
        return

    await db.mark_task_completed(task_id)
    alert_msg = "آفرین! کار انجام شد 🎉" if lang == "fa" else "Great job! Task completed 🎉"
    await callback.answer(alert_msg)

    if lang == "fa":
        done_text = (
            f"✅ **انجام شد و بسته شد!**\n\n"
            f"📌 ~~{task.title}~~\n\n"
            f"خسته نباشی قهرمان! 💪"
        )
    else:
        done_text = (
            f"✅ **Completed and closed!**\n\n"
            f"📌 ~~{task.title}~~\n\n"
            f"Well done! 💪"
        )
    try:
        await callback.message.edit_text(done_text, parse_mode="Markdown")
    except Exception:
        pass


@router.callback_query(F.data.startswith("del:"))
async def cb_task_delete(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(task_id)

    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.first_name)
    lang = user.language or "fa"

    if not task:
        await callback.answer("Task not found." if lang == "en" else "کار پیدا نشد.")
        return

    await db.delete_task(task_id)
    await callback.answer("Task deleted." if lang == "en" else "کار حذف شد.")

    del_text = f"🗑 Task **{task.title}** deleted." if lang == "en" else f"🗑 کار **{task.title}** حذف شد."
    try:
        await callback.message.edit_text(del_text, parse_mode="Markdown")
    except Exception:
        pass


@router.callback_query(F.data.startswith("snooze:"))
async def cb_task_snooze(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    task_id = int(parts[1])
    minutes = int(parts[2])

    task = await db.get_task(task_id)
    user = await db.get_or_create_user(callback.from_user.id, callback.from_user.first_name)
    lang = user.language or "fa"

    if not task:
        await callback.answer("Task not found." if lang == "en" else "کار پیدا نشد.")
        return

    now = get_current_time()
    new_dt = now + timedelta(minutes=minutes)
    new_iso = new_dt.strftime("%Y-%m-%dT%H:%M:%S")

    await db.snooze_task(task_id, new_iso)

    if lang == "fa":
        jalali_str = format_jalali(new_iso)
        if minutes == 1440:
            time_label = "فردا همین موقع"
        elif minutes >= 60:
            time_label = f"{minutes // 60} ساعت بعد"
        else:
            time_label = f"{minutes} دقیقه بعد"

        await callback.answer(f"به تعویق افتاد برای {time_label} ⏰")
        snoozed_text = (
            f"⏳ **به تعویق افتاد!**\n\n"
            f"📌 **{task.title}**\n"
            f"⏰ موعد جدید: {jalali_str}\n\n"
            f"سر وقت دوباره صدات می‌کنم! 🔔"
        )
    else:
        if minutes == 1440:
            time_label = "Tomorrow this time"
        elif minutes >= 60:
            time_label = f"{minutes // 60} hour(s) later"
        else:
            time_label = f"{minutes} minutes later"

        await callback.answer(f"Snoozed for {time_label} ⏰")
        snoozed_text = (
            f"⏳ **Snoozed!**\n\n"
            f"📌 **{task.title}**\n"
            f"⏰ New Due: {new_iso}\n\n"
            f"I'll remind you on time! 🔔"
        )

    try:
        await callback.message.edit_text(snoozed_text, parse_mode="Markdown")
    except Exception:
        pass


@router.callback_query(F.data == "run_update")
async def cb_run_update(callback: types.CallbackQuery):
    if callback.from_user.id != settings.ADMIN_CHAT_ID:
        await callback.answer("Admin only.", show_alert=True)
        return

    await callback.answer("Starting update process...")
    await callback.message.edit_text(
        "⏳ **Update in progress...**\n\n"
        "Downloading the latest release from GitHub and restarting service. 🚀",
        parse_mode="Markdown",
    )

    success, message = await updater_service.execute_update()
    if not success:
        await callback.message.answer(f"⚠️ {message}")


@router.callback_query(F.data == "dismiss_update")
async def cb_dismiss_update(callback: types.CallbackQuery):
    await callback.answer("Update dismissed.")
    try:
        await callback.message.delete()
    except Exception:
        pass
