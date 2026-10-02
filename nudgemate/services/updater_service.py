import os
import asyncio
import logging
import subprocess
from pathlib import Path
import aiohttp
from aiogram import Bot

from nudgemate import __version__
from nudgemate.config import settings, BASE_DIR
from nudgemate.utils.keyboard import get_update_notification_keyboard

logger = logging.getLogger(__name__)


class UpdaterService:
    def __init__(self):
        self.repo = settings.GITHUB_REPO
        self.last_known_sha = None
        self._notified_sha = None

    def get_local_commit_sha(self) -> str:
        """Returns the current local git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    async def check_github_for_updates(self, bot: Bot):
        """
        Checks GitHub API for new commits on the main branch.
        If a new commit is detected, sends an alert to the bot admin.
        """
        if not settings.CHECK_UPDATES or not settings.ADMIN_CHAT_ID:
            return

        api_url = f"https://api.github.com/repos/{self.repo}/commits/main"
        headers = {"User-Agent": "NudgeMate-Updater"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        logger.warning(f"GitHub update check failed with status: {resp.status}")
                        return

                    data = await resp.json()
                    remote_sha = data.get("sha", "")
                    commit_message = data.get("commit", {}).get("message", "").split("\n")[0]

                    local_sha = self.get_local_commit_sha()

                    if local_sha != "unknown" and remote_sha and not remote_sha.startswith(local_sha[:7]):
                        if remote_sha != self._notified_sha:
                            self._notified_sha = remote_sha
                            short_sha = remote_sha[:7]
                            msg = (
                                f"🚀 **نسخه جدیدی از NudgeMate منتشر شد!**\n\n"
                                f"🏷 شناسه آخرین نسخه: `{short_sha}`\n"
                                f"📝 پیام تغییرات: {commit_message}\n\n"
                                f"میتونی همین الان با دکمه زیر مستقیماً از تلگرام ربات رو آپدیت کنی، یا در ترمینال سرور دستور زیر رو بزنی:\n"
                                f"`nudgemate-update`"
                            )
                            keyboard = get_update_notification_keyboard(short_sha)
                            await bot.send_message(
                                chat_id=settings.ADMIN_CHAT_ID,
                                text=msg,
                                reply_markup=keyboard,
                                parse_mode="Markdown",
                            )
                            logger.info(f"Update notification sent for commit {short_sha}")
        except Exception as e:
            logger.error(f"Error checking GitHub updates: {e}")

    async def execute_update(self) -> tuple[bool, str]:
        """
        Executes update.sh to pull changes and restart the systemd service.
        """
        update_script = BASE_DIR / "update.sh"
        if not update_script.exists():
            return False, "فایل update.sh پیدا نشد."

        try:
            # Run bash update.sh in background so it can safely restart the systemd service
            proc = await asyncio.create_subprocess_exec(
                "bash",
                str(update_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(BASE_DIR),
            )
            # Give it a couple seconds to start executing
            return True, "دستور بروزرسانی با موفقیت صادر شد. سرویس ظرف چند ثانیه بروزرسانی و مجدداً راه‌اندازی می‌شود."
        except Exception as e:
            logger.error(f"Error triggering update script: {e}")
            return False, f"خطا در اجرای بروزرسانی: {str(e)}"


updater_service = UpdaterService()
