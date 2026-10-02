import logging
import aiohttp
from typing import Optional, Tuple
from nudgemate.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    BASE_URL = "https://console.melipayamak.com/api"

    @property
    def is_configured(self) -> bool:
        return bool(settings.MELIPAYAMAK_API_TOKEN)

    async def get_credit(self) -> Optional[float]:
        """Fetches current SMS account balance in Rials."""
        if not self.is_configured:
            return None
        url = f"{self.BASE_URL}/receive/credit/{settings.MELIPAYAMAK_API_TOKEN}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return float(data.get("amount", 0))
        except Exception as e:
            logger.warning(f"Failed to fetch MeliPayamak credit: {e}")
        return None

    async def send_reminder_sms(
        self,
        to_phone: str,
        task_title: str,
        due_time: str,
    ) -> Tuple[bool, str]:
        """
        Sends an SMS reminder to user mobile number via MeliPayamak console API.
        Supports both shared service line (pattern/bodyId) and simple SMS.
        """
        if not self.is_configured:
            return False, "سرویس پیامک در فایل تنظیمات فعال نشده است."

        # Clean phone number (e.g. +989123456789 -> 09123456789)
        phone = to_phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+98"):
            phone = "0" + phone[3:]
        elif phone.startswith("0098"):
            phone = "0" + phone[4:]
        elif phone.startswith("98"):
            phone = "0" + phone[2:]

        if not phone.startswith("09") or len(phone) != 11:
            return False, "شماره موبایل وارد شده معتبر نیست (باید با ۰۹ شروع شود و ۱۱ رقم باشد)."

        try:
            async with aiohttp.ClientSession() as session:
                # Option A: Shared Pattern / Service Line (Recommended for bypassing blacklist)
                if settings.MELIPAYAMAK_SHARED_BODY_ID > 0:
                    url = f"{self.BASE_URL}/send/shared/{settings.MELIPAYAMAK_API_TOKEN}"
                    payload = {
                        "bodyId": settings.MELIPAYAMAK_SHARED_BODY_ID,
                        "to": phone,
                        "args": [task_title[:40], due_time],
                    }
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        res_json = await resp.json()
                        if resp.status == 200 and "recId" in res_json:
                            logger.info(f"Shared pattern SMS sent to {phone}, recId={res_json.get('recId')}")
                            return True, "پیامک با موفقیت ارسال شد."
                        else:
                            err_desc = res_json.get("status", "خطای ارسال الگو")
                            logger.warning(f"Shared SMS failed: {err_desc}")
                            return False, str(err_desc)

                # Option B: Simple SMS
                url = f"{self.BASE_URL}/send/simple/{settings.MELIPAYAMAK_API_TOKEN}"
                from_num = settings.MELIPAYAMAK_FROM_NUMBER or "50004001"
                sms_text = (
                    f"یادآوری NudgeMate:\n"
                    f"📌 {task_title}\n"
                    f"⏰ موعد: {due_time}\n"
                    f"🤖 ربات دستیار شخصی شما"
                )
                payload = {
                    "from": from_num,
                    "to": phone,
                    "text": sms_text,
                }
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    res_json = await resp.json()
                    if resp.status == 200 and "recId" in res_json:
                        logger.info(f"Simple SMS sent to {phone}, recId={res_json.get('recId')}")
                        return True, "پیامک با موفقیت ارسال شد."
                    else:
                        err_desc = res_json.get("status", "خطای ارسال پیامک")
                        logger.warning(f"Simple SMS failed: {err_desc}")
                        return False, str(err_desc)

        except Exception as e:
            logger.error(f"Error sending SMS via MeliPayamak: {e}", exc_info=True)
            return False, f"خطای شبکه در ارسال پیامک: {e}"


sms_service = SMSService()
