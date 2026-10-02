from aiogram import Router, types
from aiogram.filters import Command
from nudgemate import __version__, __repo__
from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.utils.keyboard import (
    get_single_task_keyboard,
    get_update_notification_keyboard,
    get_language_keyboard,
)
from nudgemate.utils.time_utils import format_jalali, to_persian_digits, format_relative_time
from nudgemate.utils.i18n import t
from nudgemate.services.updater_service import updater_service

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    lang = user.language or "fa"
    welcome_text = t("welcome", lang, name=message.from_user.first_name)
    await message.reply(welcome_text, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    lang = user.language or "fa"
    help_text = t("help", lang, version=__version__)
    repo_link = f"\n\n🔗 GitHub: [NudgeMate Repository]({__repo__})"
    await message.reply(help_text + repo_link, parse_mode="Markdown", disable_web_page_preview=True)


@router.message(Command("lang", "language"))
async def cmd_language(message: types.Message):
    keyboard = get_language_keyboard()
    await message.reply(
        "🌐 لطفاً زبان خود را انتخاب کنید / Please select your language:",
        reply_markup=keyboard,
    )


@router.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    lang = user.language or "fa"
    tasks = await db.get_user_pending_tasks(message.from_user.id)
    if not tasks:
        await message.reply(t("no_pending_tasks", lang))
        return

    header = (
        f"📋 **لیست کارهای معوقه شما ({to_persian_digits(len(tasks))} مورد):**"
        if lang == "fa"
        else f"📋 **Your Pending Tasks ({len(tasks)} items):**"
    )
    await message.reply(header, parse_mode="Markdown")

    for idx, t_item in enumerate(tasks[:10], 1):
        num_str = to_persian_digits(idx) if lang == "fa" else str(idx)
        time_label = format_jalali(t_item.remind_at) if lang == "fa" else t_item.remind_at
        rel_str = format_relative_time(t_item.remind_at)

        if lang == "fa":
            task_msg = (
                f"{num_str}. 📌 **{t_item.title}**\n"
                f"⏰ زمان: {time_label} ({rel_str})\n"
                f"🏷 دسته‌بندی: #{t_item.category} | اولویت: {t_item.priority}"
            )
        else:
            task_msg = (
                f"{num_str}. 📌 **{t_item.title}**\n"
                f"⏰ Time: {time_label} ({rel_str})\n"
                f"🏷 Category: #{t_item.category} | Priority: {t_item.priority}"
            )
        keyboard = get_single_task_keyboard(t_item.id, lang)
        await message.answer(task_msg, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("notes"))
async def cmd_notes(message: types.Message):
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    lang = user.language or "fa"
    notes = await db.get_user_notes(message.from_user.id, limit=10)
    if not notes:
        await message.reply(t("no_notes", lang))
        return

    title_header = "🧠 **یادداشت‌های مغز دوم شما:**\n" if lang == "fa" else "🧠 **Your Second Brain Notes:**\n"
    lines = [title_header]
    for idx, n in enumerate(notes, 1):
        num_str = to_persian_digits(idx) if lang == "fa" else str(idx)
        time_str = format_jalali(n.created_at, include_time=False) if lang == "fa" else n.created_at[:10]
        lines.append(f"{num_str}. 🔹 {n.content} _({time_str})_")

    await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    lang = user.language or "fa"
    stats = await db.get_user_stats(message.from_user.id)

    if lang == "fa":
        text = (
            f"📊 **آمار عملکرد شما در NudgeMate:**\n\n"
            f"⏳ کارهای در انتظار: {to_persian_digits(stats['pending'])}\n"
            f"✅ کارهای تکمیل‌شده: {to_persian_digits(stats['completed'])}\n"
            f"📝 یادداشت‌های ذخیره شده: {to_persian_digits(stats['notes'])}\n\n"
            f"همین‌طوری پرقدرت ادامه بده! 💪"
        )
    else:
        text = (
            f"📊 **Your Productivity Stats on NudgeMate:**\n\n"
            f"⏳ Pending Tasks: {stats['pending']}\n"
            f"✅ Completed Tasks: {stats['completed']}\n"
            f"📝 Saved Notes: {stats['notes']}\n\n"
            f"Keep up the great work! 💪"
        )
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("update"))
async def cmd_update(message: types.Message):
    if message.from_user.id != settings.ADMIN_CHAT_ID:
        await message.reply("⛔️ این دستور فقط مخصوص مدیر ربات است / Admin only.")
        return

    local_sha = updater_service.get_local_commit_sha()
    await message.reply(
        f"🔍 Checking for updates from repository `{settings.GITHUB_REPO}`...\n"
        f"Current commit: `{local_sha[:7]}`",
        parse_mode="Markdown",
    )
    await updater_service.check_github_for_updates(message.bot)
