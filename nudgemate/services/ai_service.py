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

    async def analyze_message(self, user_text: str, lang: str = "fa") -> dict:
        """
        Analyzes user input (voice transcript or text) and returns a structured intent.
        Intents:
          - 'task': Has a reminder time or is an actionable task.
          - 'note': Information to remember (Second Brain), without specific deadline.
          - 'query': Asking about existing tasks or notes.
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

        lang_instruction = (
            "Response language: Persian (فارسی). Output title and reply_text in Persian."
            if lang == "fa"
            else "Response language: English. Output title and reply_text in English."
        )

        system_prompt = f"""
You are NudgeMate, a smart, friendly, and attentive personal task reminder and second brain assistant.

Server Time Information:
- Current ISO Time: {iso_now} (Timezone: {tz_name})
- Current Persian (Jalali) Time: {shamsi_str}

Language Instruction: {lang_instruction}

Analyze the user's input and output ONLY a valid JSON object matching the schema below:
{{
    "intent": "task" | "note" | "query" | "chitchat",
    "title": "Clean, concise title of the task or note",
    "remind_at": "YYYY-MM-DDTHH:MM:SS" or null (exact reminder datetime in server local time),
    "category": "work" | "personal" | "health" | "finance" | "shopping" | "general",
    "priority": "low" | "medium" | "high",
    "reply_text": "A brief, warm confirmation or reply message to the user"
}}

Rules:
1. Relative times ("in 30 minutes", "نیم ساعت دیگه") -> add to current time {iso_now}.
2. "Tomorrow at 4 PM" / "فردا ساعت ۴ عصر" -> calculate exact tomorrow date at 16:00:00.
3. Jalali dates like "۲۵ مهر ساعت ۱۰" -> convert to equivalent Gregorian ISO format in remind_at.
4. Memos/facts to remember without specific time -> intent='note', remind_at=null.
5. Questions about past notes/tasks -> intent='query'.
6. Greetings -> intent='chitchat'.
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
            fallback_reply = "پیامت رو ثبت کردم رفیق!" if lang == "fa" else "Got your message, saved!"
            return {
                "intent": "task",
                "title": user_text[:50],
                "remind_at": None,
                "category": "general",
                "priority": "medium",
                "reply_text": fallback_reply,
            }

    async def answer_second_brain_query(self, user_query: str, tasks: list, notes: list, lang: str = "fa") -> str:
        """
        Synthesizes an intelligent answer for user queries using their saved tasks and notes.
        """
        context_lines = []
        
        if tasks:
            context_lines.append("Tasks / Plans:")
            for t in tasks:
                context_lines.append(f"- {t.title} (due: {t.remind_at}, status: {t.status})")
        
        if notes:
            context_lines.append("\nNotes / Memory:")
            for n in notes:
                context_lines.append(f"- {n.content} (date: {n.created_at})")

        context_text = "\n".join(context_lines) if context_lines else "No data stored yet."
        lang_text = "Respond in Persian (فارسی)." if lang == "fa" else "Respond in English."

        prompt = f"""
You are NudgeMate. The user is asking about their tasks, schedule, or stored memories.
{lang_text}
Use the information below to give a concise, warm, and accurate response:

Stored Information:
{context_text}

User Question: {user_query}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are NudgeMate personal AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content or ("پاسخی پیدا نشد." if lang == "fa" else "No answer found.")
        except Exception as e:
            logger.error(f"Error querying second brain: {e}")
            return "متاسفانه نتونستم حافظه رو جستجو کنم." if lang == "fa" else "Could not search memory right now."



ai_service = AIService()
