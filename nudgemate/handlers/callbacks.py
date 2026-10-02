from datetime import timedelta
import logging
from aiogram import Router, F, types
from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.utils.time_utils import get_current_time, format_jalali, to_persian_digits
from nudgemate.services.updater_service import updater_service

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("done:"))
async def cb_task_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(task_id)

    if not task:
        await callback.answer("این کار پیدا نشد یا قبلاً حذف شده.", show_alert=True)
        return

    await db.mark_task_completed(task_id)
    await callback.answer("آفرین! کار انجام شد 🎉")

    done_text = (
        f"✅ **انجام شد و بسته شد!**\n\n"
        f"📌 ~~{task.title}~~\n\n"
        f"خسته نباشی قهرمان! 💪"
    )
    try:
        await callback.message.edit_text(done_text, parse_mode="Markdown")
    except Exception:
        pass


@router.callback_query(F.data.startswith("del:"))
async def cb_task_delete(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(task_id)

    if not task:
        await callback.answer("کار پیدا نشد.")
        return

    await db.delete_task(task_id)
    await callback.answer("کار حذف شد.")

    del_text = f"🗑 کار **{task.title}** حذف شد."
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
    if not task:
        await callback.answer("کار پیدا نشد.")
        return

    now = get_current_time()
    new_dt = now + timedelta(minutes=minutes)
    new_iso = new_dt.strftime("%Y-%m-%dT%H:%M:%S")

    await db.snooze_task(task_id, new_iso)

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
    try:
        await callback.message.edit_text(snoozed_text, parse_mode="Markdown")
    except Exception:
        pass


@router.callback_query(F.data == "run_update")
async def cb_run_update(callback: types.CallbackQuery):
    if callback.from_user.id != settings.ADMIN_CHAT_ID:
        await callback.answer("فقط مدیر مجاز به بروزرسانی است.", show_alert=True)
        return

    await callback.answer("شروع فرآیند بروزرسانی...")
    await callback.message.edit_text(
        "⏳ **فرآیند دریافت آخرین نسخه از گیت‌هاب و بروزرسانی آغاز شد.**\n\n"
        "سرور ظرف چند لحظه آینده ری‌استارت خواهد شد و پس از بالا آمدن آماده به کار است. 🚀",
        parse_mode="Markdown",
    )

    success, message = await updater_service.execute_update()
    if not success:
        await callback.message.answer(f"⚠️ {message}")


@router.callback_query(F.data == "dismiss_update")
async def cb_dismiss_update(callback: types.CallbackQuery):
    await callback.answer("باشه، بعداً یادآوری می‌کنم.")
    try:
        await callback.message.delete()
    except Exception:
        pass
