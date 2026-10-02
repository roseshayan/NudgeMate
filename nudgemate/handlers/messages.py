import os
import uuid
import logging
from pathlib import Path
from aiogram import Router, F, types, Bot
from aiogram.enums import ChatAction

from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.services.ai_service import ai_service
from nudgemate.services.voice_service import voice_service
from nudgemate.utils.time_utils import format_jalali, format_relative_time

logger = logging.getLogger(__name__)
router = Router()


async def handle_user_intent(message: types.Message, user_text: str, is_voice: bool = False):
    """Core logic to analyze user text or voice transcript and take appropriate database actions."""
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )
    lang = user.language or "fa"

    # Let user know AI is analyzing
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    analysis = await ai_service.analyze_message(user_text, lang=lang)
    intent = analysis.get("intent", "task")
    title = analysis.get("title", user_text[:80])
    remind_at = analysis.get("remind_at")
    category = analysis.get("category", "general")
    priority = analysis.get("priority", "medium")
    reply_text = analysis.get("reply_text", "ثبت شد!" if lang == "fa" else "Saved!")

    if is_voice:
        voice_prefix = (
            "🎙 *متن پیاده‌شده از ویس شما:*\n_«" + user_text + "»_\n\n"
            if lang == "fa"
            else "🎙 *Voice Transcript:*\n_\"" + user_text + "\"_\n\n"
        )
    else:
        voice_prefix = ""

    if intent == "task":
        if remind_at:
            task_id = await db.create_task(
                user_id=message.from_user.id,
                title=title,
                remind_at=remind_at,
                category=category,
                priority=priority,
            )
            time_display = format_jalali(remind_at) if lang == "fa" else remind_at
            rel_str = format_relative_time(remind_at)
            
            if lang == "fa":
                response = (
                    f"{voice_prefix}"
                    f"✅ **یادآوری با موفقیت تنظیم شد!**\n\n"
                    f"📌 **{title}**\n"
                    f"⏰ زمان موعد: {time_display} ({rel_str})\n"
                    f"🏷 دسته‌بندی: #{category} | اولویت: {priority}\n\n"
                    f"{reply_text}"
                )
            else:
                response = (
                    f"{voice_prefix}"
                    f"✅ **Reminder scheduled successfully!**\n\n"
                    f"📌 **{title}**\n"
                    f"⏰ Due Time: {time_display} ({rel_str})\n"
                    f"🏷 Category: #{category} | Priority: {priority}\n\n"
                    f"{reply_text}"
                )
            await message.reply(response, parse_mode="Markdown")
        else:
            # Task without deadline, save as note
            note_id = await db.create_note(
                user_id=message.from_user.id,
                content=title,
                tags=category,
            )
            if lang == "fa":
                response = (
                    f"{voice_prefix}"
                    f"📝 **کار شما در لیست کارهای عمومی ثبت شد:**\n\n"
                    f"📌 **{title}**\n"
                    f"ℹ️ _زمان مشخصی ذکر نشده بود، بنابراین توی یادداشت‌هات ذخیره کردم تا هر وقت خواستی موعد براش تعیین کنی._\n\n"
                    f"{reply_text}"
                )
            else:
                response = (
                    f"{voice_prefix}"
                    f"📝 **Task added to your general list:**\n\n"
                    f"📌 **{title}**\n"
                    f"ℹ️ _No deadline specified, saved into your notes._\n\n"
                    f"{reply_text}"
                )
            await message.reply(response, parse_mode="Markdown")

    elif intent == "note":
        note_id = await db.create_note(
            user_id=message.from_user.id,
            content=title,
            tags=category,
        )
        if lang == "fa":
            response = (
                f"{voice_prefix}"
                f"🧠 **به حافظه سپرده شد! (مغز دوم)**\n\n"
                f"🔹 {title}\n"
                f"🏷 دسته‌بندی: #{category}\n\n"
                f"{reply_text}"
            )
        else:
            response = (
                f"{voice_prefix}"
                f"🧠 **Saved to Second Brain!**\n\n"
                f"🔹 {title}\n"
                f"🏷 Category: #{category}\n\n"
                f"{reply_text}"
            )
        await message.reply(response, parse_mode="Markdown")

    elif intent == "query":
        tasks = await db.get_user_pending_tasks(message.from_user.id)
        notes = await db.get_user_notes(message.from_user.id, limit=20)
        answer = await ai_service.answer_second_brain_query(user_text, tasks, notes, lang=lang)
        response = f"{voice_prefix}💡 {answer}"
        await message.reply(response, parse_mode="Markdown")

    else:  # chitchat
        await message.reply(f"{voice_prefix}{reply_text}", parse_mode="Markdown")


@router.message(F.voice)
async def handle_voice_message(message: types.Message, bot: Bot):
    """Handles Telegram voice messages, transcribes via faster-whisper, and routes to AI."""
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)

    temp_filename = f"{uuid.uuid4().hex}.ogg"
    temp_path = settings.TEMP_AUDIO_DIR / temp_filename

    try:
        file = await bot.get_file(message.voice.file_id)
        await bot.download_file(file.file_path, destination=temp_path)

        # Transcribe audio
        transcript = await voice_service.transcribe_audio(temp_path)

        if not transcript or len(transcript.strip()) < 2:
            await message.reply("🎙 متاسفانه نتونستم صدای ویس رو واضح تشخیص بدم. لطفاً کمی نزدیک‌تر و واضح‌تر بگو.")
            return

        await handle_user_intent(message, transcript, is_voice=True)

    except Exception as e:
        logger.error(f"Error handling voice message: {e}", exc_info=True)
        await message.reply("⚠️ هنگام پردازش ویس خطایی رخ داد. مطمئن شو پکیج ffmpeg روی سرور نصبه.")
    finally:
        # Cleanup temp file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: types.Message):
    """Handles standard text messages."""
    await handle_user_intent(message, message.text, is_voice=False)
