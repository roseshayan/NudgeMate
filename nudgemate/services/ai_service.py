import json
import re
import logging
from datetime import datetime
import pytz
from openai import AsyncOpenAI
import jdatetime

from nudgemate.config import settings
from nudgemate.utils.time_utils import get_current_time

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.DAHL_BASE_URL,
            api_key=settings.DAHL_API_KEY,
        )
        self.model = settings.DAHL_MODEL

    def _clean_json_response(self, content: str) -> str:
        """Strips markdown code fences and whitespace from LLM output."""
        cleaned = content.strip()
        # Remove ```json ... ``` or ``` ... ```
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    async def analyze_message(self, user_text: str) -> dict:
        """
        Analyzes user input (voice transcript or text) and returns a structured intent.
        Intents:
          - 'task': Has a reminder time or is an actionable task.
          - 'note': Information to remember (Second Brain), without specific deadline.
          - 'query': Asking about existing tasks or notes (e.g. 'کارهام برای امروز چیه؟').
          - 'chitchat': Greetings or general conversation.
        """
        now = get_current_time()
        tz_name = settings.TIMEZONE
        iso_now = now.strftime("%Y-%m-%dT%H:%M:%S")

        # Shamsi Date for Persian prompt understanding
        jdt = jdatetime.datetime.fromgregorian(datetime=now)
        weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        weekday = weekdays[jdt.weekday()]
        shamsi_str = f"{weekday} {jdt.year}/{jdt.month}/{jdt.day} ساعت {jdt.strftime('%H:%M')}"

        system_prompt = f"""
تو دستیار هوشمند و شخصی به نام NudgeMate هستی؛ یک دستیار مهربان، دقیق و حواس‌جمع برای ثبت تسک‌ها، ریمایندرها و یادداشت‌ها.

اطلاعات زمانی سرور و کاربر:
- زمان فعلی میلادی: {iso_now} (منطقه زمانی: {tz_name})
- زمان فعلی شمسی: {shamsi_str}

وظیفه تو این است که متن کاربر را تحلیل کنی و فقط و فقط یک JSON با ساختار زیر تحویل دهی. هیچ متن اضافی یا توضیحاتی قبل و بعد از JSON ننویس.

ساختار خروجی JSON:
{{
    "intent": "task" | "note" | "query" | "chitchat",
    "title": "عنوان خلاصه و تمیز کار یا یادداشت (به فارسی)",
    "remind_at": "YYYY-MM-DDTHH:MM:SS" یا null (زمان دقیق یادآوری به وقت محلی سرور),
    "category": "work" | "personal" | "health" | "finance" | "shopping" | "general",
    "priority": "low" | "medium" | "high",
    "reply_text": "یک پاسخ کوتاه، پرانرژی و صمیمی به زبان فارسی برای تایید به کاربر"
}}

قوانین حیاتی زمان‌بندی:
۱. اگر کاربر گفت «نیم ساعت دیگه»، ۳۰ دقیقه به زمان فعلی ({iso_now}) اضافه کن.
۲. اگر گفت «فردا ساعت ۴ عصر»، تاریخ فردا با ساعت ۱۶:۰۰:۰۰ را در remind_at بگذار.
۳. اگر گفت «پس‌فردا»، ۲ روز به تاریخ فعلی اضافه کن.
۴. اگر تاریخ شمسی گفت (مثل «۲۵ مهر ساعت ۱۰»)، آن را به تاریخ میلادی متناظر دقیق در فرمت YYYY-MM-DDTHH:MM:SS تبدیل کن.
۵. اگر کار زمان‌دار بود، intent حتماً 'task' و remind_at باید تاریخ دقیق میلادی باشد.
۶. اگر نکته‌ای برای به خاطر سپردن بود اما زمان مشخصی نداشت (مثلاً «یادم باشه رمز گاوصندوق اینه» یا «ماشین رو کوچه سوم پارک کردم»)، intent را 'note' بگذار و remind_at را null قرار بده.
۷. اگر سوالی در مورد کارها یا یادداشت‌ها پرسید (مثل «کارهای امروزم چیه؟» یا «ماشینم کجاست؟»)، intent را 'query' بگذار.
۸. اگر فقط احوال‌پرسی یا گپ بود، intent را 'chitchat' بگذار.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.1,
            )

            raw_text = response.choices[0].message.content or ""
            cleaned = self._clean_json_response(raw_text)

            data = json.loads(cleaned)
            return data

        except Exception as e:
            logger.error(f"Error in Dahl AI analysis: {e}", exc_info=True)
            # Fallback response
            return {
                "intent": "task",
                "title": user_text[:50],
                "remind_at": None,
                "category": "general",
                "priority": "medium",
                "reply_text": "پیامت رو ثبت کردم رفیق!",
            }

    async def answer_second_brain_query(self, user_query: str, tasks: list, notes: list) -> str:
        """
        Synthesizes an intelligent answer for user queries using their saved tasks and notes.
        """
        now = get_current_time()
        context_lines = []
        
        if tasks:
            context_lines.append("تسک‌ها و برنامه‌های ثبت شده:")
            for t in tasks:
                context_lines.append(f"- {t.title} (زمان: {t.remind_at}, وضعیت: {t.status})")
        
        if notes:
            context_lines.append("\nیادداشت‌ها و حافظه ذخیره شده:")
            for n in notes:
                context_lines.append(f"- {n.content} (تاریخ: {n.created_at})")

        context_text = "\n".join(context_lines) if context_lines else "هیچ اطلاعاتی یافت نشد."

        prompt = f"""
تو NudgeMate هستی. کاربر سوالی درباره برنامه‌ها، کارها یا یادداشت‌های گذشته‌اش پرسیده است.
بر اساس اطلاعات موجود زیر، با لحنی صمیمی، کوتاه و دقیق پاسخ بده.

اطلاعات موجود کاربر:
{context_text}

سوال کاربر: {user_query}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "تو دستیار هوشمند و صمیمی NudgeMate هستی."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content or "پاسخی پیدا نشد."
        except Exception as e:
            logger.error(f"Error querying second brain: {e}")
            return "متاسفانه نتونستم حافظه رو جستجو کنم، ولی تسک‌هات توی دیتابیس محفوظه."


ai_service = AIService()
