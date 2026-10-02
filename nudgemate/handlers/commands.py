from aiogram import Router, types
from aiogram.filters import Command
from nudgemate import __version__, __repo__
from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.utils.keyboard import get_single_task_keyboard, get_update_notification_keyboard
from nudgemate.utils.time_utils import format_jalali, to_persian_digits, format_relative_time
from nudgemate.services.updater_service import updater_service

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )

    welcome_text = (
        f"سلام {message.from_user.first_name} عزیز! 👋\n"
        f"من **NudgeMate** هستم؛ دستیار هوشمند، حواس‌جمع و سمج تو برای یادآوری کارها و یادداشت‌ها. 🤖\n\n"
        f"**چطور با من کار کنی؟ خیلی راحته!**\n"
        f"🎙 فقط کافیه یه **ویس** برام بفرستی، یا تایپ کنی:\n"
        f"• «فردا ساعت ۴ عصر با دکتر قرار دارم»\n"
        f"• «نیم ساعت دیگه زیر گازو خاموش کن»\n"
        f"• «یادم باشه شماره پرونده بیمه فلان است»\n\n"
        f"من خودکار تاریخ و ساعت رو می‌فهمم، سر وقت بهت خبر می‌دم، و اگه حواست نبود اون‌قدر پیگیری می‌کنم تا خیالم راحت بشه انجامش دادی! 😎\n\n"
        f"دستورات مفید:\n"
        f"📋 /tasks - مشاهده لیست کارهای باز\n"
        f"📝 /notes - مشاهده یادداشت‌ها (مغز دوم)\n"
        f"☀️ /briefing - دریافت گزارش روزانه همین الان\n"
        f"📊 /stats - آمار عملکرد شما\n"
        f"ℹ️ /help - راهنمای جامع\n"
    )
    await message.reply(welcome_text, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        f"📖 **راهنمای استفاده از NudgeMate (نسخه {__version__})**\n\n"
        f"۱. **ارسال صوتی (Voice):**\n"
        f"در حال رانندگی یا پیاده‌روی هستی؟ دکمه ضبط ویس رو نگه دار و به زبان عامیانه کار یا قرارت رو بگو. من برات تبدیل به تسک می‌کنم.\n\n"
        f"۲. **سیستم پیگیری سمج (Nagging):**\n"
        f"وقتی موعد کارت برسه، برات پیام میاد با دکمه‌های [انجام شد]، [ساعت بعد] یا [فردا]. اگه جواب ندی، من هر ۱۵ دقیقه یک‌بار بهت تلنگر می‌زنم تا فراموش نکنی!\n\n"
        f"۳. **مغز دوم (Second Brain):**\n"
        f"هر نکته‌ای که خواستی یادت بمونه (مثل جای وسایل، شماره‌ها و...) بگو «یادم باشه...». بعداً می‌تونی بپرسی «فلان چیز کجاست؟» تا جوابت رو بدم.\n\n"
        f"۴. **بروزرسانی ربات:**\n"
        f"در صورت انتشار نسخه جدید در گیت‌هاب، ادمین اعلان دریافت می‌کنه و با یک کلیک یا دستور /update ربات آپدیت میشه.\n\n"
        f"🔗 ریپازیتوری پروژه: [GitHub NudgeMate]({__repo__})"
    )
    await message.reply(help_text, parse_mode="Markdown", disable_web_page_preview=True)


@router.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    tasks = await db.get_user_pending_tasks(message.from_user.id)
    if not tasks:
        await message.reply("🎉 هیچ کار معوقه‌ای نداری رفیق! همه چی عالی و مرتبه.")
        return

    await message.reply(f"📋 **لیست کارهای معوقه شما ({to_persian_digits(len(tasks))} مورد):**", parse_mode="Markdown")

    for idx, t in enumerate(tasks[:10], 1):
        jalali_str = format_jalali(t.remind_at)
        rel_str = format_relative_time(t.remind_at)
        task_msg = (
            f"{to_persian_digits(idx)}. 📌 **{t.title}**\n"
            f"⏰ زمان: {jalali_str} ({rel_str})\n"
            f"🏷 دسته‌بندی: #{t.category} | اولویت: {t.priority}"
        )
        keyboard = get_single_task_keyboard(t.id)
        await message.answer(task_msg, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("notes"))
async def cmd_notes(message: types.Message):
    notes = await db.get_user_notes(message.from_user.id, limit=10)
    if not notes:
        await message.reply("📝 هنوز هیچ یادداشتی توی حافظه‌ام ثبت نکردی.")
        return

    lines = ["🧠 **یادداشت‌های مغز دوم شما:**\n"]
    for idx, n in enumerate(notes, 1):
        jalali_str = format_jalali(n.created_at, include_time=False)
        lines.append(f"{to_persian_digits(idx)}. 🔹 {n.content} _({jalali_str})_")

    await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    stats = await db.get_user_stats(message.from_user.id)
    text = (
        f"📊 **آمار عملکرد شما در NudgeMate:**\n\n"
        f"⏳ کارهای در انتظار: {to_persian_digits(stats['pending'])}\n"
        f"✅ کارهای تکمیل‌شده: {to_persian_digits(stats['completed'])}\n"
        f"📝 یادداشت‌های ذخیره شده: {to_persian_digits(stats['notes'])}\n\n"
        f"همین‌طوری پرقدرت ادامه بده! 💪"
    )
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("update"))
async def cmd_update(message: types.Message):
    if message.from_user.id != settings.ADMIN_CHAT_ID:
        await message.reply("⛔️ این دستور فقط مخصوص مدیر ربات است.")
        return

    local_sha = updater_service.get_local_commit_sha()
    await message.reply(
        f"🔍 در حال بررسی بروزرسانی از مخزن گیت‌هاب `{settings.GITHUB_REPO}`...\n"
        f"شناسه نسخه فعلی شما: `{local_sha[:7]}`",
        parse_mode="Markdown",
    )
    await updater_service.check_github_for_updates(message.bot)
