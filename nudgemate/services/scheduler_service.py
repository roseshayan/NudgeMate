import asyncio
import logging
from datetime import datetime, timedelta, timezone
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from nudgemate.config import settings
from nudgemate.database.db import db
from nudgemate.utils.keyboard import get_task_reminder_keyboard
from nudgemate.utils.time_utils import get_current_time, format_jalali, to_persian_digits
from nudgemate.services.updater_service import updater_service
from nudgemate.services.sms_service import sms_service

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(settings.TIMEZONE))
        self.bot: Bot | None = None

    def start(self, bot: Bot):
        self.bot = bot

        # 1. Check for newly due tasks every 30 seconds
        self.scheduler.add_job(
            self._check_due_tasks,
            trigger=IntervalTrigger(seconds=30),
            id="check_due_tasks",
            replace_existing=True,
        )

        # 2. Check for nagging (unconfirmed reminders) every 60 seconds
        self.scheduler.add_job(
            self._check_nagging_tasks,
            trigger=IntervalTrigger(seconds=60),
            id="check_nagging_tasks",
            replace_existing=True,
        )

        # 3. Daily morning briefing
        hour, minute = settings.DAILY_BRIEFING_TIME.split(":")
        self.scheduler.add_job(
            self._send_daily_briefing,
            trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=settings.TIMEZONE),
            id="daily_briefing",
            replace_existing=True,
        )

        # 4. Check for updates on GitHub periodically
        if settings.CHECK_UPDATES:
            self.scheduler.add_job(
                self._check_updates_job,
                trigger=IntervalTrigger(hours=settings.UPDATE_CHECK_INTERVAL_HOURS),
                id="check_updates_job",
                replace_existing=True,
            )

        self.scheduler.start()
        logger.info("Scheduler started successfully.")

    async def _check_due_tasks(self):
        if not self.bot:
            return

        now = get_current_time()
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            tasks = await db.get_due_tasks(iso_now)
            for task in tasks:
                user = await db.get_user(task.user_id)
                lang = user.language if user else "fa"

                if lang == "fa":
                    text = (
                        f"⏰ **وقتشه رفیق!**\n\n"
                        f"📌 **{task.title}**\n"
                        f"🏷 دسته‌بندی: #{task.category}\n"
                        f"⚡️ اولویت: {task.priority}\n\n"
                        f"لطفاً وضعیت کار رو مشخص کن:"
                    )
                else:
                    text = (
                        f"⏰ **Time's up!**\n\n"
                        f"📌 **{task.title}**\n"
                        f"🏷 Category: #{task.category}\n"
                        f"⚡️ Priority: {task.priority}\n\n"
                        f"Please update task status:"
                    )
                keyboard = get_task_reminder_keyboard(task.id, lang)
                try:
                    await self.bot.send_message(
                        chat_id=task.user_id,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )
                    await db.update_nag_status(task.id, nag_count=1, last_nag_at=iso_now)
                    logger.info(f"Sent reminder for task #{task.id} to user {task.user_id}")

                    # Dispatch SMS notification if user has enabled SMS
                    if user and user.sms_enabled and user.phone_number and sms_service.is_configured:
                        time_str = format_jalali(task.remind_at) if lang == "fa" else task.remind_at
                        asyncio.create_task(
                            sms_service.send_reminder_sms(
                                to_phone=user.phone_number,
                                task_title=task.title,
                                due_time=time_str,
                            )
                        )
                except Exception as e:
                    logger.error(f"Failed to send reminder for task #{task.id}: {e}")
        except Exception as e:
            logger.error(f"Error checking due tasks: {e}")

    async def _check_nagging_tasks(self):
        """Re-remind users if they haven't marked the task completed or snoozed."""
        if not self.bot:
            return

        now = get_current_time()
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            tasks = await db.get_tasks_due_for_nagging()
            for task in tasks:
                if not task.last_nag_at:
                    continue

                last_nag = datetime.fromisoformat(task.last_nag_at)
                tz = pytz.timezone(settings.TIMEZONE)
                if last_nag.tzinfo is None:
                    last_nag = tz.localize(last_nag)

                delta = (now - last_nag).total_seconds() / 60.0
                if delta >= settings.NAG_INTERVAL_MINUTES:
                    new_nag_count = task.nag_count + 1
                    user = await db.get_user(task.user_id)
                    lang = user.language if user else "fa"

                    if lang == "fa":
                        nag_badge = to_persian_digits(f"{new_nag_count}/{settings.MAX_NAG_COUNT}")
                        text = (
                            f"⚠️ **یادآوری مجدد ({nag_badge})!**\n\n"
                            f"هنوز به این کارت رسیدگی نکردی رفیق:\n"
                            f"📌 **{task.title}**\n\n"
                            f"انجامش دادی یا به تعویق بندازیمش؟"
                        )
                    else:
                        nag_badge = f"{new_nag_count}/{settings.MAX_NAG_COUNT}"
                        text = (
                            f"⚠️ **Follow-up Reminder ({nag_badge})!**\n\n"
                            f"You haven't resolved this task yet:\n"
                            f"📌 **{task.title}**\n\n"
                            f"Done or snooze for later?"
                        )

                    keyboard = get_task_reminder_keyboard(task.id, lang)
                    try:
                        await self.bot.send_message(
                            chat_id=task.user_id,
                            text=text,
                            reply_markup=keyboard,
                            parse_mode="Markdown",
                        )
                        await db.update_nag_status(task.id, nag_count=new_nag_count, last_nag_at=iso_now)
                        logger.info(f"Nagged task #{task.id} (attempt {new_nag_count}) to user {task.user_id}")
                    except Exception as e:
                        logger.error(f"Failed to nag task #{task.id}: {e}")
        except Exception as e:
            logger.error(f"Error checking nagging tasks: {e}")

    async def _send_daily_briefing(self):
        """Sends daily morning briefing to users."""
        if not self.bot or not settings.DAILY_BRIEFING_ENABLED:
            return

        now = get_current_time()
        today_str = now.strftime("%Y-%m-%d")

        try:
            users = await db.get_all_users()
            for user in users:
                if not user.daily_briefing_enabled:
                    continue

                lang = user.language or "fa"
                tasks = await db.get_user_pending_tasks(user.user_id)
                today_tasks = [
                    t for t in tasks
                    if t.remind_at.startswith(today_str)
                ]

                if not today_tasks:
                    if lang == "fa":
                        msg = (
                            f"☀️ **صبح بخیر {user.first_name}!**\n\n"
                            f"امروز هیچ تسک مشخصی ثبت نشده. روزت رو با آرامش شروع کن! ☕️\n\n"
                            f"اگر کاری پیش اومد، ویس یا متنش رو برام بفرست."
                        )
                    else:
                        msg = (
                            f"☀️ **Good morning {user.first_name}!**\n\n"
                            f"You have no tasks scheduled for today. Have a peaceful day! ☕️\n\n"
                            f"Send me a voice note or message anytime."
                        )
                else:
                    if lang == "fa":
                        lines = [f"☀️ **صبح بخیر {user.first_name}!**\nبرنامه امروز شما:"]
                        for idx, t_item in enumerate(today_tasks, 1):
                            time_str = format_jalali(t_item.remind_at)
                            lines.append(f"{to_persian_digits(idx)}. 📌 **{t_item.title}** ({time_str})")
                        lines.append("\nامروز پر انرژی باش! هر تغییری بود در خدمتم. 🚀")
                    else:
                        lines = [f"☀️ **Good morning {user.first_name}!**\nHere is your schedule for today:"]
                        for idx, t_item in enumerate(today_tasks, 1):
                            lines.append(f"{idx}. 📌 **{t_item.title}** ({t_item.remind_at})")
                        lines.append("\nHave an energetic day! 🚀")
                    msg = "\n".join(lines)

                try:
                    await self.bot.send_message(
                        chat_id=user.user_id,
                        text=msg,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error(f"Failed to send briefing to {user.user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending daily briefing: {e}")

    async def _check_updates_job(self):
        if self.bot:
            await updater_service.check_github_for_updates(self.bot)


scheduler_service = SchedulerService()
