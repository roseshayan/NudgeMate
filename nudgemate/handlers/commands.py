from aiogram import Router, types
from aiogram.filters import Command
from nudgemate import __version__, __repo__
from nudgemate.config import settings, update_env_variable
from nudgemate.database.db import db
from nudgemate.utils.keyboard import (
    get_single_task_keyboard,
    get_update_notification_keyboard,
    get_language_keyboard,
    get_sms_keyboard,
)
from nudgemate.utils.time_utils import format_jalali, to_persian_digits, format_relative_time
from nudgemate.utils.i18n import t
from nudgemate.services.updater_service import updater_service
from nudgemate.services.sms_service import sms_service

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
    if message.from_user.id == settings.ADMIN_CHAT_ID:
        admin_hint = (
            "\n\n⚙️ **دستورات مدیریت ادمین:**\n"
            "▫️ `/admin` : پنل تنظیمات توکن پیامک، کانال و اعتبار\n"
            "▫️ `/update` : بررسی و اجرای آپدیت سورس"
            if lang == "fa"
            else
            "\n\n⚙️ **Admin Commands:**\n"
            "▫️ `/admin` : Settings panel & tokens\n"
            "▫️ `/update` : Trigger source update"
        )
        help_text += admin_hint

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


@router.message(Command("admin"))
@router.message(Command("settings"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != settings.ADMIN_CHAT_ID:
        await message.reply("⛔️ این دستور فقط مخصوص مدیر ربات است / Admin only.")
        return

    credit = await sms_service.get_credit()
    credit_str = f"{credit:,.0f} ریال" if credit is not None else "⚠️ توکن نامعتبر یا خطا در ارتباط"
    token_masked = (
        settings.MELIPAYAMAK_API_TOKEN[:6] + "..." + settings.MELIPAYAMAK_API_TOKEN[-4:]
        if len(settings.MELIPAYAMAK_API_TOKEN) > 10
        else (settings.MELIPAYAMAK_API_TOKEN or "تنظیم نشده")
    )
    chan_str = settings.REQUIRED_CHANNEL if settings.REQUIRED_CHANNEL else "غیرفعال (آزاد برای همه)"

    text = (
        f"⚙️ **پنل مدیریت و تنظیمات NudgeMate:**\n\n"
        f"📱 **توکن ملی‌پیامک:** `{token_masked}`\n"
        f"💰 **اعتبار زنده پنل:** `{credit_str}`\n"
        f"📢 **کانال عضویت اجباری:** `{chan_str}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🛠 **دستورات مدیریت تنظیمات (بدون نیاز به سرور):**\n\n"
        f"▫️ **تنظیم توکن ملی‌پیامک:**\n"
        f"`/set_sms_token <apitoken>`\n\n"
        f"▫️ **تنظیم کانال عضویت اجباری:**\n"
        f"`/set_channel @MyChannel` یا `/set_channel off`\n\n"
        f"▫️ **استعلام زنده موجودی پیامک:**\n"
        f"`/sms_credit`\n\n"
        f"▫️ **بررسی و اجرای آپدیت سرور:**\n"
        f"`/update`"
    )
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("set_sms_token"))
async def cmd_set_sms_token(message: types.Message):
    if message.from_user.id != settings.ADMIN_CHAT_ID:
        await message.reply("⛔️ این دستور فقط مخصوص مدیر ربات است / Admin only.")
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.reply(
            "ℹ️ لطفاً توکن API ملی‌پیامک را همراه با دستور ارسال کنید.\n"
            "مثال:\n`/set_sms_token 0cd932c7f08946509b95519513bbc4be`",
            parse_mode="Markdown",
        )
        return

    new_token = parts[1].strip()
    settings.MELIPAYAMAK_API_TOKEN = new_token
    update_env_variable("MELIPAYAMAK_API_TOKEN", new_token)

    # Live test token
    credit = await sms_service.get_credit()
    if credit is not None:
        await message.reply(
            f"✅ **توکن ملی‌پیامک با موفقیت ذخیره و در .env ست شد!**\n\n"
            f"💰 اعتبار فعال حساب شما: `{credit:,.0f} ریال`\n"
            f"از این پس یادآوری‌های پیامکی با این توکن ارسال خواهند شد.",
            parse_mode="Markdown",
        )
    else:
        await message.reply(
            f"⚠️ **توکن در فایل .env ذخیره شد، اما اتصال به ملی‌پیامک برقرار نشد.**\n\n"
            f"لطفاً مطمئن شوید توکن کنسول ملی‌پیامک صحیح است.",
            parse_mode="Markdown",
        )


@router.message(Command("set_channel"))
async def cmd_set_channel(message: types.Message):
    if message.from_user.id != settings.ADMIN_CHAT_ID:
        await message.reply("⛔️ این دستور فقط مخصوص مدیر ربات است / Admin only.")
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        cur_chan = settings.REQUIRED_CHANNEL or "غیرفعال"
        await message.reply(
            f"📢 **تنظیم کانال عضویت اجباری:**\n\n"
            f"کانال فعلی: `{cur_chan}`\n\n"
            f"برای تغییر کانال:\n`/set_channel @MyChannel`\n\n"
            f"برای غیرفعال کردن عضویت اجباری:\n`/set_channel off`",
            parse_mode="Markdown",
        )
        return

    chan_input = parts[1].strip()
    if chan_input.lower() in ("off", "none", "disable", "حذف", "غیرفعال"):
        settings.REQUIRED_CHANNEL = ""
        update_env_variable("REQUIRED_CHANNEL", "")
        await message.reply("✅ عضویت اجباری در کانال غیرفعال شد.", parse_mode="Markdown")
        return

    if not chan_input.startswith("@") and not chan_input.startswith("-100") and not chan_input.startswith("-"):
        chan_input = f"@{chan_input}"

    settings.REQUIRED_CHANNEL = chan_input
    update_env_variable("REQUIRED_CHANNEL", chan_input)
    await message.reply(
        f"✅ **کانال عضویت اجباری با موفقیت به `{chan_input}` تغییر یافت و در .env ذخیره شد!**",
        parse_mode="Markdown",
    )


@router.message(Command("sms_credit"))
async def cmd_sms_credit(message: types.Message):
    if message.from_user.id != settings.ADMIN_CHAT_ID:
        await message.reply("⛔️ این دستور فقط مخصوص مدیر ربات است / Admin only.")
        return

    credit = await sms_service.get_credit()
    if credit is not None:
        await message.reply(
            f"💰 **استعلام زنده اعتبار ملی‌پیامک:**\n\n"
            f"اعتبار کیف پول: `{credit:,.0f} ریال`\n"
            f"وضعیت اتصال: متصل و فعال ✅",
            parse_mode="Markdown",
        )
    else:
        await message.reply(
            f"❌ **خطا در دریافت اعتبار ملی‌پیامک!**\n\n"
            f"توکن API یا اینترنت سرور به سرور ملی‌پیامک را بررسی کنید.\n"
            f"تنظیم توکن با دستور: `/set_sms_token <توکن>`",
            parse_mode="Markdown",
        )


@router.message(Command("phone"))
async def cmd_phone(message: types.Message):
    user = await db.get_or_create_user(message.from_user.id, message.from_user.first_name)
    lang = user.language or "fa"

    parts = message.text.strip().split()
    if len(parts) < 2:
        cur_phone = user.phone_number or ("ثبت نشده" if lang == "fa" else "Not set")
        guide = (
            f"📱 **تنظیم شماره موبایل برای یادآوری پیامکی:**\n\n"
            f"شماره فعلی شما: `{cur_phone}`\n\n"
            f"برای ثبت یا تغییر شماره موبایل، دستور را به همراه شماره خود ارسال کنید:\n"
            f"`/phone 09123456789`"
            if lang == "fa"
            else
            f"📱 **Set Phone Number for SMS Reminders:**\n\n"
            f"Current Phone: `{cur_phone}`\n\n"
            f"Usage:\n`/phone 09123456789`"
        )
        await message.reply(guide, parse_mode="Markdown")
        return

    raw_phone = parts[1].strip()
    phone = raw_phone.replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("98"):
        phone = "0" + phone[2:]

    if not phone.startswith("09") or len(phone) != 11 or not phone.isdigit():
        err = (
            "❌ شماره موبایل نامعتبر است! شماره باید ۱۱ رقم بوده و با ۰۹ شروع شود.\nمثال: `/phone 09123456789`"
            if lang == "fa"
            else "❌ Invalid phone number! Must be 11 digits starting with 09.\nExample: `/phone 09123456789`"
        )
        await message.reply(err, parse_mode="Markdown")
        return

    await db.set_user_phone(message.from_user.id, phone)
    await db.set_user_sms_enabled(message.from_user.id, True)

    success_msg = (
        f"✅ **شماره موبایل شما با موفقیت ثبت و پیامک فعال شد!**\n\n"
        f"📞 شماره: `{phone}`\n\n"
        f"از این پس هنگام فرا رسیدن موعد کارهایتان، علاوه بر تلگرام، یک پیامک هشدار فوری نیز دریافت خواهید کرد. 🔔\n\n"
        f"برای مدیریت پیامک‌ها دستور /sms را ارسال کنید."
        if lang == "fa"
        else
        f"✅ **Phone number saved and SMS reminders enabled!**\n\n"
        f"📞 Phone: `{phone}`\n\n"
        f"You will now receive SMS alerts when your tasks are due. 🔔"
    )
    await message.reply(success_msg, parse_mode="Markdown")


@router.message(Command("sms"))
async def cmd_sms(message: types.Message):
    await send_sms_settings_panel(message, message.from_user.id, edit=False)


async def send_sms_settings_panel(message: types.Message, user_id: int, edit: bool = False):
    user = await db.get_user(user_id)
    first_name = message.from_user.first_name if message.from_user else ""
    if not user:
        user = await db.get_or_create_user(user_id, first_name)
    lang = user.language or "fa"

    status_str = "فعال ✅" if user.sms_enabled else "غیرفعال ❌"
    phone_str = user.phone_number if user.phone_number else "ثبت نشده"

    text = (
        f"📱 **تنظیمات یادآوری پیامکی (SMS Reminders):**\n\n"
        f"وضعیت ارسال پیامک: **{status_str}**\n"
        f"شماره موبایل: `{phone_str}`\n\n"
        f"ℹ️ با فعال بودن این قابلیت، اگر در زمان موعد کارت به تلگرام دسترسی نداشته باشی یا اینترنتت قطع باشه، یک پیامک هشدار برات ارسال میشه! 🚀\n\n"
        f"💡 **برای ثبت یا تغییر شماره موبایل:**\n"
        f"دستور `/phone 09123456789` را ارسال کن.\n\n"
        f"🎁 **تخفیف ویژه ملی‌پیامک:** ۱۰٪ تخفیف خرید پنل با کد `MPDBMRN`"
        if lang == "fa"
        else
        f"📱 **SMS Reminder Settings:**\n\n"
        f"SMS Status: **{'Active ✅' if user.sms_enabled else 'Disabled ❌'}**\n"
        f"Phone Number: `{user.phone_number or 'Not set'}`\n\n"
        f"To change phone number send: `/phone 09123456789`\n\n"
        f"🎁 **MeliPayamak Discount:** 10% off with coupon `MPDBMRN`"
    )

    keyboard = get_sms_keyboard(user.sms_enabled, bool(user.phone_number), lang)
    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
