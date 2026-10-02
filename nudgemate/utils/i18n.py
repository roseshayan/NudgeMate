"""
Internationalization (i18n) module for NudgeMate.
Supports Persian (fa) and English (en).
"""

MESSAGES = {
    "welcome": {
        "fa": (
            "سلام {name} عزیز! 👋\n"
            "من **NudgeMate** هستم؛ دستیار هوشمند، حواس‌جمع و سمج تو برای یادآوری کارها و یادداشت‌ها. 🤖\n\n"
            "**چطور با من کار کنی؟ خیلی راحته!**\n"
            "🎙 فقط کافیه یه **ویس** برام بفرستی، یا تایپ کنی:\n"
            "• «فردا ساعت ۴ عصر با دکتر قرار دارم»\n"
            "• «نیم ساعت دیگه زیر گازو خاموش کن»\n"
            "• «یادم باشه شماره پرونده بیمه فلان است»\n\n"
            "من خودکار تاریخ و ساعت رو می‌فهمم، سر وقت بهت خبر می‌دم، و اگه حواست نبود اون‌قدر پیگیری می‌کنم تا خیالم راحت بشه انجامش دادی! 😎\n\n"
            "دستورات مفید:\n"
            "📋 /tasks - کارهای فعال\n"
            "📝 /notes - یادداشت‌ها (مغز دوم)\n"
            "☀️ /briefing - گزارش روزانه\n"
            "🌐 /lang - تغییر زبان (Language)\n"
            "📊 /stats - آمار عملکرد شما\n"
            "ℹ️ /help - راهنمای کامل"
        ),
        "en": (
            "Hello {name}! 👋\n"
            "I'm **NudgeMate**, your smart, persistent AI task reminder & second brain assistant. 🤖\n\n"
            "**How to use me? Super easy!**\n"
            "🎙 Just send me a **voice message** or type:\n"
            "• \"Dentist appointment tomorrow at 4 PM\"\n"
            "• \"Turn off the oven in 30 minutes\"\n"
            "• \"Remember safe box code is 98765\"\n\n"
            "I understand natural time expressions, remind you on time, and follow up persistently if you forget to check in! 😎\n\n"
            "Useful Commands:\n"
            "📋 /tasks - Active tasks\n"
            "📝 /notes - Saved notes (Second Brain)\n"
            "☀️ /briefing - Today's briefing\n"
            "🌐 /lang - Change language\n"
            "📊 /stats - Your productivity stats\n"
            "ℹ️ /help - Comprehensive guide"
        ),
    },
    "help": {
        "fa": (
            "📖 **راهنمای استفاده از NudgeMate (نسخه {version})**\n\n"
            "۱. **ارسال صوتی (Voice):**\n"
            "در حال رانندگی یا پیاده‌روی هستی؟ ویس بفرست تا با هوش مصنوعی تبدیل به متن و تسک بشه.\n\n"
            "۲. **سیستم پیگیری سمج (Nagging):**\n"
            "وقتی زمان کارت برسه، دکمه‌های [انجام شد] یا [به تعویق انداختن] برات میاد. اگه جواب ندی، ربات پیگیری می‌کنه تا یادت نره!\n\n"
            "۳. **مغز دوم (Second Brain):**\n"
            "هر نکته‌ای خواستی یادت بمونه بگو «یادم باشه...». بعداً می‌تونی بپرسی «فلان چیز کجاست؟» تا جوابت رو بدم.\n\n"
            "🌐 تغییر زبان: با دستور /lang می‌تونی زبان ربات رو بین فارسی و انگلیسی تغییر بدی."
        ),
        "en": (
            "📖 **NudgeMate User Guide (v{version})**\n\n"
            "1. **Voice Input:**\n"
            "Walking or driving? Just speak a voice note. AI will transcribe and schedule it automatically.\n\n"
            "2. **Nagging Reminder Loop:**\n"
            "When a reminder triggers, you get buttons to complete or snooze it. If ignored, the bot persistently re-reminds you!\n\n"
            "3. **Second Brain:**\n"
            "Say \"Remember my keys are on the kitchen desk\". Later, ask \"Where are my keys?\" and the bot will recall it.\n\n"
            "🌐 Language: Type /lang to switch between English and Persian."
        ),
    },
    "no_pending_tasks": {
        "fa": "🎉 هیچ کار معوقه‌ای نداری رفیق! همه چی عالی و مرتبه.",
        "en": "🎉 You have no pending tasks! You are all caught up.",
    },
    "no_notes": {
        "fa": "📝 هنوز هیچ یادداشتی توی حافظه‌ام ثبت نکردی.",
        "en": "📝 You haven't stored any notes yet.",
    },
    "task_created": {
        "fa": "✅ **یادآوری با موفقیت تنظیم شد!**",
        "en": "✅ **Reminder scheduled successfully!**",
    },
    "note_saved": {
        "fa": "🧠 **به حافظه سپرده شد! (مغز دوم)**",
        "en": "🧠 **Saved to Second Brain!**",
    },
    "general_task_saved": {
        "fa": "📝 **کار شما در لیست عمومی ثبت شد:**",
        "en": "📝 **Task added to your general list:**",
    },
    "time_due": {
        "fa": "⏰ **وقتشه رفیق!**",
        "en": "⏰ **Time's up!**",
    },
    "nag_title": {
        "fa": "⚠️ **یادآوری مجدد ({count})!**",
        "en": "⚠️ **Follow-up Reminder ({count})!**",
    },
    "btn_done": {
        "fa": "✅ انجام شد",
        "en": "✅ Done",
    },
    "btn_cancel": {
        "fa": "❌ لغو",
        "en": "❌ Cancel",
    },
    "btn_snooze_10": {
        "fa": "⏳ ۱۰ دقیقه بعد",
        "en": "⏳ In 10 mins",
    },
    "btn_snooze_30": {
        "fa": "⏳ ۳۰ دقیقه بعد",
        "en": "⏳ In 30 mins",
    },
    "btn_snooze_60": {
        "fa": "⏳ ۱ ساعت بعد",
        "en": "⏳ In 1 hour",
    },
    "btn_snooze_day": {
        "fa": "🔁 فردا همین موقع",
        "en": "🔁 Tomorrow",
    },
    "btn_delete": {
        "fa": "🗑 حذف",
        "en": "🗑 Delete",
    },
    "lang_changed": {
        "fa": "🇮🇷 زبان ربات با موفقیت روی **فارسی** تنظیم شد.",
        "en": "🇬🇧 Bot language successfully switched to **English**.",
    },
}


def t(key: str, lang: str = "fa", **kwargs) -> str:
    """Translates a message key to specified language with formatting."""
    lang_dict = MESSAGES.get(key, {})
    text = lang_dict.get(lang, lang_dict.get("en", key))
    if kwargs:
        return text.format(**kwargs)
    return text
